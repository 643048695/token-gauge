# -*- coding: utf-8 -*-
"""开机自启（可选）：HKCU Run 键，无需管理员权限。

- 开发模式：pythonw.exe + main.py 绝对路径
- 打包模式：exe 自身路径
"""
import os
import sys
import winreg

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "TokenGauge"


def _command():
    """返回写入 Run 键的启动命令。"""
    if getattr(sys, "frozen", False):
        return '"%s"' % sys.executable
    main_py = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main.py")
    return '"%s" "%s"' % (sys.executable, main_py)


def set_enabled(enabled):
    """启用/禁用开机自启。"""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE)
    except OSError:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY)
    try:
        if enabled:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _command())
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
    finally:
        winreg.CloseKey(key)


def is_enabled():
    """查询当前是否已设置开机自启。"""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY)
    except OSError:
        return False
    try:
        try:
            winreg.QueryValueEx(key, APP_NAME)
            return True
        except FileNotFoundError:
            return False
    finally:
        winreg.CloseKey(key)
