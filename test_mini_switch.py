# -*- coding: utf-8 -*-
"""综合自动化测试：尺寸连切 10 次 + 开关开合，走完整 save_settings 链路 + Win32 断言"""
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

RESULT = os.path.join(BASE, "test_mini_switch_result.txt")


def log(msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    with open(RESULT, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line, flush=True)


with open(RESULT, "w", encoding="utf-8") as f:
    f.write("=== 综合测试（尺寸×10 + 开关） %s ===\n" % time.strftime("%Y-%m-%d %H:%M:%S"))

import webview  # noqa: E402
from main import DashboardApp  # noqa: E402

CFG = json.load(open("config.json", encoding="utf-8"))
app = DashboardApp(CFG)
user32 = ctypes.windll.user32


def mini_win_state():
    """返回 (visible, w, h, left, top) 或 None"""
    hwnd = app._mini_hwnd
    if not hwnd:
        return None
    try:
        vis = user32.IsWindowVisible(ctypes.c_void_p(hwnd))
        rect = ctypes.wintypes.RECT()
        user32.GetWindowRect(ctypes.c_void_p(hwnd), ctypes.byref(rect))
        return (int(vis), rect.right - rect.left, rect.bottom - rect.top,
                rect.left, rect.top)
    except Exception as e:
        return ("err", str(e))


def test_loop():
    # 等 loaded
    for _ in range(150):
        if app._mini_hwnd:
            break
        time.sleep(0.2)
    time.sleep(1)
    log(f"初始: {mini_win_state()}")

    # ========== 1) 尺寸连切 10 次 ==========
    sizes = [(240, 140), (300, 170), (380, 210)] * 3 + [(300, 170)]
    fails = 0
    for i, (w, h) in enumerate(sizes):
        try:
            r = app.api.save_settings({"window": dict(
                app.kernel.get_settings().get("window") or {},
                mini_width=w, mini_height=h)})
        except Exception as e:
            log(f"尺寸 {i} {w}x{h}: save_settings 异常 {e}")
            fails += 1
            continue
        time.sleep(0.6)
        st = mini_win_state()
        if st is None:
            log(f"尺寸 {i} {w}x{h}: 窗口丢失!")
            fails += 1
            continue
        vis, cw, ch, l, t = st
        # 物理尺寸 = 逻辑 × 1.25（允许 ±3）
        exp_w = round(w * 1.25)
        exp_h = round(h * 1.25)
        ok = vis == 1 and abs(cw - exp_w) <= 4 and abs(ch - exp_h) <= 4 and l >= 0 and t >= 0
        log(f"尺寸 {i} {w}x{h}: visible={vis} 实际={cw}x{ch} 期望~{exp_w}x{exp_h} "
            f"pos=({l},{t}) {'PASS' if ok else 'FAIL'}")
        if not ok:
            fails += 1
    log(f"尺寸测试完成: {10 - fails}/10 PASS")

    # ========== 2) 开关开合 ==========
    # 关
    try:
        app.api.save_settings({"mini_widget_enabled": False})
    except Exception as e:
        log(f"开关关 异常: {e}")
    time.sleep(0.8)
    st = mini_win_state()
    log(f"开关关: {st} (期望 visible=0)")
    # 开
    try:
        app.api.save_settings({"mini_widget_enabled": True})
    except Exception as e:
        log(f"开关开 异常: {e}")
    time.sleep(0.8)
    st = mini_win_state()
    log(f"开关开: {st} (期望 visible=1)")

    # 再切一次尺寸确认开关后尺寸仍可用
    try:
        app.api.save_settings({"window": dict(
            app.kernel.get_settings().get("window") or {},
            mini_width=380, mini_height=210)})
    except Exception:
        pass
    time.sleep(0.6)
    log(f"开关后切大尺寸: {mini_win_state()}")

    log("测试完成")


threading.Thread(target=test_loop, daemon=True).start()
app.run()
