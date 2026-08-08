# -*- coding: utf-8 -*-
"""成就系统 v0.1（2026-08-08）。

- 23 个成就，5 类：燃烧(burn) / 坚持(stick) / 配置(setup) / 探索(explore)
- 状态持久化：app/data/achievements.json  {unlocked: {id: ts}, flags: {...}}
- 统计全部从真实数据推导（快照历史 + settings），不造假
- token 估算口径与 opencode_go 一致：月度限额 × 用量% × 默认输出费率折算
"""

import json
import os
import time
from datetime import datetime, date

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
STATE_FILE = os.path.join(DATA_DIR, "achievements.json")

# opencode Go 月度限额（与 opencode_go.py 保持一致）
MONTHLY_LIMIT_USD = 60.0
# 默认输出费率（美元/百万 token，与 opencode_go 默认 DeepSeek V4 Flash 一致）
DEFAULT_PRICE = 2.0

# 成就定义：(id, 类别, tier, 图标, 名称zh, 名称en, 描述zh, 描述en, 目标值, 单位)
# tier: 1=铜 2=银 3=金；target=None 表示布尔型（有 flag 即解锁）
ACHIEVEMENTS = [
    # ---- 燃烧类：token / 金额消耗 ----
    ("burn_first",   "burn", 1, "🔥", "初燃",      "First Burn",      "累计消耗 10 万 token",            "Burn 100K tokens in total",            100_000,     "tokens"),
    ("burn_mil",     "burn", 1, "⚡", "烈焰",      "Flame",           "累计消耗 100 万 token",           "Burn 1M tokens in total",              1_000_000,   "tokens"),
    ("burn_10mil",   "burn", 2, "🌋", "熔炉",      "Furnace",         "累计消耗 1000 万 token",          "Burn 10M tokens in total",             10_000_000,  "tokens"),
    ("burn_100mil",  "burn", 2, "💥", "百万吨级",  "Megaton",         "累计消耗 1 亿 token",             "Burn 100M tokens in total",            100_000_000, "tokens"),
    ("burn_bil",     "burn", 3, "💎", "亿万吨级",  "Gigaton",         "累计消耗 10 亿 token",            "Burn 1B tokens in total",              1_000_000_000, "tokens"),
    ("burn_50pct",   "burn", 1, "📈", "冲榜者",    "Top Burner",      "单月用量达到 50%",                "Reach 50% monthly usage",              50,          "pct"),
    ("burn_90pct",   "burn", 2, "♨️", "极致燃烧",  "Max Burn",        "单月用量达到 90%",                "Reach 90% monthly usage",              90,          "pct"),
    ("spend_5",      "burn", 1, "💸", "破费者",    "Spender",         "累计消耗 $5",                      "Spend $5 in total",                    5,           "usd"),
    ("spend_25",     "burn", 2, "🏦", "挥金如土",  "Big Spender",     "累计消耗 $25",                     "Spend $25 in total",                   25,          "usd"),
    ("spend_100",    "burn", 3, "👑", "一掷千金",  "Whale",           "累计消耗 $100",                    "Spend $100 in total",                  100,         "usd"),
    ("burn_99pct",   "burn", 3, "♨️", "白热化",    "White-Hot",       "单月用量达到 99%",                 "Reach 99% monthly usage",             99,          "pct"),
    ("burn_day_mil", "burn", 2, "🌋", "今日之王",  "Day Emperor",     "单日燃烧 100 万 token",            "Burn 1M tokens in a single day",       1_000_000,   "day_tokens"),
    # ---- 坚持类：连续 / 累计监控 ----
    ("stick_3",      "stick", 1, "📆", "三日之约",  "3-Day Watch",     "连续监控 3 天",                    "Monitor for 3 days in a row",          3,           "days"),
    ("stick_7",      "stick", 1, "📅", "七日之约",  "Week Watch",      "连续监控 7 天",                    "Monitor for 7 days in a row",          7,           "days"),
    ("stick_14",     "stick", 2, "🗓️", "双周守望",  "Fortnight",       "连续监控 14 天",                   "Monitor for 14 days in a row",         14,          "days"),
    ("stick_30",     "stick", 2, "🏅", "月度全勤",  "Monthly Grind",   "累计监控 30 天",                   "Monitor for 30 days in total",         30,          "days"),
    ("stick_90",     "stick", 3, "🏆", "季度守望",  "Quarter Keeper",  "累计监控 90 天",                   "Monitor for 90 days in total",         90,          "days"),
    ("stick_180",    "stick", 3, "🎖️", "半年守望",  "Half-Year Keeper", "累计监控 180 天",                  "Monitor for 180 days in total",        180,         "days"),
    ("stick_365",    "stick", 3, "🏅", "周年庆典",  "Anniversary",     "累计监控 365 天",                   "Monitor for a full year",              365,         "days"),
    ("stick_night",  "stick", 1, "🌙", "夜猫子",    "Night Owl",       "在 23:00–05:00 打开过软件",        "Open the app between 11pm and 5am",    None,        "flag"),
    ("stick_weekend","stick", 1, "🎮", "周末战士",  "Weekend Warrior", "在周末打开过软件",                 "Open the app on a weekend",            None,        "flag"),
    ("stick_early",  "stick", 1, "🌅", "早鸟",      "Early Bird",      "在 05:00–09:00 打开过软件",        "Open the app between 5am and 9am",     None,        "flag"),
    # ---- 配置类：引导 / 供应商管理 ----
    ("setup_first",  "setup", 1, "🎯", "初试锋芒",  "First Setup",     "引导页完成第一次配置",             "Complete your first setup",            None,        "flag"),
    ("setup_3",      "setup", 1, "🧩", "多面手",    "Multiplexer",     "配置 3 个不同供应商",              "Configure 3 different providers",      3,           "providers"),
    ("setup_6",      "setup", 2, "🗂️", "收藏家",    "Collector",       "配置 6 个供应商",                  "Configure 6 providers",                6,           "providers"),
    ("setup_10",     "setup", 3, "🏛️", "十全十美",  "Decadence",       "配置 10 个供应商",                 "Configure 10 providers",               10,          "providers"),
    ("setup_dual",   "setup", 2, "🔑", "双料特工",  "Double Agent",    "同时使用 API Key 型和 Cookie 型供应商", "Use both API-key and cookie providers", None, "flag"),
    ("setup_apix3",  "setup", 2, "⚙️", "供应商控",  "API Hoarder",     "同时启用 3 个 API Key 型供应商",   "Run 3 API-key providers at once",      3,           "api_count"),
    # ---- 探索类：功能发现 ----
    ("explore_all",  "explore", 2, "👀", "全知者",  "All-Seeing",      "打开过主面板全部页面",             "Visit every main panel page",          None,        "flag"),
    ("explore_tray", "explore", 1, "🪟", "隐形人",  "Invisible",       "用过「隐藏到托盘」",               "Use hide-to-tray",                     None,        "flag"),
    ("explore_mini", "explore", 1, "🖥️", "悬浮大师", "Floating Master", "用过迷你窗",                        "Use the mini widget",                  None,        "flag"),
    ("explore_refresh","explore", 1, "🔄", "手动大师", "Manual Master",  "手动刷新 10 次",                   "Refresh manually 10 times",            10,          "refresh"),
    ("explore_test", "explore", 1, "🧪", "测试狂人",  "Test Junkie",     "测试连接 10 次",                    "Test connections 10 times",            10,          "test"),
    ("explore_theme", "explore", 1, "🎨", "外观控",   "Stylist",         "修改过外观设置",                    "Change appearance settings",           None,        "flag"),
    ("explore_lang", "explore", 1, "🌐", "语言达人",  "Polyglot",        "切换过语言",                         "Switch the language",                  None,        "flag"),
    ("action_refresh1","explore", 1, "💧", "第一滴血", "First Refresh",  "首次手动刷新",                      "Refresh manually for the first time",  1,           "refresh"),
    ("action_test1", "explore", 1, "💎", "试金石",   "Trial Stone",     "首次测试连接",                      "Test a connection for the first time", 1,           "test"),
]

_INDEX = {a[0]: a for a in ACHIEVEMENTS}
CATS = {"burn": "燃烧", "stick": "坚持", "setup": "配置", "explore": "探索"}
CATS_EN = {"burn": "Burn", "stick": "Stick", "setup": "Setup", "explore": "Explore"}


def _load_state():
    if not os.path.exists(STATE_FILE):
        return {"unlocked": {}, "flags": {}}
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"unlocked": {}, "flags": {}}


def _save_state(state):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)


def get_state():
    """供外部读取（如 UI 需要 flags）。"""
    return _load_state()


# ---------------- 统计推导 ----------------

def _monthly_peak_pct(snapshots):
    """按自然月取用量峰值，返回 [(year, month, max_pct)]——跨月累计正确。"""
    by_month = {}
    for s in snapshots:
        pct = s.get("monthly_pct") or 0
        if pct <= 0:
            continue
        ts = s.get("ts") or 0
        d = datetime.fromtimestamp(ts)
        key = (d.year, d.month)
        by_month[key] = max(by_month.get(key, 0), pct)
    return sorted(by_month.items())


def compute_stats(settings, snapshots_by_pid):
    """从快照历史 + settings 推导全部统计。

    snapshots_by_pid: {pid: [快照 dict 列表]}（快照需含 ts/balance/monthly_pct）
    返回 {tokens, usd, month_pct, days_total, days_streak, night, weekend, early,
          max_day_tokens, providers, api_count, has_cookie, has_api, refresh, test,
          setup_first, pages, hide_tray, mini, appearance, lang}
    """
    tokens = 0.0
    usd = 0.0
    month_peaks = []
    all_ts = []
    for pid, snaps in (snapshots_by_pid or {}).items():
        if not snaps:
            continue
        # token / 金额：按月用量峰值累计（opencode 口径）
        for (ym, pct) in _monthly_peak_pct(snaps):
            tokens += MONTHLY_LIMIT_USD / DEFAULT_PRICE * 1_000_000 * pct / 100.0
            usd += MONTHLY_LIMIT_USD * pct / 100.0
            month_peaks.append((ym, pct))
        # API 类（无 monthly_pct）：余额下降 = 消耗金额（单位按快照内提示，统一视为原币种，
        # v0.1 仅累计 USD 口径的 opencode 用量；余额类金额留待 v0.2 精确折算）
        for s in snaps:
            ts = s.get("ts") or 0
            if ts:
                all_ts.append(ts)

    # 天数：按自然日去重
    days = sorted({datetime.fromtimestamp(t).date() for t in all_ts})
    days_total = len(days)
    streak = 0
    if days:
        cur = 1
        best = 1
        for i in range(1, len(days)):
            if (days[i] - days[i - 1]).days == 1:
                cur += 1
                best = max(best, cur)
            else:
                cur = 1
        streak = best

    # 时段 flag：夜猫子 / 周末战士 / 早鸟
    night = False
    weekend = False
    early = False
    for t in all_ts:
        d = datetime.fromtimestamp(t)
        if d.hour >= 23 or d.hour < 5:
            night = True
        if d.weekday() >= 5:
            weekend = True
        if 5 <= d.hour < 9:
            early = True

    # 单日燃烧峰值（今日之王）：按天取用量峰值 → 相邻天差值最大 × 限额（遍历全部 provider）
    day_peaks = {}
    for _pid, _snaps in (snapshots_by_pid or {}).items():
        for s in _snaps or []:
            pct = s.get("monthly_pct") or 0
            if pct <= 0 or not s.get("ts"):
                continue
            d = datetime.fromtimestamp(s["ts"]).date()
            day_peaks[d] = max(day_peaks.get(d, 0), pct)
    max_day_tokens = 0
    sorted_days = sorted(day_peaks.items())
    prev_pct = None
    for _d, pct in sorted_days:
        if prev_pct is not None:
            delta = max(0.0, pct - prev_pct)
            max_day_tokens = max(max_day_tokens,
                                 int(delta / 100.0 * MONTHLY_LIMIT_USD / DEFAULT_PRICE * 1_000_000))
        prev_pct = pct

    # 配置类
    provs = settings.get("providers") or {}
    pids = [p for p, c in provs.items() if c and c.get("enabled") is not False]
    has_cookie = any(
        (provs.get(p) or {}).get("type") == "opencode-go"
        or (provs.get(p) or {}).get("config", {}).get("auth_cookie")
        for p in pids
    )
    has_api = any(
        (provs.get(p) or {}).get("config", {}).get("api_key")
        for p in pids
    )
    api_count = sum(
        1 for p in pids
        if (provs.get(p) or {}).get("config", {}).get("api_key")
    )

    flags = _load_state().get("flags", {})
    # 最近一个自然月的用量峰值（单月成就判定用，不受跨月累计影响）
    month_pct = month_peaks[-1][1] if month_peaks else 0
    return {
        "tokens": int(tokens),
        "usd": round(usd, 2),
        "month_pct": month_pct,
        "days_total": days_total,
        "days_streak": streak,
        "night": night,
        "weekend": weekend,
        "early": early,
        "max_day_tokens": max_day_tokens,
        "providers": len(pids),
        "has_cookie": has_cookie,
        "has_api": has_api,
        "api_count": api_count,
        "refresh": int(flags.get("refresh", 0)),
        "test": int(flags.get("test", 0)),
        "setup_first": bool(settings.get("ui", {}).get("onboarded")) and len(pids) > 0,
        "pages": flags.get("pages", []),
        "hide_tray": flags.get("hide_tray", False),
        "mini": flags.get("mini", False),
        "appearance": flags.get("appearance", False),
        "lang": flags.get("lang", False),
    }


def progress_for(ach_id, stats):
    """单个成就的当前进度值（未达目标前用于进度条）。"""
    a = _INDEX.get(ach_id)
    if not a:
        return 0
    key = {
        "burn_first": "tokens", "burn_mil": "tokens", "burn_10mil": "tokens",
        "burn_100mil": "tokens", "burn_bil": "tokens",
        "burn_50pct": "tokens_pct", "burn_90pct": "tokens_pct", "burn_99pct": "tokens_pct",
        "spend_5": "usd", "spend_25": "usd", "spend_100": "usd",
        "stick_3": "days_streak", "stick_7": "days_streak", "stick_14": "days_streak",
        "stick_30": "days_total", "stick_90": "days_total",
        "stick_180": "days_total", "stick_365": "days_total",
        "setup_3": "providers", "setup_6": "providers", "setup_10": "providers",
        "setup_apix3": "api_count",
        "burn_day_mil": "max_day_tokens",
        "explore_refresh": "refresh", "explore_test": "test",
        "action_refresh1": "refresh", "action_test1": "test",
    }.get(ach_id)
    if key == "tokens_pct":
        return int(min(100, stats.get("month_pct", 0)))
    return stats.get(key, 0) if key else 0


def _is_unlocked(ach_id, stats):
    a = _INDEX.get(ach_id)
    if not a:
        return False
    target, unit = a[8], a[9]
    if unit == "flag":
        if ach_id == "stick_night":
            return stats["night"]
        if ach_id == "stick_weekend":
            return stats["weekend"]
        if ach_id == "stick_early":
            return stats["early"]
        if ach_id == "setup_first":
            return stats["setup_first"]
        if ach_id == "setup_dual":
            return stats["has_cookie"] and stats["has_api"]
        if ach_id == "explore_all":
            return len(set(stats["pages"])) >= 5
        if ach_id == "explore_tray":
            return stats["hide_tray"]
        if ach_id == "explore_mini":
            return stats["mini"]
        if ach_id == "explore_theme":
            return stats["appearance"]
        if ach_id == "explore_lang":
            return stats["lang"]
        return False
    if unit == "tokens":
        return stats["tokens"] >= target
    if unit == "usd":
        return stats["usd"] >= target
    if unit == "day_tokens":
        return stats["max_day_tokens"] >= target
    if unit == "api_count":
        return stats["api_count"] >= target
    if unit == "refresh":
        return stats["refresh"] >= target
    if unit == "test":
        return stats["test"] >= target
    if unit == "pct":
        cur = stats.get("month_pct", 0)
        return cur >= target
    if unit == "days":
        key = "days_streak" if ach_id in ("stick_3", "stick_7", "stick_14") else "days_total"
        return stats[key] >= target
    if unit == "providers":
        return stats["providers"] >= target
    return False


def check_and_unlock(settings, snapshots_by_pid):
    """计算全部成就 → 新解锁写入状态 → 返回新解锁列表 [{id, name, icon, ts}]。"""
    stats = compute_stats(settings, snapshots_by_pid)
    state = _load_state()
    unlocked = state.setdefault("unlocked", {})
    new_ones = []
    now = int(time.time())
    for a in ACHIEVEMENTS:
        aid = a[0]
        if aid in unlocked:
            continue
        if _is_unlocked(aid, stats):
            unlocked[aid] = now
            new_ones.append({
                "id": aid, "name": a[4], "name_en": a[5],
                "icon": a[3], "ts": now,
            })
    if new_ones:
        _save_state(state)
    return new_ones


def record_flag(name, value=True):
    """行为类 flag 持久化（页面访问/托盘/迷你窗等）。"""
    state = _load_state()
    flags = state.setdefault("flags", {})
    if name == "page_visited":
        pages = flags.setdefault("pages", [])
        if value not in pages:
            pages.append(value)
    elif name == "hide_tray":
        flags["hide_tray"] = True
    elif name == "mini":
        flags["mini"] = True
    elif name == "refresh":
        flags["refresh"] = int(flags.get("refresh", 0)) + 1
    elif name == "test":
        flags["test"] = int(flags.get("test", 0)) + 1
    elif name == "appearance":
        flags["appearance"] = True
    elif name == "lang":
        flags["lang"] = True
    _save_state(state)


def get_achievements(settings, snapshots_by_pid):
    """完整成就列表 + 解锁状态 + 进度（供 UI）。"""
    stats = compute_stats(settings, snapshots_by_pid)
    state = _load_state()
    unlocked = state.get("unlocked", {})
    items = []
    for a in ACHIEVEMENTS:
        aid = a[0]
        items.append({
            "id": aid,
            "cat": a[1],
            "tier": a[2],
            "icon": a[3],
            "name": a[4],
            "name_en": a[5],
            "desc": a[6],
            "desc_en": a[7],
            "target": a[8],
            "unit": a[9],
            "unlocked": aid in unlocked,
            "ts": unlocked.get(aid),
            "progress": min(progress_for(aid, stats), a[8] or 1) if a[8] else 0,
        })
    return {
        "list": items,
        "total": len(items),
        "unlocked_count": len(unlocked),
    }
