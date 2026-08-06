"""快照存储（app/store.py）：per-provider JSON 文件，保留 30 天（720 小时）。

文件位置：app/data/snapshots/{provider_id}.json
接口（INTERFACES.md §2）：
    append(provider_id, result)      # 把一次成功抓取的标准化结果追加为快照
    snapshots(provider_id, hours=720)  # 读取快照列表（升序，按时间裁剪）
    clear(provider_id)               # 删除该 provider 的快照文件

快照条目结构（沿用 v0.1 store.py 口径）：
    {"ts": 时间戳, "monthly_pct": int, "weekly_pct": int, "rolling_pct": int}
余额型（DeepSeek/Kimi 等按量供应商）无百分比窗口：
    monthly_pct 等保留为 0 占位，另存 balance 字段（可用余额，用于消耗速度/还能撑推算）
"""
import json
import os
import time

# app/data/snapshots/ 目录（相对本文件定位，与工作目录无关）
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "snapshots")

# 保留时长：30 天
KEEP_HOURS = 720


def _path(provider_id: str) -> str:
    """返回某 provider 的快照文件绝对路径。"""
    return os.path.join(DATA_DIR, f"{provider_id}.json")


def _read(provider_id: str) -> list:
    """读取原始快照列表（不做时间裁剪，仅做格式过滤）。文件缺失/损坏返回 []。"""
    try:
        with open(_path(provider_id), encoding="utf-8") as f:
            data = json.load(f)
        snaps = data.get("snapshots", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    # 过滤异常条目：必须是 dict 且含 ts；配额型要 monthly_pct，余额型要 balance
    return [s for s in snaps if isinstance(s, dict) and "ts" in s
            and ("monthly_pct" in s or "balance" in s)]


def append(provider_id: str, result: dict) -> None:
    """把一次成功抓取的标准化结果追加为快照。

    失败结果（ok:false）不落盘；相同 ts 视为同一条快照，不重复追加。
    追加后按 KEEP_HOURS 裁剪，防止文件膨胀。
    """
    if not result.get("ok"):
        return
    # 从 limits 数组里取三个维度的用量百分比
    limits = {item.get("id"): item for item in result.get("limits", []) if isinstance(item, dict)}
    snap = {
        "ts": int(time.time()),
        "monthly_pct": (limits.get("monthly") or {}).get("used_pct", 0),
        "weekly_pct": (limits.get("weekly") or {}).get("used_pct", 0),
        "rolling_pct": (limits.get("rolling") or {}).get("used_pct", 0),
    }
    # 余额型：把可用余额存进快照（消耗速度推算用）
    bal = result.get("balance") or {}
    if isinstance(bal.get("amount"), (int, float)):
        snap["balance"] = round(float(bal["amount"]), 6)
    snaps = _read(provider_id)
    # 同一秒内的重复抓取不落盘
    if snaps and snaps[-1].get("ts") == snap["ts"]:
        return
    snaps.append(snap)
    # 裁剪：只保留最近 KEEP_HOURS
    cutoff = int(time.time()) - KEEP_HOURS * 3600
    snaps = [s for s in snaps if s["ts"] >= cutoff]
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(_path(provider_id), "w", encoding="utf-8") as f:
        json.dump({"snapshots": snaps}, f, ensure_ascii=False)


def snapshots(provider_id: str, hours: int = 720) -> list:
    """读取某 provider 的快照列表。

    返回按 ts 升序排列、只保留最近 hours 小时（默认 720 = 30 天）的条目。
    """
    snaps = _read(provider_id)
    cutoff = int(time.time()) - hours * 3600
    snaps = [s for s in snaps if s["ts"] >= cutoff]
    snaps.sort(key=lambda s: s["ts"])
    return snaps


def clear(provider_id: str) -> None:
    """删除该 provider 的快照文件（不存在时静默通过）。"""
    try:
        os.remove(_path(provider_id))
    except FileNotFoundError:
        pass


def day_start_ts(ts: int) -> int:
    """本地时区的当天 0 点时间戳（供今日用量基准计算用）。"""
    lt = time.localtime(ts)
    return int(time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday, 0, 0, 0, 0, 0, -1)))
