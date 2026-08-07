# -*- coding: utf-8 -*-
"""设置读写：config.json 与内置默认值的深合并。

契约（INTERFACES.md §1）：
- load()            -> dict   读 config.json，与默认值深合并，未知键保留
- save(patch: dict) -> dict   顶层 key 整体替换对应子 dict，写回 config.json
- get(path)         -> value  点路径读取（如 "notify.threshold"）
- set(path, value)  -> dict   点路径精准修改并写回

顶层 key 整体替换语义（契约原文）：
  patch = {"notify": {"threshold": 90}} 会让 notify 整组被替换，
  只留下 {"threshold": 90}。前端每次保存应当传完整的子 dict。
  为兼容精细修改，key 含 "." 时按点路径精准设置（不整体替换）。
"""

from __future__ import annotations

import json
import os
from pathlib import Path

# 项目根（app/ 的上一级）下的 config.json
CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"

# 内置默认值，结构与 INTERFACES.md §1 一致
DEFAULTS: dict = {
    "providers": {},
    "refresh_interval_sec": 300,
    "theme": {"id": "paper", "variant": None},
    "opacity": {"main": 0.95, "mini": 0.92},
    "window": {
        "main_width": 920,
        "main_height": 600,
        "mini_width": 300,
        "mini_height": 170,
        "mini_corner": "bottom-right",
    },
    "mini_widget_enabled": True,
    "diy": {
        "mini_provider": "",
        "modules": {
            "balance": {"bal_main": True, "meta_grid": True, "token_est": True, "chart": True},
            "quota": {"progress": True, "tokens": True, "chart": True},
        },
    },
    "density": "compact",
    "currency": "usd",
    "display": {
        "unit": "auto",
        "fx_rate": 7.2,
    },
    "order": {
        "providers": [],
    },
    "notify": {
        "method": "tray",
        "threshold": 80,
        "urgent": 95,
        "events": {
            "threshold": True,
            "urgent": True,
            "cookie_fail": True,
            "fetch_fail": True,
        },
    },
    "start_with_windows": False,
}

# 内存态缓存（供 get/set 使用），首次 load 时填充
_current: dict | None = None


# ---------------------------------------------------------------- 内部工具

def _deep_merge(base: dict, override: dict) -> dict:
    """深合并：override 递归覆盖 base，未知键保留（override 的键全部并入）。"""
    out = dict(base)
    for key, value in override.items():
        if key in out and isinstance(out[key], dict) and isinstance(value, dict):
            # 两侧都是 dict 时递归合并，保证默认值里的深层键被补齐
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def _read_file() -> dict:
    """读磁盘上的 config.json；文件不存在或损坏时返回 {}。敏感字段解密为明文。"""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            _walk_secrets(data, _dpapi_decrypt)
        return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[settings] 读取 config.json 失败：{exc}")
        return {}


"""DPAPI 加密/解密（Windows 当前用户级）；非 Windows 或失败退化为明文。"""
_SECRET_KEYS = {"api_key", "auth_cookie"}
_DPAPI_PREFIX = "DPAPI:"


def _dblob(data: bytes):
    import ctypes
    import ctypes.wintypes

    class _BLOB(ctypes.Structure):
        _fields_ = [("cbData", ctypes.wintypes.DWORD),
                    ("pbData", ctypes.POINTER(ctypes.c_byte))]

    buf = ctypes.create_string_buffer(data, len(data))
    return _BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_byte)))


def _dpapi_encrypt(plain: str) -> str:
    """CryptProtectData 加密；失败返回原明文（不阻塞功能）。已加密的值不再重复加密（幂等）。"""
    if not isinstance(plain, str) or plain.startswith(_DPAPI_PREFIX):
        return plain
    if os.name != "nt":
        return plain
    try:
        import base64
        import ctypes
        blob_in = _dblob(plain.encode("utf-8"))
        blob_out = _dblob(b"")
        ok = ctypes.windll.crypt32.CryptProtectData(
            ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out))
        if ok and blob_out.cbData:
            data = ctypes.string_at(blob_out.pbData, blob_out.cbData)
            ctypes.windll.kernel32.LocalFree(blob_out.pbData)
            return _DPAPI_PREFIX + base64.b64encode(data).decode()
    except Exception:
        pass
    return plain


def _dpapi_decrypt(value: str):
    """解密 DPAPI 密文；非 DPAPI 前缀原样返回；解密失败返回 None。"""
    if not isinstance(value, str) or not value.startswith(_DPAPI_PREFIX):
        return value
    if os.name != "nt":
        return value
    try:
        import base64
        import ctypes
        raw = base64.b64decode(value[len(_DPAPI_PREFIX):])
        blob_in = _dblob(raw)
        blob_out = _dblob(b"")
        ok = ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out))
        if ok and blob_out.cbData:
            data = ctypes.string_at(blob_out.pbData, blob_out.cbData)
            ctypes.windll.kernel32.LocalFree(blob_out.pbData)
            return data.decode("utf-8")
    except Exception:
        pass
    return None


def _walk_secrets(cfg: dict, fn) -> None:
    """递归遍历所有 dict，对 _SECRET_KEYS 命中的值应用 fn（返回新值并写回）。"""
    for key, val in list(cfg.items()):
        if isinstance(val, dict):
            _walk_secrets(val, fn)
        elif key in _SECRET_KEYS and isinstance(val, str):
            cfg[key] = fn(val)


def _write_file(cfg: dict) -> None:
    """写回 config.json：敏感字段先加密，原子写防并发撕裂。"""
    _walk_secrets(cfg, _dpapi_encrypt)
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    _tmp = CONFIG_PATH.with_suffix(".tmp")
    with open(_tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    os.replace(_tmp, CONFIG_PATH)


def _split_path(path: str) -> list[str]:
    """点路径切分，空串返回 []。"""
    if not path:
        return []
    return [seg for seg in path.split(".") if seg]


# ---------------------------------------------------------------- 公开 API

def load() -> dict:
    """读配置：磁盘内容与默认值深合并，未知键保留。返回全量 dict。"""
    global _current
    disk = _read_file()
    merged = _deep_merge(DEFAULTS, disk)
    _current = merged
    return merged


def save(patch: dict) -> dict:
    """应用 patch 并写回。

    - 顶层 key 整体替换对应子 dict（浅合并语义，契约 §1）
    - key 含 "." 时按点路径精准修改（如 {"notify.threshold": 90}）
    - 未知顶层键保留原样，不删除
    """
    global _current
    cfg = dict(_current) if _current is not None else load()
    if not isinstance(patch, dict):
        raise TypeError("patch 必须是 dict")
    for key, value in patch.items():
        if not isinstance(key, str):
            continue
        if "." in key:
            _set_path(cfg, key, value)
        else:
            cfg[key] = value
    _write_file(cfg)
    _current = cfg
    return cfg


def get(path: str = "") -> object:
    """点路径读取；path 为空返回全量。路径不存在返回 None。"""
    cfg = _current if _current is not None else load()
    segs = _split_path(path)
    node = cfg
    for seg in segs:
        if not isinstance(node, dict) or seg not in node:
            return None
        node = node[seg]
    return node


def set(path: str, value: object) -> dict:
    """点路径精准设置并写回，等价于 save({path: value})。返回新全量。"""
    return save({path: value})


def _set_path(cfg: dict, path: str, value: object) -> None:
    """在内存 dict 上按点路径写入（中间层不存在时自动创建）。"""
    segs = _split_path(path)
    if not segs:
        return
    node = cfg
    for seg in segs[:-1]:
        if not isinstance(node.get(seg), dict):
            node[seg] = {}
        node = node[seg]
    node[segs[-1]] = value


# 便于外部判断项目根（如 D 的 main.py 定位 ui/ 目录）
PROJECT_ROOT = CONFIG_PATH.parent
