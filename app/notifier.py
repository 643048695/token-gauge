# -*- coding: utf-8 -*-
"""通知层：托盘气泡 / 系统通知（winotify）/ 关闭，事件去重。

契约（INTERFACES.md §3）：
- set_tray_icon(icon)                 注入 pystray icon（由 D 在 main.py 注入）
- notify(method, title, body)         method: "tray" / "system" / "off"
- check(provider_id, result, prev_result, settings)  事件判断（内部去重，状态存内存）

事件：月度 used_pct ≥ threshold（默认 80）/ ≥ urgent（默认 95）、
cookie_valid=False、连续失败 ≥ 3 次。
去重：每个 (provider_id, 事件类型) 触发一次，状态回落/恢复后重置，
    之后条件再满足可以再次触发。
"""

from __future__ import annotations

import threading
import logging

log = logging.getLogger(__name__)

# 事件类型常量（与 config.json 中 notify.events 的键一一对应）
EV_THRESHOLD = "threshold"      # 月度用量预警
EV_URGENT = "urgent"            # 月度用量紧急
EV_COOKIE_FAIL = "cookie_fail"  # 凭据失效
EV_FETCH_FAIL = "fetch_fail"    # 连续抓取失败


class Notifier:
    """通知判断与投递。事件去重状态全部保存在内存。"""

    def __init__(self) -> None:
        self._icon = None                      # pystray icon（D 注入）
        self._fired: set[tuple[str, str]] = set()   # {(provider_id, event)}
        self._fail_streak: dict[str, int] = {}      # provider_id -> 连续失败次数
        self._lock = threading.Lock()

    # ------------------------------------------------------------ 注入

    def set_tray_icon(self, icon) -> None:
        """注入托盘 icon 实例，供气泡通知使用。"""
        self._icon = icon

    # ------------------------------------------------------------ 投递

    def notify(self, method: str, title: str, body: str) -> None:
        """按 method 投递通知；异常一律降级，不让通知影响主流程。"""
        if method == "off":
            return  # 静默
        if method == "system":
            try:
                from winotify import Notification  # 可选依赖
                toast = Notification(app_id="TokenGauge",
                                     title=title, msg=body)
                toast.show()
                return
            except Exception:
                method = "tray"  # 系统通知不可用，降级托盘
        # method == "tray"（含降级）
        if self._icon is not None:
            try:
                self._icon.notify(body, title)
                return
            except Exception as _e: log.debug(f"notifier.py 异常: {_e}")
        # 无 icon / 托盘失败 → 打印兜底（pythonw 无控制台时 print 会抛异常，需防御）
        try:
            print(f"[notify] {title}｜{body}")
        except Exception as _e: log.debug(f"notifier.py 异常: {_e}")

    # ------------------------------------------------------------ 事件判断

    def check(self, provider_id: str, result: dict,
              prev_result: dict | None = None, settings: dict | None = None) -> None:
        """对一次抓取结果做事件判断。

        参数：
          provider_id : provider 标识
          result      : 本次抓取结果（标准化结构）
          prev_result : 上一次展示结果（契约签名保留，内部不强制依赖）
          settings    : 全量配置（读 notify 段：method / threshold / urgent / events）
        """
        settings = settings or {}
        notify_cfg = settings.get("notify", {}) or {}
        events = notify_cfg.get("events", {}) or {}
        method = notify_cfg.get("method", "tray")
        threshold = float(notify_cfg.get("threshold", 80))
        urgent = float(notify_cfg.get("urgent", 95))

        ok = bool(result.get("ok"))
        used_pct = self._monthly_used_pct(result)

        with self._lock:
            # ---- 连续失败（fetch_fail）----
            if not ok:
                streak = self._fail_streak.get(provider_id, 0) + 1
                self._fail_streak[provider_id] = streak
                if streak >= 3 and events.get(EV_FETCH_FAIL, True):
                    self._fire(provider_id, EV_FETCH_FAIL, method,
                               "TokenGauge：连续抓取失败",
                               f"已连续 {streak} 次抓取失败，请检查网络或凭据")
            else:
                # 恢复成功：重置失败计数与去重状态
                self._fail_streak.pop(provider_id, None)
                self._fired.discard((provider_id, EV_FETCH_FAIL))

            # ---- Cookie 失效（cookie_fail）----
            if result.get("cookie_valid") is False:
                if events.get(EV_COOKIE_FAIL, True):
                    self._fire(provider_id, EV_COOKIE_FAIL, method,
                               "TokenGauge：凭据失效",
                               "登录凭据已失效，请打开主面板更新")
            else:
                self._fired.discard((provider_id, EV_COOKIE_FAIL))

            # ---- 月度用量阈值 / 紧急（仅在本次抓取成功时判断）----
            if ok and used_pct is not None:
                if used_pct >= urgent and events.get(EV_URGENT, True):
                    self._fire(provider_id, EV_URGENT, method,
                               "TokenGauge：额度紧急",
                               self._pct_message(used_pct, result))
                elif used_pct >= threshold and events.get(EV_THRESHOLD, True):
                    self._fire(provider_id, EV_THRESHOLD, method,
                               "TokenGauge：额度预警",
                               self._pct_message(used_pct, result))
            # 用量回落 → 解除对应事件的去重标记，允许再次触发
            if used_pct is not None and used_pct < threshold:
                self._fired.discard((provider_id, EV_THRESHOLD))
            if used_pct is not None and used_pct < urgent:
                self._fired.discard((provider_id, EV_URGENT))

    # ------------------------------------------------------------ 内部

    def _fire(self, provider_id: str, event: str, method: str,
              title: str, body: str) -> None:
        """去重触发：同 (provider_id, event) 已触发过则跳过；否则投递并记录。"""
        key = (provider_id, event)
        if key in self._fired:
            return
        self._fired.add(key)
        self.notify(method, title, body)

    @staticmethod
    def _monthly_used_pct(result: dict) -> float | None:
        """从 limits 中取 monthly 的 used_pct；取不到返回 None。"""
        for lim in result.get("limits") or []:
            if lim.get("id") == "monthly" and lim.get("used_pct") is not None:
                return float(lim["used_pct"])
        return None

    @staticmethod
    def _pct_message(used_pct: float, result: dict) -> str:
        """生成中文用量文案，如「本月额度已用 80%，剩余约 $12」。"""
        meta = result.get("meta") or {}
        limit_usd = meta.get("monthly_limit_usd")
        used_usd = meta.get("used_usd")
        if limit_usd is not None and used_usd is not None:
            left = float(limit_usd) - float(used_usd)
            if left < 0:
                left = 0.0
            return f"本月额度已用 {used_pct:.0f}%，剩余约 ${left:.0f}"
        return f"本月额度已用 {used_pct:.0f}%"
