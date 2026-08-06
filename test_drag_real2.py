# -*- coding: utf-8 -*-
"""验证 SendInput 点击窗口右下角时命中什么元素"""
import ctypes
import ctypes.wintypes
import json
import os
import sys
import threading
import time

BASE = r"C:\Users\A6430\Desktop\oc-go-dashboard"
sys.path.insert(0, BASE)
os.chdir(BASE)

RESULT = os.path.join(BASE, "test_drag_real2_result.txt")

user32 = ctypes.windll.user32


def log(msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    with open(RESULT, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line, flush=True)


with open(RESULT, "w", encoding="utf-8") as f:
    f.write("=== 右下角命中验证 %s ===\n" % time.strftime("%Y-%m-%d %H:%M:%S"))

import webview  # noqa: E402
from main import DashboardApp  # noqa: E402

CFG = json.load(open("config.json", encoding="utf-8"))
app = DashboardApp(CFG)


def rect_of(hwnd):
    r = ctypes.wintypes.RECT()
    user32.GetWindowRect(ctypes.c_void_p(hwnd), ctypes.byref(r))
    return (r.left, r.top, r.right - r.left, r.bottom - r.top)


def test_loop():
    for _ in range(150):
        if app._mini_hwnd:
            break
        time.sleep(0.2)
    time.sleep(1.2)

    hwnd = app._mini_hwnd
    x0, y0, w, h = rect_of(hwnd)
    log(f"窗口: ({x0},{y0}) {w}x{h}")

    # 用 evaluate 读 resizeHandle 的屏幕坐标（页面 rect + 窗口位置）
    js = """JSON.stringify((function(){
      var el = document.getElementById('resizeHandle');
      if(!el) return 'no-el';
      var r = el.getBoundingClientRect();
      return {l:r.left, t:r.top, w:r.width, h:r.height};
    })())"""
    r = app.mini_window.evaluate_js(js)
    log("resizeHandle 页面坐标: " + str(r))
    data = json.loads(r)
    # 窗口物理 vs 页面逻辑：页面坐标是逻辑（CSS），屏幕物理 = 窗口物理 + 页面逻辑*scale
    sx = x0 + int(data["l"] * 1.25) + 7
    sy = y0 + int(data["t"] * 1.25) + 7
    log(f"换算屏幕坐标: ({sx},{sy})")

    # 真实点击那个位置（down 不动 up），看是否触发 drag_start
    user32.SetCursorPos(sx, sy)
    time.sleep(0.15)
    user32.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.25)
    user32.mouse_event(0x0004, 0, 0, 0, 0)
    time.sleep(0.5)
    log("点击完成（看日志是否 drag_start kind=resize）")
    log("测试完成")


threading.Thread(target=test_loop, daemon=True).start()
app.run()
