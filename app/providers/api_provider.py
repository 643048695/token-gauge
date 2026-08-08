# -*- coding: utf-8 -*-
"""通用 API 导入 Provider（app/providers/api_provider.py）。

实现 INTERFACES.md §2 的 Provider 抽象：用"查询模板 + 字段映射"对接任意
带额度查询接口的 AI API 服务（DeepSeek / Kimi / 硅基流动 / StepFun /
OpenRouter / one-api 中转站 / z.ai / Groq 等）。

config 结构（config.json providers.<实例id>.config）：
    {
        "template": "deepseek",      # 模板 id，或 "detect" 启用探测模式
        "api_key": "sk-...",         # 必填
        "base_url": "https://...",   # 模板 url 含 {base} 或探测模式时必填
        "user_id": "12345"           # 可选（one-api 新版用）
    }

行为要点：
- 模板映射提取 remaining（必填）；used / limit / currency / plan_name 可选
- used+limit 都有 → 构造 limits 进度条项；limit 缺失 → 用 remaining+used 求和
- 余额型（balance）无窗口概念 → 不落快照（store），meta 携带原始提取值
- verify 复用 fetch，失败时附带响应预览（前 200 字符）便于实测校准模板
- 探测模式（template="detect"）：按 PROBE_PATHS 候选路径依次尝试，
  200 + JSON + 余额字段白名单三条件同时满足才算命中，并自动猜测映射
"""

import re
import time

import requests

from .base import Provider
from . import api_templates as tpl
from .. import store

REQUEST_TIMEOUT = 15      # 模板模式请求超时（秒）
PROBE_TIMEOUT = 5         # 探测模式单路径超时（秒）
PREVIEW_LEN = 200         # 响应预览长度


def _to_number(v):
    """把 int/float/数字字符串转 float；无法转换返回 None（bool 除外）。"""
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v.strip())
        except (TypeError, ValueError):
            return None
    return None


def _resolve_path(data, path: str):
    """点路径解析：data.xxx[0].yyy → 值；找不到返回 None。

    支持数字索引写法（balance_infos[0].total_balance）。
    """
    cur = data
    for part in path.split("."):
        m = re.match(r"^([A-Za-z_]\w*)\[(\d+)\]$", part)
        if m and isinstance(cur, dict):
            arr = cur.get(m.group(1))
            idx = int(m.group(2))
            if isinstance(arr, list) and idx < len(arr):
                cur = arr[idx]
                continue
            return None
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
            continue
        return None
    return cur


def _preview(data) -> str:
    """响应预览（调试/校准用），截断避免刷屏。"""
    if isinstance(data, str):
        text = data.strip()
    else:
        try:
            import json as _json
            text = _json.dumps(data, ensure_ascii=False)
        except Exception:
            text = str(data)
    return text[:PREVIEW_LEN] + ("…" if len(text) > PREVIEW_LEN else "")


def _to_reset_in_sec(v, now: int):
    """把重置时间（ISO 字符串 / 秒 / 毫秒时间戳）转成距 now 的秒数；无法解析返回 None。"""
    if v is None:
        return None
    import datetime as _dt
    ts = None
    if isinstance(v, str):
        s = v.strip()
        try:
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            ts = _dt.datetime.fromisoformat(s).timestamp()
        except ValueError:
            return None
    elif isinstance(v, (int, float)):
        ms = v * 1000 if v < 1_000_000_000_000 else v
        ts = ms / 1000
    if ts is None:
        return None
    return max(0, int(ts - now))


class ApiProvider(Provider):
    id = "api"
    name = "API 导入"
    plan_name = ""
    template_id = None  # 子类固定模板；为 None 时从 config["template"] 取
    schema = [
        {"key": "template", "label": "查询模板",
         "type": "select", "secret": False,
         "options": [
             {"value": tid, "label": t.get("name", tid),
              "needs": tpl.template_field_needs(tid)}
             for tid, t in tpl.TEMPLATES.items()
         ] + [{"value": "detect", "label": "探测模式（自动找余额接口）",
               "needs": ["base_url"]}]},
        {"key": "api_key", "label": "API Key", "type": "text", "secret": True},
        {"key": "base_url", "label": "Base URL", "type": "text", "secret": False,
         "when": "base_url", "placeholder": "https://api.example.com"},
        {"key": "user_id", "label": "User ID（one-api 中转站可选）",
         "type": "text", "secret": False,
         "when": "user_id", "placeholder": "123456"},
    ]

    # ------------------------------------------------------------ 对外接口

    def fetch(self) -> dict:
        """抓取一次，返回标准化结果（INTERFACES.md §2）；成功自动落快照。"""
        return self._run(record=True)

    def verify(self) -> dict:
        """测试连接：复用 _run 判断（不落快照），失败时带响应预览方便校准模板。"""
        result = self._run(record=False)
        if result.get("meta", {}).get("demo"):
            return {"ok": True, "message": "演示模式（模拟数据）", "detail": result}
        if result.get("ok"):
            bal = result.get("balance", {})
            meta = result.get("meta", {})
            msg = f"连接成功：剩余 {bal.get('amount', 0)} {bal.get('currency', '')}"
            if meta.get("used") is not None:
                msg += f"，已用 {meta['used']}"
            return {"ok": True, "message": msg.strip(), "detail": result}
        return {"ok": False, "message": result.get("error", "连接失败"),
                "detail": result}

    # ------------------------------------------------------------ 主流程

    def _run(self, record: bool = True) -> dict:
        cfg = self.config or {}
        template = ((cfg.get("template") or "").strip() or self.template_id or "").strip()
        api_key = (cfg.get("api_key") or "").strip()
        base_url = (cfg.get("base_url") or "").strip().rstrip("/")

        # 演示模式：无需 API Key，返回内置模拟数据（前端带"演示数据"标签）
        if str(cfg.get("demo", "")).lower() in ("true", "1", "yes", "on"):
            return self._demo_result(template)

        if not api_key:
            return self._fail("缺少配置：api_key 未设置")

        if template == "detect":
            return self._detect(base_url, api_key)

        tmpl = tpl.TEMPLATES.get(template)
        if tmpl is None:
            return self._fail(f"未知模板：{template}")

        # ---- 构建请求 ----
        url = tmpl.get("url") or ""
        if "{base}" in url:
            base = base_url or (tmpl.get("default_base") or "").rstrip("/")
            if not base:
                return self._fail("模板需要 Base URL，未填写")
            url = url.replace("{base}", base)
        if not url:
            return self._fail(f"模板 {tmpl.get('name', template)} 未配置完整（端点待校准）")

        headers = {
            "Accept": "application/json",
        }
        auth = tmpl.get("auth", "bearer")
        if auth == "raw":
            # 智谱系：Authorization 直接放 key，不加 Bearer 前缀
            headers["Authorization"] = api_key
        else:
            headers["Authorization"] = f"Bearer {api_key}"
        for k, v in (tmpl.get("headers") or {}).items():
            headers[k] = v.replace("{api_key}", api_key).replace("{user_id}",
                                                                 cfg.get("user_id") or "")

        try:
            resp = requests.request(tmpl.get("method", "GET"), url,
                                    headers=headers, timeout=REQUEST_TIMEOUT)
        except requests.RequestException as e:
            return self._fail(f"网络错误: {e}")

        if resp.status_code == 401 or resp.status_code == 403:
            return self._fail(f"凭据无效（HTTP {resp.status_code}）")
        if resp.status_code != 200:
            return self._fail(f"HTTP {resp.status_code}: {_preview(resp.text)}")

        try:
            data = resp.json()
        except ValueError:
            return self._fail(f"响应不是 JSON：{_preview(resp.text)}")

        # ---- 订阅型（多窗口）分支 ----
        if tmpl.get("windows"):
            return self._run_windows(tmpl, data, template)

        # ---- 余额型 / 中转站型：字段提取 ----
        # 数值字段（remaining/used/limit）过 _to_number + 系数；
        # 字符串字段（currency/plan_name）保持原始字符串。
        NUMERIC_KEYS = ("remaining", "used", "limit")
        extracted = {}
        for key in NUMERIC_KEYS + ("currency", "plan_name"):
            path = (tmpl.get("mapping") or {}).get(key)
            if not path:
                continue
            scale = 1.0
            if "*" in path:
                path, _, scale_s = path.partition("*")
                try:
                    scale = float(scale_s)
                except ValueError:
                    scale = 1.0
            raw = _resolve_path(data, path)
            if key in NUMERIC_KEYS:
                val = _to_number(raw)
                if val is not None:
                    extracted[key] = val * scale
            else:
                if raw is not None and not isinstance(raw, (dict, list)):
                    extracted[key] = str(raw)

        remaining = extracted.get("remaining")
        if remaining is None:
            # 无限额度（如 OpenRouter 套餐 limit_remaining/limit 为 null）：按 0 显示
            if tmpl.get("infinite"):
                remaining = 0.0
            else:
                return self._fail(
                    f"未从响应提取到 remaining（模板 {tmpl.get('name', template)} "
                    f"可能待校准或接口结构变化）。响应：{_preview(data)}")

        used = extracted.get("used")
        limit = extracted.get("limit")
        if limit is None and used is not None:
            limit = remaining + used  # 总量缺失时按 剩余+已用 求和

        currency = extracted.get("currency") or (tmpl.get("static") or {}).get("currency", "")
        plan_name = extracted.get("plan_name") or (tmpl.get("static") or {}).get("plan_name", "") \
            or tmpl.get("name", template)

        # ---- 组装标准化结果 ----
        now = int(time.time())
        limits = []
        if used is not None and limit and limit > 0:
            limits.append({
                "id": "quota",
                "label": "总量",
                "used_pct": round(min(100.0, used / limit * 100), 1),
                "reset_in_sec": None,
            })

        result = {
            "ok": True,
            "fetched_at": now,
            "cookie_valid": True,
            "plan_name": plan_name,
            "limits": limits,
            "balance": {"currency": currency, "amount": round(remaining, 4)},
            "site": tmpl.get("site") or "",
            "peak": bool(tmpl.get("peak")),
            "meta": {
                "template": template,
                "kind": tmpl.get("kind", "balance"),
                "unit": tmpl.get("unit", "amount"),
            },
        }
        # 附加字段：有才放，保持结构干净
        for k, v in (("used", used), ("limit", limit), ("currency", currency)):
            if v is not None:
                result["meta"][k] = v
        if tmpl.get("note"):
            result["meta"]["note"] = tmpl["note"]
        # 单价表（balance 型可带 static.models）
        _models = (tmpl.get("static") or {}).get("models")
        if _models:
            result["meta"]["models"] = _models
        # 可选字段（余额状态/赠金/充值拆分等）：mapping 有路径就原样进 meta
        for _ok in ("available", "granted", "topped_up"):
            _p = (tmpl.get("mapping") or {}).get(_ok)
            if not _p:
                continue
            _rv = _resolve_path(data, _p)
            if _rv is not None and not isinstance(_rv, (dict, list)):
                result["meta"][_ok] = _rv
        # 余额型/中转站型：落快照 + 消耗速度推算
        self._finalize(result, record)
        # provider 字段不在此填，由 kernel 按实例 id 补齐
        return result

    # ------------------------------------------------------------ 余额消耗推算

    def _snap_id(self) -> str:
        """快照文件标识：优先用实例 pid（kernel 注入，多实例隔离），
        未注入时退回模板/类 id（单实例兼容，行为与旧版一致）。"""
        return getattr(self, "pid", None) or self.id

    def _finalize(self, result: dict, record: bool) -> None:
        """成功后：落快照（余额型/中转站型），并给 meta 附消耗速度/还能撑。"""
        bal = result.get("balance") or {}
        amount = bal.get("amount")
        if not isinstance(amount, (int, float)):
            return
        if record:
            store.append(self._snap_id(), result)
        try:
            result["meta"]["speed"] = self._speed_meta(float(amount), int(time.time()))
        except Exception as _e: log.debug(f"api_provider.py 异常: {_e}")

    def _speed_meta(self, balance: float, now: int) -> dict:
        """余额消耗速度：按日取当日最小余额，相邻日差值（消耗为正）取日均，
        再算还能撑天数。充值跳升自动跳过；样本不足返回 data_ready:false。"""
        snaps = store.snapshots(self._snap_id(), hours=720)
        day_min = {}
        for s in snaps:
            b = s.get("balance")
            if b is None:
                continue
            day = time.strftime("%Y-%m-%d", time.localtime(s["ts"]))
            if day not in day_min or b < day_min[day]:
                day_min[day] = b
        if not day_min:
            return {"data_ready": False, "sample_days": 0}
        today = time.strftime("%Y-%m-%d", time.localtime(now))
        day_min[today] = min(day_min.get(today, balance), balance)
        days = sorted(day_min.items())
        deltas = []
        for i in range(1, len(days)):
            d = days[i - 1][1] - days[i][1]  # 余额下降 → 消耗为正
            if d > 0:
                deltas.append(d)
        if len(deltas) < 2:  # 至少 3 天跨度才有意义
            return {"data_ready": False, "sample_days": len(deltas),
                    "today_amount": self._today_amount(day_min, days, now),
                    "week": self._week_series(day_min, days, now),
                    "total_consumed": self._total_consumed(day_min, days),
                    "since_ts": self._since_ts(day_min, days)}
        recent = deltas[-3:]
        daily = sum(recent) / len(recent)
        days_left = balance / daily if daily > 0 else None
        return {
            "data_ready": True,
            "daily_amount": round(daily, 4),
            "daily_text": self._fmt_amount(daily),
            "days_left": round(days_left, 1) if days_left else None,
            "days_left_text": self._fmt_days(days_left * 24) if days_left else "—",
            "sample_days": len(recent),
            "today_amount": self._today_amount(day_min, days, now),
            "week": self._week_series(day_min, days, now),
            "total_consumed": self._total_consumed(day_min, days),
            "since_ts": self._since_ts(day_min, days),
        }

    @staticmethod
    def _total_consumed(day_min: dict, days: list) -> float:
        """统计起点以来累计消耗（金额）：所有相邻日正差值求和（充值跳升自动跳过）。"""
        total = 0.0
        for i in range(1, len(days)):
            d = days[i - 1][1] - days[i][1]
            if d > 0:
                total += d
        return round(total, 4)

    @staticmethod
    def _since_ts(day_min: dict, days: list) -> int | None:
        """统计起点：快照最早一天（本地 0 点）时间戳；无快照返回 None。"""
        if not days:
            return None
        import datetime as _dt
        try:
            return int(_dt.datetime.strptime(days[0][0], "%Y-%m-%d").timestamp())
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _today_amount(day_min: dict, days: list, now: int) -> float | None:
        """今日消耗：昨天日最小余额 − 今日最小余额（正数）。无昨日数据返回 None。"""
        today = time.strftime("%Y-%m-%d", time.localtime(now))
        cur = day_min.get(today)
        if cur is None or len(days) < 2:
            return None
        prev_day = days[-2]
        prev_min = day_min.get(prev_day)
        if prev_min is None:
            return None
        d = prev_min - cur
        return round(max(0.0, d), 4) if d > 0 else 0.0

    @staticmethod
    def _week_series(day_min: dict, days: list, now: int) -> list:
        """近 7 天每日消耗序列（含今天，元）：前一天日最小 − 当日最小。
        缺前日数据的日期记 0；最多返回 7 项，不足补 0 到 7。"""
        last_days = days[-8:]  # 前 8 天（含前日基准）
        out = []
        for i in range(1, len(last_days)):
            prev_min = day_min.get(last_days[i - 1])
            cur_min = day_min.get(last_days[i])
            if prev_min is None or cur_min is None:
                out.append(0.0)
                continue
            d = prev_min - cur_min
            out.append(round(max(0.0, d), 4))
        while len(out) < 7:
            out.insert(0, 0.0)
        return out[-7:]

    @staticmethod
    def _fmt_amount(v: float) -> str:
        if v < 0.01:
            return f"{v:.4f}"
        if v < 100:
            return f"{v:.2f}"
        return f"{v:,.0f}"

    @staticmethod
    def _fmt_days(hours: float) -> str:
        if hours < 72:
            return f"{max(1, int(round(hours)))} 小时"
        d = hours / 24
        if d < 30:
            return f"{d:.1f} 天"
        return f"{d / 30:.1f} 个月"

    # ------------------------------------------------------------ 订阅型多窗口

    def _run_windows(self, tmpl: dict, data: dict, template: str) -> dict:
        """订阅型（quota）多窗口提取：按 windows 定义构造 limits 数组。

        每个窗口支持：
          pct        直接给已用百分比的路径（可带 *系数）
          used_of    用 limit/remaining 两条路径算已用百分比
          invert     接口给剩余百分比 → 反转为已用
          reset      重置时间路径（ISO 字符串 / 秒 / 毫秒时间戳）
        """
        now = int(time.time())
        limits = []
        for w in tmpl.get("windows") or []:
            pct = None
            if w.get("pct"):
                path = w["pct"]
                scale = 1.0
                if "*" in path:
                    path, _, scale_s = path.partition("*")
                    try:
                        scale = float(scale_s)
                    except ValueError:
                        scale = 1.0
                pct = _to_number(_resolve_path(data, path))
                if pct is not None:
                    pct *= scale
                    if w.get("scale100"):
                        pct *= 100
            elif w.get("used_of"):
                lim = _to_number(_resolve_path(data, w["used_of"].get("limit", "")))
                rem = _to_number(_resolve_path(data, w["used_of"].get("remaining", "")))
                if lim is not None and lim > 0 and rem is not None:
                    pct = (lim - rem) / lim * 100
            if pct is None:
                continue
            if w.get("invert"):
                pct = 100 - pct
            pct = round(min(100.0, max(0.0, pct)), 1)

            reset_in_sec = None
            if w.get("reset"):
                reset_in_sec = _to_reset_in_sec(_resolve_path(data, w["reset"]), now)

            limits.append({
                "id": w.get("id", "window"),
                "label": w.get("label", "窗口"),
                "used_pct": pct,
                "reset_in_sec": reset_in_sec,
            })

        if not limits:
            return self._fail(
                f"未从响应提取到任何窗口额度（模板 {tmpl.get('name', template)} "
                f"可能待校准或接口结构变化）。响应：{_preview(data)}")
        # 剩余/总量/已用 token：优先取第一个有 remaining/limit 路径的窗口（kimi-coding 等）
        remaining_tokens = None
        limit_tokens = None
        for w in tmpl.get("windows") or []:
            if remaining_tokens is None:
                rem_path = (w.get("used_of") or {}).get("remaining")
                if rem_path:
                    rv = _resolve_path(data, rem_path)
                    if rv is not None:
                        remaining_tokens = rv
            if limit_tokens is None:
                lim_path = (w.get("used_of") or {}).get("limit")
                if lim_path:
                    rv = _resolve_path(data, lim_path)
                    if rv is not None:
                        limit_tokens = rv
            if remaining_tokens is not None and limit_tokens is not None:
                break
        meta = {
            "template": template,
            "kind": tmpl.get("kind", "quota"),
            "unit": tmpl.get("unit", "tokens"),
            "windows": len(limits),
        }
        if remaining_tokens is not None:
            meta["remaining_tokens"] = remaining_tokens
            meta["available_tokens"] = remaining_tokens
            if limit_tokens is not None:
                meta["used_tokens"] = max(0, int(limit_tokens) - int(remaining_tokens))
                meta["total_tokens"] = int(limit_tokens)
        return {
            "ok": True,
            "fetched_at": now,
            "cookie_valid": True,
            "plan_name": tmpl.get("name", template),
            "limits": limits,
            "balance": {"currency": "", "amount": float(limits[0]["used_pct"])},
            "meta": meta,
        }

    # ------------------------------------------------------------ 探测模式

    def _detect(self, base_url: str, api_key: str) -> dict:
        """只给 base_url + api_key：按候选路径探测余额接口并猜测映射。"""
        if not base_url:
            return self._fail("探测模式需要 Base URL")

        for path in tpl.PROBE_PATHS:
            url = f"{base_url}/{path}"
            try:
                resp = requests.get(url, timeout=PROBE_TIMEOUT, headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {api_key}",
                })
            except requests.RequestException:
                continue
            if resp.status_code != 200:
                continue
            try:
                data = resp.json()
            except ValueError:
                continue
            hit = self._guess_mapping(data)
            if hit is not None:
                obj, mapping = hit
                return self._build_probe_result(base_url, path, obj, mapping)

        # 全失败：兜底判定 key 是否有效
        try:
            r = requests.get(f"{base_url}/models", timeout=PROBE_TIMEOUT, headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {api_key}",
            })
            if r.status_code == 200:
                return self._fail("Key 有效但未发现标准余额接口；可改用自定义映射或选具体模板")
            return self._fail(f"Key 无效或端点不对（/models 返回 HTTP {r.status_code}）")
        except requests.RequestException as e:
            return self._fail(f"网络错误: {e}")

    def _guess_mapping(self, data: dict):
        """从响应 JSON 猜测字段映射；无法识别返回 None。

        返回 (obj, mapping)：obj 是映射路径所基于的对象（顶层或嵌套一层），
        mapping 为 {"remaining": 路径, "used": 路径, "limit": 路径}（可为 None）。
        """
        candidates = [data]
        for _k, v in (data.items() if isinstance(data, dict) else []):
            if isinstance(v, dict) and any(
                    f in v for f in tpl.BALANCE_FIELD_KEYS):
                candidates.append(v)
        for obj in candidates:
            keys = set(obj.keys())
            if "used_quota" in keys and "quota" in keys:
                return obj, {"remaining": "quota", "used": "used_quota", "limit": None}
            if "limit_remaining" in keys:
                return obj, {"remaining": "limit_remaining",
                             "used": "usage" if "usage" in keys else None,
                             "limit": "limit" if "limit" in keys else None}
            if "balance" in keys:
                return obj, {"remaining": "balance", "used": None, "limit": None}
            if "total_balance" in keys:
                return obj, {"remaining": "total_balance", "used": None, "limit": None}
            if "available_balance" in keys:
                return obj, {"remaining": "available_balance", "used": None, "limit": None}
            if "remain_quota" in keys:
                return obj, {"remaining": "remain_quota",
                             "used": "used_quota" if "used_quota" in keys else None,
                             "limit": "total_quota" if "total_quota" in keys else None}
            if "remaining" in keys:
                return obj, {"remaining": "remaining", "used": None, "limit": None}
        # 白名单字段散落在顶层但不满足上面组合 → 尝试任意命中字段
        for f in tpl.BALANCE_FIELD_KEYS:
            if f in (data.keys() if isinstance(data, dict) else set()):
                return data, {"remaining": f, "used": None, "limit": None}
        return None

    def _build_probe_result(self, base_url: str, path: str,
                            obj: dict, hit: dict) -> dict:
        """用探测命中的映射组装结果（obj 为映射路径所基于的对象）。"""
        remaining = _to_number(_resolve_path(obj, hit["remaining"]))
        if remaining is None:
            return self._fail(f"探测命中 {path} 但剩余量字段无法解析，"
                              f"响应：{_preview(obj)}")
        used = _to_number(_resolve_path(obj, hit["used"])) if hit.get("used") else None
        limit = _to_number(_resolve_path(obj, hit["limit"])) if hit.get("limit") else None
        if limit is None and used is not None:
            limit = remaining + used

        now = int(time.time())
        limits = []
        if used is not None and limit and limit > 0:
            limits.append({
                "id": "quota", "label": "总量",
                "used_pct": round(min(100.0, used / limit * 100), 1),
                "reset_in_sec": None,
            })
        return {
            "ok": True,
            "fetched_at": now,
            "cookie_valid": True,
            "plan_name": "探测",
            "limits": limits,
            "balance": {"currency": "", "amount": round(remaining, 4)},
            "meta": {
                "template": "detect",
                "kind": "relay",
                "unit": "amount",
                "probe": {"base_url": base_url, "path": path,
                          "mapping": hit},
                "raw_preview": _preview(obj),
            },
        }

    # ------------------------------------------------------------ 工具

    # ------------------------------------------------------------ 演示模式

    def _demo_result(self, template: str) -> dict:
        """无 key 演示：按模板 kind 生成模拟数据，meta.demo=true 供前端标注。"""
        tmpl = tpl.TEMPLATES.get(template, {})
        kind = tmpl.get("kind", "balance")
        currency = (tmpl.get("static") or {}).get("currency", "CNY")
        now = int(time.time())
        base_meta = {
            "template": template, "kind": kind,
            "unit": tmpl.get("unit", "amount"), "demo": True,
        }
        if kind == "balance":
            return {
                "ok": True, "fetched_at": now, "cookie_valid": True,
                "plan_name": tmpl.get("name", template),
                "limits": [],
                "balance": {"currency": currency, "amount": 20.0},
                "site": tmpl.get("site") or "",
                "peak": bool(tmpl.get("peak")),
                "meta": {
                    **base_meta,
                    "available": True, "granted": 5.0, "topped_up": 15.0,
                    "models": (tmpl.get("static") or {}).get("models", []),
                    "speed": {
                        "data_ready": True, "today_amount": 1.2, "daily_amount": 0.8,
                        "days_left": 25.0, "days_left_text": "25.0 天", "sample_days": 3,
                        "week": [0.5, 0.9, 0.4, 1.1, 0.7, 0.3, 1.2],
                    },
                },
            }
        if kind == "relay":
            return {
                "ok": True, "fetched_at": now, "cookie_valid": True,
                "plan_name": tmpl.get("name", template),
                "limits": [{"id": "quota", "label": "总量", "used_pct": 30, "reset_in_sec": None}],
                "balance": {"currency": currency, "amount": 5.5},
                "site": tmpl.get("site") or "",
                "peak": False,
                "meta": {
                    **base_meta, "used": 2.3, "limit": 7.8,
                    "speed": {
                        "data_ready": True, "daily_amount": 0.15, "daily_text": "0.15",
                        "days_left": 36.0, "days_left_text": "36 天", "sample_days": 3,
                        "today_amount": 0.2, "week": [0.1, 0.2, 0.15, 0.1, 0.3, 0.15, 0.2],
                    },
                },
            }
        # quota（订阅型）
        return {
            "ok": True, "fetched_at": now, "cookie_valid": True,
            "plan_name": tmpl.get("name", template),
            "limits": [
                {"id": "five_hour", "label": "5h", "used_pct": 42, "reset_in_sec": 3600},
                {"id": "weekly", "label": "周", "used_pct": 55, "reset_in_sec": 86400},
            ],
            "balance": {"currency": "", "amount": 42.0},
            "site": tmpl.get("site") or "",
            "peak": False,
            "meta": {**base_meta, "windows": 2, "remaining_tokens": 260000000},
        }

    def _fail(self, error: str) -> dict:
        """失败结果：结构完整（契约要求 ok:false 仍带全字段）。"""
        return {
            "ok": False,
            "fetched_at": int(time.time()),
            "cookie_valid": False,
            "plan_name": "",
            "limits": [],
            "balance": {"currency": "", "amount": 0.0},
            "meta": {},
            "error": error,
        }


# ================================================================
# 模板即类型：每个模板注册成一个独立 Provider 子类，
# 用户在「添加供应商」里直接看到供应商清单（DeepSeek / Kimi …），
# 选中后只需填 API Key（中转站模板才补 Base URL 等）。
# ================================================================


def _build_template_schema(tid: str) -> list:
    """按模板 needs 生成类型 schema：无模板下拉，只列实际要填的字段。"""
    needs = tpl.template_field_needs(tid)
    t = tpl.TEMPLATES.get(tid, {})
    guide = t.get("guide", "")  # 模板级凭据引导 id（api-key 等），挂到 api_key 字段
    schema = [
        {"key": "api_key", "label": "API Key", "type": "text", "secret": True,
         "help": guide or None},
        {"key": "demo", "label": "演示模式（无需 API Key）", "type": "select", "secret": False,
         "options": [{"value": "", "label": "否（填真实 Key）"},
                     {"value": "true", "label": "是（内置模拟数据）"}]},
        {"key": "est_price_per_mtok", "label": "估算单价（币种/百万token，token 估算用）",
         "type": "text", "secret": False, "placeholder": "3"},
    ]
    if "base_url" in needs:
        schema.append({"key": "base_url", "label": "Base URL", "type": "text",
                       "secret": False, "placeholder": "https://api.example.com"})
    if "user_id" in needs:
        schema.append({"key": "user_id", "label": "User ID（one-api 中转站可选）",
                       "type": "text", "secret": False, "placeholder": "123456"})
    return schema


def _make_template_provider(tid: str):
    """为模板动态生成 Provider 子类：id=模板 id，template_id 固定，schema 按需。"""
    t = tpl.TEMPLATES.get(tid, {})
    tname = t.get("name", tid)
    tguide = t.get("guide", "")
    tsite = t.get("site", "")

    class _TemplateProvider(ApiProvider):
        id = tid
        name = tname
        plan_name = tname
        template_id = tid
        cred_guide = tguide  # 凭据引导 id（api-key 等），前端 ❓ 弹获取指引
        site = tsite        # 官网（卡片 🌐 按钮）
        schema = _build_template_schema(tid)

    _TemplateProvider.__name__ = f"TemplateProvider_{tid}"
    return _TemplateProvider


class DetectProvider(ApiProvider):
    """探测模式：只给 base_url + api_key，自动找余额接口。"""
    id = "detect"
    name = "探测模式（自动找余额接口）"
    plan_name = "探测"
    template_id = "detect"
    schema = [
        {"key": "api_key", "label": "API Key", "type": "text", "secret": True},
        {"key": "base_url", "label": "Base URL", "type": "text", "secret": False,
         "placeholder": "https://api.example.com"},
    ]


# 模板类型注册表（id → 子类），顺序即添加面板清单顺序
TEMPLATE_PROVIDERS: dict = {
    tid: _make_template_provider(tid) for tid in tpl.TEMPLATE_ORDER
}
