#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""OC-GO Dashboard CLI：agent / 脚本程序化配置供应商（密钥走 DPAPI 加密落盘）。

用法：
  python cli.py add <pid> --type <type> [--name 显示名] [--api-key KEY | --api-key -]
  python cli.py set <pid> --api-key KEY | -
  python cli.py rm <pid>
  python cli.py list
  python cli.py test <pid>

安全：--api-key - 表示从 stdin 读（不暴露在命令行参数/进程列表）。
写操作后会在项目根留 .config_changed 标记，运行中的软件 3 秒内自动重载。
"""
import argparse
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.chdir(BASE_DIR)

from app import settings  # noqa: E402
from app.providers import PROVIDERS, TEMPLATE_PROVIDERS  # noqa: E402

CONFIG_MARKER = os.path.join(BASE_DIR, ".config_changed")

VALID_TYPES = set(PROVIDERS.keys())


def _read_key(arg, name="API Key"):
    """从参数或 stdin 读密钥。arg == '-' 时从 stdin 读一行。"""
    if arg == "-":
        key = sys.stdin.read().strip()
        if not key:
            print(f"错误：stdin 未提供 {name}")
            sys.exit(1)
        return key
    if not arg:
        print(f"错误：缺少 --api-key（用 --api-key - 从 stdin 读）")
        sys.exit(1)
    return arg


def _mark_changed():
    try:
        with open(CONFIG_MARKER, "w", encoding="utf-8") as f:
            f.write(str(__import__("time").time()))
    except OSError as e:
        print(f"警告：写入变更标记失败（软件热重载将不生效）: {e}")


def _providers(cfg):
    return dict(cfg.get("providers") or {})


def cmd_add(args):
    if args.type not in VALID_TYPES:
        print(f"错误：未知类型 '{args.type}'。可用类型：{', '.join(sorted(VALID_TYPES))}")
        sys.exit(1)
    key = _read_key(args.api_key)
    cfg = settings.load()
    provs = _providers(cfg)
    if args.pid in provs:
        print(f"错误：供应商 '{args.pid}' 已存在（用 set 更新密钥，或 rm 后重加）")
        sys.exit(1)
    provs[args.pid] = {
        "enabled": True,
        "name": args.name or args.pid,
        "type": args.type,
        "config": {"api_key": key},
    }
    settings.save({"providers": provs})
    _mark_changed()
    print(f"已添加供应商 '{args.pid}'（type={args.type}）——运行中的软件将自动重载")


def cmd_set(args):
    key = _read_key(args.api_key)
    cfg = settings.load()
    provs = _providers(cfg)
    if args.pid not in provs:
        print(f"错误：供应商 '{args.pid}' 不存在（用 add 添加）")
        sys.exit(1)
    provs[args.pid].setdefault("config", {})["api_key"] = key
    settings.save({"providers": provs})
    _mark_changed()
    print(f"已更新 '{args.pid}' 的 API Key——运行中的软件将自动重载")


def cmd_rm(args):
    cfg = settings.load()
    provs = _providers(cfg)
    if args.pid not in provs:
        print(f"错误：供应商 '{args.pid}' 不存在")
        sys.exit(1)
    del provs[args.pid]
    settings.save({"providers": provs})
    _mark_changed()
    print(f"已删除供应商 '{args.pid}'——运行中的软件将自动重载")


def cmd_list(_args):
    cfg = settings.load()
    provs = _providers(cfg)
    if not provs:
        print("（暂无供应商）")
        return
    print(f"{'PID':<16} {'类型':<14} {'启用':<5} 名称")
    print("-" * 60)
    for pid, p in provs.items():
        print(f"{pid:<16} {str(p.get('type','')):<14} {str(p.get('enabled', True)):<5} {p.get('name','')}")
    print(f"\n共 {len(provs)} 个供应商（密钥已加密存储）")


def cmd_test(args):
    cfg = settings.load()
    provs = _providers(cfg)
    if args.pid not in provs:
        print(f"错误：供应商 '{args.pid}' 不存在")
        sys.exit(1)
    pcfg = provs[args.pid]
    ptype = pcfg.get("type") or args.pid
    cls = PROVIDERS.get(ptype)
    if cls is None:
        print(f"错误：类型 '{ptype}' 无实现")
        sys.exit(1)
    try:
        prov = cls(pcfg.get("config") or {})
        res = prov.verify()
        ok = bool(res.get("ok"))
        print(("连接成功" if ok else "连接失败") + " · " + str(res.get("message", "")))
        sys.exit(0 if ok else 1)
    except Exception as e:
        print(f"测试异常: {type(e).__name__}: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(prog="ocgo-cli", description="OC-GO Dashboard 供应商配置 CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="添加供应商")
    p_add.add_argument("pid", help="供应商实例 ID（如 kimi-main）")
    p_add.add_argument("--type", required=True, help="类型（deepseek/kimi/siliconflow/...）")
    p_add.add_argument("--name", help="显示名（默认=pid）")
    p_add.add_argument("--api-key", default=None, help="API Key（- 表示从 stdin 读）")
    p_add.set_defaults(fn=cmd_add)

    p_set = sub.add_parser("set", help="更新供应商 API Key")
    p_set.add_argument("pid")
    p_set.add_argument("--api-key", default=None, help="API Key（- 表示从 stdin 读）")
    p_set.set_defaults(fn=cmd_set)

    p_rm = sub.add_parser("rm", help="删除供应商")
    p_rm.add_argument("pid")
    p_rm.set_defaults(fn=cmd_rm)

    p_list = sub.add_parser("list", help="列出供应商（不含密钥）")
    p_list.set_defaults(fn=cmd_list)

    p_test = sub.add_parser("test", help="测试供应商连接")
    p_test.add_argument("pid")
    p_test.set_defaults(fn=cmd_test)

    args = parser.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
