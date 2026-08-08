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
    # ---- 坚持类：连续 / 累计监控 ----
    ("stick_3",      "stick", 1, "📆", "三日之约",  "3-Day Watch",     "连续监控 3 天",                    "Monitor for 3 days in a row",          3,           "days"),
    ("stick_7",      "stick", 1, "📅", "七日之约",  "Week Watch",      "连续监控 7 天",                    "Monitor for 7 days in a row",          7,           "days"),
    ("stick_14",     "stick", 2, "🗓️", "双周守望",  "Fortnight",       "连续监控 14 天",                   "Monitor for 14 days in a row",         14,          "days"),
    ("stick_30",     "stick", 2, "🏅", "月度全勤",  "Monthly Grind",   "累计监控 30 天",                   "Monitor for 30 days in total",         30,          "days"),
    ("stick_90",     "stick", 3, "🏆", "季度守望",  "Quarter Keeper",  "累计监控 90 天",                   "Monitor for 90 days in total",         90,          "days"),
    ("stick_night",  "stick", 1, "🌙", "夜猫子",    "Night Owl",       "在 23:00–05:00 打开过软件",        "Open the app between 11pm and 5am",    None,        "flag"),
    ("stick_weekend","stick", 1, "🎮", "周末战士",  "Weekend Warrior", "在周末打开过软件",                 "Open the app on a weekend",            None,        "flag"),
    # ---- 配置类：引导 / 供应商管理 ----
    ("setup_first",  "setup", 1, "🎯", "初试锋芒",  "First Setup",     "引导页完成第一次配置",             "Complete your first setup",            None,        "flag"),
    ("setup_3",      "setup", 1, "🧩", "多面手",    "Multiplexer",     "配置 3 个不同供应商",              "Configure 3 different providers",      3,           "providers"),
    ("setup_6",      "setup", 2, "🗂️", "收藏家",    "Collector",       "配置 6 个供应商",                  "Configure 6 providers",                6,           "providers"),
    ("setup_dual",   "setup", 2, "🔑", "双料特工",  "Double Agent",    "同时使用 API Key 型和 Cookie 型供应商", "Use both API-key and cookie providers", None, "flag"),
    # ---- 探索类：功能发现 ----
    ("explore_all",  "explore", 2, "👀", "全知者",  "All-Seeing",      "打开过主面板全部页面",             "Visit every main panel page",          None,        "flag"),
    ("explore_tray", "explore", 1, "🪟", "隐形人",  "Invisible",       "用过「隐藏到托盘」",               "Use hide-to-tray",                     None,        "flag"),
    ("explore_mini", "explore", 1, "🖥️", "悬浮大师", "Floating Master", "用过迷你窗",                        "Use the mini widget",                  None,        "flag"),
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
    返回 {tokens, usd, days_total, days_streak, night, weekend, providers, has_cookie, pages, hide_tray, mini}
    """
    tokens = 0.0
    usd = 0.0
    all_ts = []
    for pid, snaps in (snapshots_by_pid or {}).items():
        if not snaps:
            continue
        # token / 金额：按月用量峰值累计（opencode 口径）
        for (_, _m), pct in _monthly_peak_pct(snaps):
            tokens += MONTHLY_LIMIT_USD / DEFAULT_PRICE * 1_000_000 * pct / 100.0
            usd += MONTHLY_LIMIT_USD * pct / 100.0
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

    # 时段 flag：夜猫子 / 周末战士
    night = False
    weekend = False
    for t in all_ts:
        d = datetime.fromtimestamp(t)
        if d.hour >= 23 or d.hour < 5:
            night = True
        if d.weekday() >= 5:
            weekend = True

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

    flags = _load_state().get("flags", {})
    return {
        "tokens": int(tokens),
        "usd": round(usd, 2),
        "days_total": days_total,
        "days_streak": streak,
        "night": night,
        "weekend": weekend,
        "providers": len(pids),
        "has_cookie": has_cookie,
        "has_api": has_api,
        "setup_first": bool(settings.get("ui", {}).get("onboarded")) and len(pids) > 0,
        "pages": flags.get("pages", []),
        "hide_tray": flags.get("hide_tray", False),
        "mini": flags.get("mini", False),
    }


def progress_for(ach_id, stats):
    """单个成就的当前进度值（未达目标前用于进度条）。"""
    a = _INDEX.get(ach_id)
    if not a:
        return 0
    key = {
        "burn_first": "tokens", "burn_mil": "tokens", "burn_10mil": "tokens",
        "burn_100mil": "tokens", "burn_bil": "tokens",
        "burn_50pct": "tokens_pct", "burn_90pct": "tokens_pct",
        "spend_5": "usd", "spend_25": "usd",
        "stick_3": "days_streak", "stick_7": "days_streak", "stick_14": "days_streak",
        "stick_30": "days_total", "stick_90": "days_total",
        "setup_3": "providers", "setup_6": "providers",
    }.get(ach_id)
    if key == "tokens_pct":
        return int(min(100, stats["tokens"] / (MONTHLY_LIMIT_USD / DEFAULT_PRICE * 1_000_000) * 100)) if stats["tokens"] else 0
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
        return False
    if unit == "tokens":
        return stats["tokens"] >= target
    if unit == "usd":
        return stats["usd"] >= target
    if unit == "pct":
        cur = stats["tokens"] / (MONTHLY_LIMIT_USD / DEFAULT_PRICE * 1_000_000) * 100
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
