# -*- coding: utf-8 -*-
"""真实环境拖动测试 v2：hwnd 用 FindWindowW 按标题获取（绕开 pythonnet 跨线程）"""
import ctypes
import ctypes.wintypes
import json
import os
import sys
import threading
import time

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
os.chdir(BASE)

RESULT = os.path.join(BASE, "test_drag_result.txt")


def log(msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    with open(RESULT, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line, flush=True)


with open(RESULT, "w", encoding="utf-8") as f:
    f.write("=== 真实拖动测试 v2 %s ===\n" % time.strftime("%Y-%m-%d %H:%M:%S"))

import webview  # noqa: E402
from main import DashboardApp  # noqa: E402

CFG = json.load(open("config.json", encoding="utf-8"))
app = DashboardApp(CFG)

WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_MOUSEMOVE = 0x0200
MK_LBUTTON = 0x0001
user32 = ctypes.windll.user32
user32.FindWindowW.restype = ctypes.c_void_p


def find_mini_hwnd():
    h = user32.FindWindowW(None, "OC-GO Mini")
    return int(h) if h else None


def post_mouse(hwnd, msg, x, y, wparam=0):
    lparam = ((y & 0xFFFF) << 16) | (x & 0xFFFF)
    user32.PostMessageW(ctypes.c_void_p(hwnd), msg, wparam, lparam)


def drag(hwnd, x1, y1, x2, y2):
    post_mouse(hwnd, WM_LBUTTONDOWN, x1, y1, MK_LBUTTON)
    time.sleep(0.05)
    steps = 6
    for i in range(1, steps + 1):
        x = x1 + (x2 - x1) * i // steps
        y = y1 + (y2 - y1) * i // steps
        post_mouse(hwnd, WM_MOUSEMOVE, x, y, MK_LBUTTON)
        time.sleep(0.03)
    time.sleep(0.05)
    post_mouse(hwnd, WM_LBUTTONUP, x2, y2, 0)


def click(hwnd, x, y):
    post_mouse(hwnd, WM_LBUTTONDOWN, x, y, MK_LBUTTON)
    time.sleep(0.05)
    post_mouse(hwnd, WM_LBUTTONUP, x, y, 0)


def mini_state():
    if app.mini_window is None:
        return "no-window"
    try:
        js = "JSON.stringify({cls:document.getElementById('hud').className, dToday:!!document.getElementById('dToday')})"
        return app.mini_window.evaluate_js(js)
    except Exception as e:
        return "eval-err:%s" % e


def test_loop():
    time.sleep(12)
    hwnd = None
    for _ in range(150):  # 最多等 30 秒 loaded 完成
        hwnd = app._mini_hwnd
        if hwnd:
            break
        time.sleep(0.2)
    log(f"迷你窗 hwnd={hwnd} (app._mini_hwnd)")
    if not hwnd:
        return
    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(ctypes.c_void_p(hwnd), ctypes.byref(rect))
    cw = rect.right - rect.left
    ch = rect.bottom - rect.top
    log(f"窗口 {cw}x{ch}")

    log(f"初始: {mini_state()}")

    # 测试 1：无位移点击（中部）→ 应展开
    click(hwnd, cw // 2, int(ch * 0.5))
    time.sleep(0.4)
    log(f"点击后: {mini_state()}")

    # 收起
    click(hwnd, cw // 2, int(ch * 0.5))
    time.sleep(0.4)
    log(f"再点击后: {mini_state()}")

    # 测试 2：顶部拖拽区拖动
    log("拖动（顶部）...")
    drag(hwnd, cw - 80, 10, cw - 20, 30)
    time.sleep(0.5)
    log(f"顶部拖动后: {mini_state()}")

    # 测试 3：中部拖动（非拖拽区，模拟鼠标滑动）
    log("拖动（中部）...")
    drag(hwnd, cw // 2, int(ch * 0.5), cw // 2 + 50, int(ch * 0.5) + 30)
    time.sleep(0.5)
    log(f"中部拖动后: {mini_state()}")

    log("测试完成")


threading.Thread(target=test_loop, daemon=True).start()
app.run()
