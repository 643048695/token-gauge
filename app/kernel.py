# -*- coding: utf-8 -*-
"""调度内核：多供应商并行抓取、缓存、通知判断。

契约（INTERFACES.md §3）：
- __init__(self, config, providers=None)   providers 为 None 时按 config 实例化
- start() / stop()                         调度线程 + ThreadPoolExecutor 并行抓取
- get_view()                               全视图（ok/fetched_at/providers/settings/theme_css）
- refresh_now(provider_id=None)            后台线程触发抓取
- test_provider(provider_id)               同步 verify
- get_settings() / save_settings(patch)    透传 settings.py

缓存策略：
- 成功结果进缓存；
- 失败时保留上次成功结果，get_view 时若上次成功超过 2 个 refresh 周期附加 "stale": true；
- 无成功历史时直接返回失败结果本身。
"""

from __future__ import annotations

import importlib
import threading
import logging

log = logging.getLogger(__name__)
import time
from concurrent.futures import ThreadPoolExecutor

from app import settings
from app.notifier import Notifier


class Kernel:
    """调度内核：负责 provider 实例化、周期/手动抓取、缓存与视图组装。"""

    def __init__(self, config: dict, providers: dict | None = None) -> None:
        """providers 参数允许外部注入 provider 实例 dict（便于测试）；
        为 None 时从 config.providers 实例化所有 enabled 的 provider。"""
        self.config = config
        self.notifier = Notifier()

        self._lock = threading.Lock()            # 保护缓存与状态字段
        self._stop_event = threading.Event()     # 调度线程停止信号
        self._scheduler_thread: threading.Thread | None = None
        self._executor: ThreadPoolExecutor | None = None

        # 缓存与状态
        self._cache: dict[str, dict] = {}        # pid -> 展示用结果
        self._last_success: dict[str, dict] = {}  # pid -> 最近成功结果
        self._last_success_at: dict[str, float] = {}  # pid -> 最近成功时间戳
        self._last_attempt_failed: dict[str, bool] = {}  # pid -> 最近一次尝试是否失败
        self._last_error: dict[str, str] = {}    # pid -> 最近错误信息

        # provider 实例与实例化错误
        self._providers: dict[str, object] = {}
        self._provider_errors: dict[str, str] = {}

        if providers is not None:
            # 测试注入：外部实例直接使用
            self._providers = dict(providers)
        else:
            self._build_providers_from_config()

    # ------------------------------------------------------------ 构建 provider

    def _build_providers_from_config(self) -> None:
        """按 config.providers 实例化所有 enabled provider。

        找不到实现类 / 初始化抛异常的 provider 记入 _provider_errors，
        并在缓存里放一个 error 结果，不崩溃。
        """
        pcfg_all = self.config.get("providers", {}) or {}
        for pid, pcfg in pcfg_all.items():
            if not pcfg.get("enabled", True):
                continue
            cls = self._find_provider_class(pid)
            if cls is None and pcfg.get("type"):
                # API 导入型：config.providers.<id>.type 为模板 id（deepseek 等）
                # 或 "api"（自定义），统一从 PROVIDERS 注册表找类
                try:
                    from app.providers import PROVIDERS as _REG
                    cls = _REG.get(str(pcfg["type"]))
                except Exception:
                    cls = None
            if cls is None:
                msg = f"未找到 provider 实现：{pid}"
                self._provider_errors[pid] = msg
                self._cache[pid] = {
                    "provider": pid, "ok": False,
                    "error": msg, "cookie_valid": False,
                    "fetched_at": int(time.time()),
                    "limits": [], "balance": {}, "meta": {},
                }
                continue
            try:
                inst = cls(pcfg.get("config", {}) or {})
                # 注入实例 pid：快照落盘/读取按实例隔离（多实例同模板不串数据）
                try:
                    inst.pid = pid
                except Exception:
                    pass
            except Exception as exc:  # noqa: BLE001
                msg = f"provider 初始化失败：{type(exc).__name__}: {exc}"
                self._provider_errors[pid] = msg
                self._cache[pid] = {
                    "provider": pid, "ok": False,
                    "error": msg, "cookie_valid": False,
                    "fetched_at": int(time.time()),
                    "limits": [], "balance": {}, "meta": {},
                }
                continue
            self._providers[pid] = inst

    @staticmethod
    def _find_provider_class(pid: str):
        """按 provider id 找实现类。

        顺序：1) app.providers 包的 PROVIDERS 注册表（Agent A 可能提供）
             2) 模块名 app.providers.<pid 的 - 换 _>，扫描类属性 id 匹配的实现类
        找不到返回 None。
        """
        # 1) 注册表
        try:
            pkg = importlib.import_module("app.providers")
            registry = getattr(pkg, "PROVIDERS", None)
            if isinstance(registry, dict) and pid in registry:
                return registry[pid]
        except Exception as _e: log.debug(f"kernel.py 异常: {_e}")
        # 2) 模块扫描
        mod_name = "app.providers." + pid.replace("-", "_")
        try:
            mod = importlib.import_module(mod_name)
        except Exception:
            return None
        for name in dir(mod):
            obj = getattr(mod, name)
            if isinstance(obj, type) and getattr(obj, "id", None) == pid:
                return obj
        return None

    def _provider_order(self) -> list[str]:
        """启用的 provider pid 列表。以已实例化的 _providers 为准：
        config 里没有的注入 provider（测试场景）按启用处理；
        config 里有的按 enabled 过滤。"""
        order = []
        for pid in self._providers:
            pcfg = (self.config.get("providers", {}) or {}).get(pid)
            if pcfg is None or pcfg.get("enabled", True):
                order.append(pid)
        return order

    # ------------------------------------------------------------ 生命周期

    def start(self) -> None:
        """启动调度线程：先立即抓一轮，之后每 refresh_interval_sec 抓一轮。"""
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            return
        self._stop_event.clear()
        workers = max(1, min(8, len(self._providers) or 1))
        self._executor = ThreadPoolExecutor(max_workers=workers,
                                            thread_name_prefix="kernel-fetch")
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop, name="kernel-scheduler", daemon=True)
        self._scheduler_thread.start()

    def stop(self) -> None:
        """停止调度线程并关闭线程池。"""
        self._stop_event.set()
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=3)
            self._scheduler_thread = None
        if self._executor:
            try:
                self._executor.shutdown(wait=False, cancel_futures=True)
            except Exception as _e: log.debug(f"kernel.py 异常: {_e}")
            self._executor = None

    def _scheduler_loop(self) -> None:
        """调度主循环：启动即抓一轮，随后按周期等待（Event.wait 可被 stop 立即唤醒）。"""
        self._fetch_all()
        while not self._stop_event.wait(self._interval_sec()):
            self._fetch_all()

    def _interval_sec(self) -> int:
        return int(self.config.get("refresh_interval_sec", 300))

    # ------------------------------------------------------------ 抓取

    def refresh_now(self, provider_id: str | None = None) -> None:
        """后台线程触发一次抓取（provider_id 为空则抓全部）。"""
        threading.Thread(target=self._refresh_background,
                         args=(provider_id,), daemon=True,
                         name="kernel-refresh-now").start()

    def _refresh_background(self, provider_id: str | None) -> None:
        self._fetch_all([provider_id] if provider_id else None)

    def _fetch_all(self, provider_ids: list[str] | None = None) -> None:
        """并行抓取目标 provider（ThreadPoolExecutor），逐个更新缓存并通知判断。"""
        targets = [
            pid for pid in self._provider_order()
            if pid in self._providers
            and (provider_ids is None or pid in provider_ids)
        ]
        if not targets:
            return
        futures = {}
        if self._executor is not None:
            for pid in targets:
                futures[pid] = self._executor.submit(self._fetch_one, pid)
            for pid, fut in futures.items():
                try:
                    fut.result(timeout=120)
                except Exception:
                    pass  # 单个 provider 异常已在 _fetch_one 内兜底
        else:
            # 线程池未启动（stop 后 / 单测直调）时同步执行
            for pid in targets:
                self._fetch_one(pid)

    def _fetch_one(self, pid: str) -> None:
        """抓取单个 provider：更新缓存、记录状态、触发通知判断。异常不冒泡。"""
        prov = self._providers.get(pid)
        if prov is None:
            return
        try:
            result = prov.fetch()
            if not isinstance(result, dict):
                raise TypeError("fetch() 必须返回 dict")
        except Exception as exc:  # noqa: BLE001
            result = {
                "provider": pid, "ok": False,
                "error": f"{type(exc).__name__}: {exc}",
                "cookie_valid": False,
                "fetched_at": int(time.time()),
                "limits": [], "balance": {}, "meta": {},
            }
        # 标准化兜底
        result.setdefault("provider", pid)
        result.setdefault("fetched_at", int(time.time()))

        with self._lock:
            prev = self._cache.get(pid)  # 上一次展示结果（供通知判断）
            if result.get("ok"):
                self._cache[pid] = result
                self._last_success[pid] = result
                self._last_success_at[pid] = float(result["fetched_at"])
                self._last_attempt_failed[pid] = False
                self._last_error.pop(pid, None)
            else:
                # 失败：无成功历史时缓存失败结果本身；有历史则保留上次成功结果
                if pid not in self._last_success:
                    self._cache[pid] = result
                self._last_attempt_failed[pid] = True
                self._last_error[pid] = str(result.get("error", "未知错误"))
        # 通知判断（锁外执行，避免通知阻塞抓取流程）
        self.notifier.check(pid, result, prev, self.config)

    # ------------------------------------------------------------ 视图

    def get_view(self) -> dict:
        """全视图：{ok, fetched_at, refresh_interval_sec, providers, settings, theme_css}。"""
        now = time.time()
        interval = self._interval_sec()
        with self._lock:
            providers_view: dict[str, dict] = {}
            fetched_at: float | None = None
            for pid in self._provider_order():
                r = self._build_provider_view(pid, interval, now)
                if r is not None:
                    providers_view[pid] = r
                    ts = self._last_success_at.get(pid)
                    if ts and (fetched_at is None or ts > fetched_at):
                        fetched_at = ts
            # ok：所有 provider 的最近一次尝试均未失败且结果成功（无结果视为正常空态）。
            # 注意不能用展示结果的 ok 直接 all()——失败时缓存保留的是成功结果（ok=True），
            # 必须结合 _last_attempt_failed 判断真实状态。
            ok = True
            for pid, r in providers_view.items():
                if self._last_attempt_failed.get(pid, False):
                    ok = False
                    break
                if not r.get("ok", False):
                    ok = False
                    break
        theme_css = self._load_theme_css()
        return {
            "ok": ok,
            "fetched_at": int(fetched_at) if fetched_at else None,
            "refresh_interval_sec": interval,
            "providers": providers_view,
            "settings": self.config,
            "theme_css": theme_css,
        }

    def _build_provider_view(self, pid: str, interval: int,
                             now: float) -> dict | None:
        """组装单个 provider 的视图结果（含 stale 标注与占位）。"""
        if pid not in self._cache:
            # 尚未抓取过（例如刚启用），给占位结果，避免前端缺字段
            return {
                "provider": pid, "ok": False,
                "error": "尚未抓取", "cookie_valid": False,
                "fetched_at": None,
                "limits": [], "balance": {}, "meta": {},
            }
        r = self._cache[pid]
        # 最近一次尝试失败且存在成功历史 → 展示成功缓存并标注
        if self._last_attempt_failed.get(pid) and pid in self._last_success:
            out = dict(r)
            last_ok_at = self._last_success_at.get(pid, 0)
            # 超过 2 个 refresh 周期才标记 stale（数据确已过时）
            if now - last_ok_at > 2 * interval:
                out["stale"] = True
            err = self._last_error.get(pid)
            if err:
                out["last_error"] = err
            return out
        return r

    def _load_theme_css(self) -> str:
        """从 app.themes 构建 CSS；themes 模块不可用时返回空串。"""
        try:
            from app.themes import build_css
            theme = self.config.get("theme", {}) or {}
            return build_css(theme.get("id", "paper"),
                             theme.get("variant"))
        except Exception:
            return ""

    # ------------------------------------------------------------ 设置

    def remove_provider(self, provider_id: str) -> dict:
        """从 config 删除供应商（save_settings 会自动重建实例并清缓存）。"""
        provs = dict(self.config.get("providers", {}) or {})
        if provider_id not in provs:
            return {"ok": False, "message": "供应商不存在"}
        del provs[provider_id]
        self.save_settings({"providers": provs})
        return {"ok": True}

    def refresh_provider(self, provider_id: str) -> dict:
        """立即抓取单个供应商（手动刷新）。"""
        if provider_id not in self._providers:
            return {"ok": False, "message": "供应商未启用或不存在"}
        try:
            self._fetch_one(provider_id)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "message": f"{type(exc).__name__}: {exc}"}
        return {"ok": True, "provider": provider_id}

    def test_provider(self, provider_id: str) -> dict:
        """同步调用 provider.verify()，返回 {"ok", "message", "detail"}。"""
        prov = self._providers.get(provider_id)
        if prov is None:
            msg = self._provider_errors.get(provider_id,
                                            "provider 未启用或不存在")
            return {"ok": False, "message": msg}
        try:
            res = prov.verify()
            return {
                "ok": bool(res.get("ok")),
                "message": str(res.get("message", "")),
                "detail": res.get("detail"),
            }
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "message": f"{type(exc).__name__}: {exc}"}

    def get_provider_types(self) -> list:
        """列出可添加的供应商类型（id / 显示名 / 配置字段 schema）。"""
        from app.providers import PROVIDERS
        types = []
        for pid, cls in PROVIDERS.items():
            types.append({
                "id": getattr(cls, "id", pid),
                "name": getattr(cls, "name", pid),
                "plan_name": getattr(cls, "plan_name", ""),
                "schema": list(getattr(cls, "schema", [])),
            })
        return types

    def get_styles(self) -> list:
        """列出可用界面风格（id / 名称 / 描述），供外观页渲染。"""
        from app.themes import list_styles
        return list_styles()

    def get_settings(self) -> dict:
        """当前 config 全量（含默认值合并），透传 settings.load()。"""
        self.config = settings.load()
        return self.config

    def save_settings(self, patch: dict) -> dict:
        """合并且持久化设置；refresh_interval_sec / providers 变化时联动重建。"""
        old_interval = self._interval_sec()
        old_providers = dict(self.config.get("providers", {}) or {})
        new_cfg = settings.save(patch)
        self.config = new_cfg

        restart = False
        if (new_cfg.get("providers", {}) or {}) != old_providers:
            # 供应商配置（增删/启停/凭据）变化 → 重建实例（保留既有缓存）
            self._rebuild_providers()
            restart = True
        if self._interval_sec() != old_interval:
            restart = True
        if restart:
            self._restart_scheduler()
        return {"ok": True, "settings": new_cfg}

    def _rebuild_providers(self) -> None:
        """按新 config 重建 provider 实例与错误记录（缓存不清空）。"""
        with self._lock:
            self._providers = {}
            self._provider_errors = {}
        self._build_providers_from_config()

    def _restart_scheduler(self) -> None:
        """若调度线程正在运行则重启（stop + start），否则仅更新配置。"""
        was_running = (self._scheduler_thread is not None
                       and self._scheduler_thread.is_alive())
        if was_running:
            self.stop()
            self.start()

    # ------------------------------------------------------------ 托盘注入（便捷透传）

    def set_tray_icon(self, icon) -> None:
        """透传给 notifier（D 的 main.py 调用）。"""
        self.notifier.set_tray_icon(icon)
