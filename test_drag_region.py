# -*- coding: utf-8 -*-
"""拖拽链路实测 v2：evaluate_js 在页面内派发真实语义事件，验证 JS→move_mini→SetWindowPos"""
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

RESULT = os.path.join(BASE, "test_drag_region_result.txt")


def log(msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    with open(RESULT, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line, flush=True)


with open(RESULT, "w", encoding="utf-8") as f:
    f.write("=== 拖拽链路实测 v2（evaluate_js 派发） %s ===\n" % time.strftime("%Y-%m-%d %H:%M:%S"))

import webview  # noqa: E402
from main import DashboardApp  # noqa: E402

CFG = json.load(open("config.json", encoding="utf-8"))
app = DashboardApp(CFG)
user32 = ctypes.windll.user32


def mini_rect():
    hwnd = app._mini_hwnd
    if not hwnd:
        return None
    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(ctypes.c_void_p(hwnd), ctypes.byref(rect))
    return (rect.left, rect.top, rect.right, rect.bottom)


def eval_js(js):
    try:
        return app.mini_window.evaluate_js(js)
    except Exception as e:
        return "eval-err:%s" % e


def test_loop():
    for _ in range(150):
        if app._mini_hwnd:
            break
        time.sleep(0.2)
    time.sleep(1)
    r0 = mini_rect()
    log(f"初始 rect: {r0}")
    if not r0:
        log("窗口不可用")
        return
    # 页面内派发：drag-top mousedown（screenX/Y）→ window mousemove → mouseup
    # 模拟：按下 (1000,500)，移动 +60,+40，松开
    js = """(function(){
      var drag = document.querySelector('.drag-top');
      var out = {dragFound: !!drag};
      drag.dispatchEvent(new MouseEvent('mousedown', {screenX:1000, screenY:500, clientX:30, clientY:25, bubbles:true, cancelable:true}));
      window.dispatchEvent(new MouseEvent('mousemove', {screenX:1060, screenY:540, bubbles:true}));
      window.dispatchEvent(new MouseEvent('mouseup', {screenX:1060, screenY:540, bubbles:true}));
      return JSON.stringify(out);
    })()"""
    log("页面派发拖拽事件: " + str(eval_js(js)))
    time.sleep(0.8)
    r1 = mini_rect()
    log(f"拖动后 rect: {r1}")
    if r1 and (r1[0] != r0[0] or r1[1] != r0[1]):
        log(f"PASS: 窗口移动了 (Δ=({r1[0]-r0[0]},{r1[1]-r0[1]}))")
    else:
        log("FAIL: 窗口未移动")
    # 还原
    try:
        app.apply_mini_geometry(app.kernel.get_settings())
    except Exception:
        pass
    log("测试完成")


threading.Thread(target=test_loop, daemon=True).start()
app.run()
