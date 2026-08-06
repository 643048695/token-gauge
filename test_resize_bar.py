# -*- coding: utf-8 -*-
"""测试 resize_mini_main（主窗口滑条 API）"""
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

RESULT = os.path.join(BASE, "test_resize_bar_result.txt")

user32 = ctypes.windll.user32


def log(msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    with open(RESULT, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line, flush=True)


with open(RESULT, "w", encoding="utf-8") as f:
    f.write("=== resize_mini_main 测试 %s ===\n" % time.strftime("%Y-%m-%d %H:%M:%S"))

import webview  # noqa: E402
from main import DashboardApp  # noqa: E402

CFG = json.load(open("config.json", encoding="utf-8"))
app = DashboardApp(CFG)


def mini_wh():
    hwnd = app._mini_hwnd
    if not hwnd:
        return None
    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(ctypes.c_void_p(hwnd), ctypes.byref(rect))
    return (rect.right - rect.left, rect.bottom - rect.top)


def test_loop():
    for _ in range(150):
        if app._mini_hwnd:
            break
        time.sleep(0.2)
    time.sleep(1.2)

    w0, h0 = mini_wh() or (0, 0)
    log(f"初始: {w0}x{h0}")

    # 主面板调 resize_mini_main（滑条 input 事件的调用方式）
    js = """JSON.stringify((function(){
      var api = window.pywebview && window.pywebview.api;
      if(!api || !api.resize_mini_main) return 'no-api';
      return api.resize_mini_main(400);
    })())"""
    try:
        r = app.main_window.evaluate_js(js)
        log("resize_mini_main(400) 返回: " + str(r))
    except Exception as e:
        log("evaluate 异常: %s" % e)
    time.sleep(0.8)
    w1, h1 = mini_wh()
    log(f"调后: {w1}x{h1} (期望宽~500=400x1.25)")

    # 再调 300
    app.main_window.evaluate_js(
        "window.pywebview.api.resize_mini_main(300)")
    time.sleep(0.8)
    w2, h2 = mini_wh()
    log(f"调 300 后: {w2}x{h2} (期望宽~375)")
    log("测试完成")


threading.Thread(target=test_loop, daemon=True).start()
app.run()
