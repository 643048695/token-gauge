"""OpenCode Go Provider（app/providers/opencode_go.py）。

从旧 v0.1 的 fetcher.py + estimator.py 迁移而来：
- 抓取解析（正则抠 SolidJS 页面内嵌数据）→ 旧 fetcher.py
- 今日用量 + 消耗速度推算 → 旧 estimator.py，速度推算升级为三层：
    L3 trend：最近快照最小二乘线性回归（快照 ≥ 6 条且跨度 ≥ 6h）
    L2 today：今日平均（今日基准存在且 elapsed ≥ 2h）
    L1 short：最近两次快照 Δ%/Δt（间隔 ≥ 30min）
  优先级 L3 > L2 > L1，结果带 source 字段（"trend" / "today" / "short" / ""）。

页面是 SolidJS 渲染，用量数据以 JS 对象字面量形式内嵌在 script 中，结构如：
    rollingUsage:$R[31]={status:"ok",resetInSec:1409,usagePercent:6},
    weeklyUsage:$R[32]={status:"ok",resetInSec:390376,usagePercent:21},
    monthlyUsage:$R[33]={status:"ok",resetInSec:1489940,usagePercent:40}

fetch() 返回 INTERFACES.md §2 标准化结构；成功时自动落快照（app/store.py）并
计算 meta.today / meta.speed / meta.used_usd。
"""
import re
import time

import requests

from .base import Provider
from .. import store

# ---- 抓取常量 ----
BASE_URL = "https://opencode.ai/workspace/{}/go"
MONTHLY_LIMIT_USD = 60.0  # Go 套餐月度限额（美元），也写入 meta.monthly_limit_usd

# Go 模型输出费率（美元/百万 token，2026-08 opencode.ai/docs/go）——token 估算按输出价（保守口径）
OC_MODEL_PRICES = {
    "grok-4.5": 6.00, "gpt-5.6-luna": 1.20, "glm-5.2": 4.40, "glm-5.1": 4.40,
    "kimi-k3": 15.00, "kimi-k2.7-code": 4.00, "kimi-k2.6": 4.00,
    "mimo-v2.5": 0.28, "mimo-v2.5-pro": 0.87,
    "minimax-m3": 1.20, "minimax-m2.7": 1.20, "minimax-m2.5": 1.20,
    "qwen3.8-max": 6.00, "qwen3.7-max": 7.50, "qwen3.7-plus": 1.60, "qwen3.6-plus": 3.00,
    "deepseek-v4-pro": 0.87, "deepseek-v4-flash": 0.28, "hy3": 0.58,
}
OC_MODEL_LABELS = {
    "grok-4.5": "Grok 4.5", "gpt-5.6-luna": "GPT 5.6 Luna", "glm-5.2": "GLM-5.2",
    "glm-5.1": "GLM-5.1", "kimi-k3": "Kimi K3", "kimi-k2.7-code": "Kimi K2.7 Code",
    "kimi-k2.6": "Kimi K2.6", "mimo-v2.5": "MiMo V2.5", "mimo-v2.5-pro": "MiMo V2.5 Pro",
    "minimax-m3": "MiniMax M3", "minimax-m2.7": "MiniMax M2.7", "minimax-m2.5": "MiniMax M2.5",
    "qwen3.8-max": "Qwen3.8 Max", "qwen3.7-max": "Qwen3.7 Max", "qwen3.7-plus": "Qwen3.7 Plus",
    "qwen3.6-plus": "Qwen3.6 Plus", "deepseek-v4-pro": "DeepSeek V4 Pro",
    "deepseek-v4-flash": "DeepSeek V4 Flash", "hy3": "Hy3",
}

# 页面内嵌数据的正则（沿用 v0.1 fetcher.py）
RE_ITEM = re.compile(
    r"(rollingUsage|weeklyUsage|monthlyUsage):[^=]*=\{[^}]*?"
    r"status:\"(ok|error)\",resetInSec:(\d+),usagePercent:(\d+)\}"
)
RE_BALANCE = re.compile(r"balance:([\d.]+),reload:")
RE_USE_BALANCE = re.compile(r"useBalance:(true|false)")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# 三层速度推算的阈值
TREND_MIN_SNAPS = 6        # L3：最少快照条数
TREND_MIN_SPAN_SEC = 6 * 3600  # L3：最小时间跨度 6h
TODAY_MIN_ELAPSED_SEC = 2 * 3600  # L2：今日基准以来至少 2h
SHORT_WINDOW_SEC = 3600           # L1：近 1 小时窗口的消耗速率
SHORT_MIN_WINDOW_SEC = 15 * 60      # L1：窗口至少 15 分钟才有意义
RESET_DROP_PCT = 10        # 月度百分比回跳超过该值视为跨月重置


def _fmt_hours(hours: float) -> str:
    """把小时数格式化成人类可读文本（沿用 v0.1 estimator.py）。"""
    if hours < 0.05:
        return "—"
    if hours < 72:
        h = int(round(hours))
        if h < 1:
            m = max(1, int(round(hours * 60)))
            return f"{m} 分钟"
        return f"{h} 小时"
    d = hours / 24
    if d < 30:
        return f"{d:.1f} 天"
    return f"{d / 30:.1f} 个月"


class OpenCodeGoProvider(Provider):
    id = "opencode-go"
    name = "OpenCode Go"
    plan_name = "Go"
    site = "https://opencode.ai"
    cred_guide = "opencode-cookie"  # F12 开发者工具取 auth Cookie 的引导（i18n GUIDES）
    schema = [
        {"key": "workspace_id", "label": "工作区 ID", "type": "text", "secret": False,
         "help": "opencode-cookie"},
        {"key": "auth_cookie", "label": "认证 Cookie", "type": "text", "secret": True,
         "help": "opencode-cookie"},
        {"key": "est_model", "label": "常用模型（token 估算按该模型费率）",
         "type": "select", "secret": False,
         "options": [{"value": mid, "label": OC_MODEL_LABELS.get(mid, mid)}
                     for mid in OC_MODEL_PRICES]},
    ]

    # ---------------------------------------------------------------- 对外接口

    def fetch(self) -> dict:
        """抓取一次，返回标准化结果；成功时自动落快照并附带 meta。"""
        return self._fetch(record=True)

    def verify(self) -> dict:
        """测试连接：复用 fetch 实现判断，但不落快照（避免测试污染数据）。"""
        result = self._fetch(record=False)
        if result.get("ok"):
            monthly = next((l for l in result.get("limits", []) if l.get("id") == "monthly"), None)
            pct = monthly.get("used_pct", 0) if monthly else 0
            return {"ok": True, "message": f"连接成功：每月已用 {pct}%", "detail": result}
        return {"ok": False, "message": result.get("error", "连接失败"), "detail": result}

    # ---------------------------------------------------------------- 抓取与解析

    def _fetch(self, record: bool) -> dict:
        now = int(time.time())
        workspace_id = (self.config or {}).get("workspace_id", "")
        auth_cookie = (self.config or {}).get("auth_cookie", "")

        # 配置缺失：结构完整但 ok:false
        if not workspace_id or not auth_cookie:
            return self._fail("缺少配置：workspace_id / auth_cookie 未设置", cookie_valid=False, now=now)

        headers = {
            "Cookie": f"auth={auth_cookie}",
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        try:
            resp = requests.get(
                BASE_URL.format(workspace_id), headers=headers, timeout=20, allow_redirects=True
            )
        except requests.RequestException as e:
            # 网络层失败：cookie 无法判断，按有效处理（走 fetch_fail 事件而非 cookie_fail）
            return self._fail(f"网络错误: {e}", cookie_valid=True, now=now)

        # ---- cookie 失效检测 ----
        # 1) 被重定向（登录页跳转）；2) 最终 URL 落在登录页
        if resp.history or "sign-in" in resp.url or "signin" in resp.url or "login" in resp.url:
            return self._fail("登录过期（Cookie 失效）", cookie_valid=False, now=now)

        if resp.status_code != 200:
            return self._fail(f"HTTP {resp.status_code}", cookie_valid=True, now=now)

        # ---- 页面解析 ----
        html = resp.text
        matches = RE_ITEM.findall(html)
        if len(matches) < 3:
            # 页面里连 resetInSec 都没有 → 大概率被跳到了别的页面（cookie 失效）
            if "resetInSec" not in html:
                return self._fail("登录过期（Cookie 失效）", cookie_valid=False, now=now)
            return self._fail("页面结构变化，无法解析", cookie_valid=True, now=now)

        KEY_MAP = {"rollingUsage": "rolling", "weeklyUsage": "weekly", "monthlyUsage": "monthly"}
        items = {}
        for name, status, reset, pct in matches:
            items[KEY_MAP.get(name, name)] = {
                "status": status,
                "reset_in_sec": int(reset),
                "usage_percent": int(pct),
            }

        # 余额：useBalance 为 true 时才有意义，否则金额按 0
        balance_m = RE_BALANCE.search(html)
        use_m = RE_USE_BALANCE.search(html)
        zen_balance = float(balance_m.group(1)) if balance_m else 0.0
        use_balance = use_m.group(1) == "true" if use_m else False

        # ---- 组装标准化结果 ----
        result = {
            "provider": self.id,
            "ok": True,
            "fetched_at": now,
            "cookie_valid": True,
            "plan_name": self.plan_name,
            "site": self.site,
            "limits": [
                {"id": "rolling", "label": "5h 滚动",
                 "used_pct": items["rolling"]["usage_percent"],
                 "reset_in_sec": items["rolling"]["reset_in_sec"]},
                {"id": "weekly", "label": "每周",
                 "used_pct": items["weekly"]["usage_percent"],
                 "reset_in_sec": items["weekly"]["reset_in_sec"]},
                {"id": "monthly", "label": "每月",
                 "used_pct": items["monthly"]["usage_percent"],
                 "reset_in_sec": items["monthly"]["reset_in_sec"]},
            ],
            "balance": {"currency": "USD", "amount": zen_balance if use_balance else 0.0},
            "meta": {},
        }

        # ---- 落快照 + 推算 meta ----
        if record:
            store.append(self._snap_id(), result)
        current_pct = items["monthly"]["usage_percent"]
        result["meta"] = self._build_meta(current_pct, now)
        return result

    def _snap_id(self) -> str:
        """快照文件标识：优先用实例 pid（kernel 注入，多实例隔离），
        未注入时退回类 id（单实例兼容，行为与旧版一致）。"""
        return getattr(self, "pid", None) or self.id

    def _fail(self, error: str, cookie_valid: bool, now: int) -> dict:
        """构造失败结果：结构完整（INTERFACES.md §2 要求 ok:false 仍带全字段）。"""
        return {
            "provider": self.id,
            "ok": False,
            "fetched_at": now,
            "cookie_valid": cookie_valid,
            "plan_name": self.plan_name,
            "limits": [],
            "balance": {"currency": "USD", "amount": 0.0},
            "meta": {},
            "error": error,
        }

    # ---------------------------------------------------------------- meta 推算

    def _build_meta(self, current_pct: int, now: int) -> dict:
        """今日用量 + 三层速度推算 + 月度金额 + token 估算。"""
        snaps = store.snapshots(self._snap_id(), hours=720)  # 30 天快照
        used_usd = round(current_pct / 100.0 * MONTHLY_LIMIT_USD, 2)
        # token 估算：按常用模型输出费率（默认 DeepSeek V4 Flash）
        est_model = str((self.config or {}).get("est_model") or "deepseek-v4-flash")
        price = OC_MODEL_PRICES.get(est_model, OC_MODEL_PRICES["deepseek-v4-flash"])
        total_tokens = int(MONTHLY_LIMIT_USD / price * 1_000_000)
        used_tokens = int(total_tokens * current_pct / 100.0)
        today = self._today_meta(current_pct, snaps, now)
        week_pct = self._week_pct(current_pct, snaps, now)
        # 今日消耗 token + 每日消耗 token 序列（百分比 × 总 token）
        today["today_tokens"] = int(today.get("delta_pct", 0.0) / 100.0 * total_tokens)
        week_tokens = [int(v / 100.0 * total_tokens) for v in week_pct]
        return {
            "today": today,
            "speed": self._speed_meta(current_pct, snaps, now),
            "week_pct": week_pct,
            "week_tokens": week_tokens,
            "monthly_limit_usd": MONTHLY_LIMIT_USD,
            "used_usd": used_usd,
            "est_price_per_mtok": price,
            "est_model": est_model,
            "est_model_label": OC_MODEL_LABELS.get(est_model, est_model),
            "used_tokens": used_tokens,
            "available_tokens": total_tokens - used_tokens,
            "total_tokens": total_tokens,
        }

    @staticmethod
    def _week_pct(current_pct: int, snaps: list, now: int) -> list:
        """近 5 天每日消耗（%）：当日月度峰值 − 前日峰值。跨月重置自动跳过。"""
        day_max = {}
        for s in snaps:
            day = time.strftime("%Y-%m-%d", time.localtime(s["ts"]))
            pct = s["monthly_pct"]
            if day not in day_max or pct > day_max[day]:
                day_max[day] = pct
        today = time.strftime("%Y-%m-%d", time.localtime(now))
        day_max[today] = max(day_max.get(today, 0), current_pct)
        days = sorted(day_max.items())
        out = []
        for i in range(max(0, len(days) - 5), len(days)):
            prev = days[i - 1][1] if i > 0 else days[i][1]
            out.append(round(max(0.0, days[i][1] - prev), 1))
        return out

    def _today_meta(self, current_pct: int, snaps: list, now: int) -> dict:
        """今日用量：当前月度百分比 − 今日基准（0 点前最后一条快照，否则今天第一条）。"""
        dst = store.day_start_ts(now)
        base = self._find_today_base(snaps, dst)
        # 跨月重置 / 数据回跳：current 比基准还小，改用今天第一条快照
        if base is not None and current_pct < base["monthly_pct"]:
            today_snaps = [s for s in snaps if s["ts"] >= dst]
            base = today_snaps[0] if today_snaps else None

        if base is None:
            return {"delta_pct": 0.0, "delta_usd": 0.0, "base_label": None, "since_midnight": False}

        delta_pct = max(0.0, float(current_pct) - base["monthly_pct"])
        return {
            "delta_pct": round(delta_pct, 1),
            "delta_usd": round(delta_pct / 100.0 * MONTHLY_LIMIT_USD, 2),
            "base_label": time.strftime("%H:%M", time.localtime(base["ts"])),
            "since_midnight": base["ts"] < dst,
        }

    def _find_today_base(self, snaps: list, dst: int) -> dict | None:
        """找今日基准：0 点之前最后一条快照；没有则用今天第一条。"""
        base = None
        for s in snaps:  # 快照升序
            if s["ts"] < dst:
                base = s
            else:
                break
        if base is None:
            today_snaps = [s for s in snaps if s["ts"] >= dst]
            if today_snaps:
                base = today_snaps[0]
        return base

    def _speed_meta(self, current_pct: int, snaps: list, now: int) -> dict:
        """双指标速度推算：
        - 当前烧速（三层：trend > today > short）——"按现在这速度还能用几天"
        - 科学日均（近 N 天每日消耗平均）——贴合周期性使用模式
        各自带来源标注；数据不足时对应指标为"积累中"。
        """
        result = {}
        # ---- 指标一：当前烧速 ----
        hourly_pct, source = self._estimate_speed(current_pct, snaps, now)
        if hourly_pct <= 0:
            result.update({"hourly_pct": 0.0, "days_left": None,
                           "days_left_text": "—", "source": ""})
        else:
            days_left = (100.0 - current_pct) / (hourly_pct * 24)
            result.update({
                "hourly_pct": round(hourly_pct, 2),
                "days_left": round(days_left, 1),
                "days_left_text": _fmt_hours(days_left * 24),
                "source": source,
            })
        # ---- 指标二：科学日均（近 N 天）----
        avg_daily, avg_source, avg_days = self._estimate_daily_avg(
            current_pct, snaps, now)
        if avg_daily > 0:
            avg_days_left = (100.0 - current_pct) / avg_daily
            result.update({
                "avg_daily_pct": round(avg_daily, 2),
                "avg_days_left": round(avg_days_left, 1),
                "avg_days_left_text": _fmt_hours(avg_days_left * 24),
                "avg_source": avg_source,
                "avg_sample_days": avg_days,
                "data_ready": True,
            })
        else:
            result.update({
                "avg_daily_pct": 0.0, "avg_days_left": None,
                "avg_days_left_text": "—", "avg_source": "",
                "avg_sample_days": 0, "data_ready": False,
            })
        return result

    @staticmethod
    def _estimate_daily_avg(current_pct: int, snaps: list, now: int):
        """近 N 天日均消耗（%/天）。按本地日期取每日峰值，逐日差值平均，
        自动跳过跨月重置。返回 (daily_pct, 来源文字, 样本天数)。"""
        from collections import OrderedDict
        day_max = OrderedDict()
        for s in snaps:
            day = time.strftime("%Y-%m-%d", time.localtime(s["ts"]))
            pct = s["monthly_pct"]
            if day not in day_max or pct > day_max[day]:
                day_max[day] = pct
        today = time.strftime("%Y-%m-%d", time.localtime(now))
        day_max[today] = max(day_max.get(today, 0), current_pct)
        days = list(day_max.items())
        deltas = []
        for i in range(1, len(days)):
            d = days[i][1] - days[i - 1][1]
            if 0 < d <= 100:  # 排除跨月重置（负值）与异常跳变
                deltas.append(d)
        if len(deltas) < 2:  # 至少 3 天跨度才有意义，否则算"积累中"
            return 0.0, "", 0
        recent = deltas[-3:]  # 近 3 日趋势（贴合近期使用模式）
        avg = sum(recent) / len(recent)
        return avg, "近3日日均", len(recent)

    def _estimate_speed(self, current_pct: int, snaps: list, now: int) -> tuple:
        """返回 (hourly_pct, source)；无可用速度时 (0.0, "")。"""
        # ---- L3 趋势：最小二乘线性回归（快照 ≥ 6 条且跨度 ≥ 6h）----
        trend_seg = self._post_reset_segment(snaps)
        if len(trend_seg) >= TREND_MIN_SNAPS and \
                (trend_seg[-1]["ts"] - trend_seg[0]["ts"]) >= TREND_MIN_SPAN_SEC:
            slope = self._least_squares_hourly(trend_seg)  # 每小时消耗的月度百分比
            if slope > 0:
                return slope, "trend"

        # ---- L2 今日平均（今日基准存在且 elapsed ≥ 2h）----
        dst = store.day_start_ts(now)
        base = self._find_today_base(snaps, dst)
        if base is not None and current_pct >= base["monthly_pct"]:
            elapsed_h = (now - base["ts"]) / 3600.0
            if elapsed_h >= TODAY_MIN_ELAPSED_SEC / 3600.0:
                hourly = (current_pct - base["monthly_pct"]) / elapsed_h
                if hourly > 0:
                    return hourly, "today"

        # ---- L1 近 1 小时窗口 Δ%/Δt（最新 vs 约 1 小时前，5 分钟抓取也适用）----
        if len(snaps) >= 2:
            target = now - SHORT_WINDOW_SEC
            older = None
            for s in reversed(snaps):
                if s["ts"] <= target:
                    older = s
                    break
            if older is not None and snaps[-1]["ts"] > older["ts"]:
                dt_h = (snaps[-1]["ts"] - older["ts"]) / 3600.0
                if dt_h >= SHORT_MIN_WINDOW_SEC / 3600.0:
                    delta = snaps[-1]["monthly_pct"] - older["monthly_pct"]
                    hourly = delta / dt_h
                    if hourly > 0:
                        return hourly, "short"

        return 0.0, ""

    @staticmethod
    def _post_reset_segment(snaps: list) -> list:
        """取最近一段无跨月重置的快照序列（从最新往回找，遇大回跳截断）。"""
        if not snaps:
            return []
        seg = []
        newest_pct = None
        for s in reversed(snaps):  # 从新到旧
            if newest_pct is not None and s["monthly_pct"] > newest_pct + RESET_DROP_PCT:
                break  # 比最新值还高出一截 → 跨过了月度重置点
            seg.append(s)
            if newest_pct is None:
                newest_pct = s["monthly_pct"]
        seg.reverse()
        return seg

    @staticmethod
    def _least_squares_hourly(seg: list) -> float:
        """最小二乘拟合 pct ~ 时间（小时），返回斜率（每小时消耗的月度百分比）。"""
        t0 = seg[0]["ts"]
        xs = [(s["ts"] - t0) / 3600.0 for s in seg]
        ys = [float(s["monthly_pct"]) for s in seg]
        n = len(xs)
        mx = sum(xs) / n
        my = sum(ys) / n
        sxx = sum((x - mx) ** 2 for x in xs)
        sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        if sxx <= 0:
            return 0.0
        return sxy / sxx
