# -*- coding: utf-8 -*-
"""迷你窗尺寸切换自动化测试 v2：结果写入文件，不受终端输出影响"""
import ctypes
import json
import os
import sys
import threading
import time

BASE = r"C:\Users\A6430\Desktop\oc-go-dashboard"
sys.path.insert(0, BASE)
os.chdir(BASE)

RESULT_FILE = os.path.join(BASE, "test_result.txt")


def log(msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    with open(RESULT_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line, flush=True)


with open(RESULT_FILE, "w", encoding="utf-8") as f:
    f.write("=== mini resize 自动化测试 %s ===\n" % time.strftime("%Y-%m-%d %H:%M:%S"))

import webview  # noqa: E402
from main import DashboardApp  # noqa: E402

CFG = json.load(open("config.json", encoding="utf-8"))
app = DashboardApp(CFG)


def get_mini_state():
    w = app.mini_window
    if w is None:
        return ("no-window", 0, 0, 0, 0)
    hwnd = app._window_hwnd(w)
    if not hwnd:
        return ("no-hwnd", 0, 0, 0, 0)
    user32 = ctypes.windll.user32
    vis = user32.IsWindowVisible(ctypes.c_void_p(hwnd))
    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(ctypes.c_void_p(hwnd), ctypes.byref(rect))
    return (int(vis), rect.left, rect.top, rect.right, rect.bottom)


def screen_size():
    # 物理分辨率：GetMonitorInfo 返回物理像素（GetSystemMetrics 在 DPI unaware 进程返回逻辑值会误判）
    try:
        hwnd = app._window_hwnd(app.mini_window)
        mw = app._monitor_work(hwnd)
        if mw:
            return mw[2], mw[3]
    except Exception:
        pass
    user32 = ctypes.windll.user32
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


def test_loop():
    time.sleep(10)
    sw, sh = screen_size()
    log(f"屏幕 {sw}x{sh}")
    # ===== 坐标约定实测：move 已知值，读实际位置反推换算 =====
    try:
        w = app.mini_window
        if w is not None:
            w.move(100, 100)
            time.sleep(0.8)
            st = get_mini_state()
            log(f"坐标实测: move(100,100) -> rect=({st[1]},{st[2]},{st[3]},{st[4]})  => 换算系数={st[1] / 100.0 if st[1] else 0:.2f}")
            # 恢复右下角
            cfg0 = json.load(open("config.json", encoding="utf-8"))
            app.apply_mini_geometry(cfg0)
            time.sleep(0.8)
    except Exception as e:
        log(f"坐标实测异常: {e}")
    sizes = [(240, 140), (300, 170), (380, 210), (300, 170), (240, 140)]
    all_pass = True
    for i, (w, h) in enumerate(sizes):
        cfg2 = json.load(open("config.json", encoding="utf-8"))
        cfg2["window"]["mini_width"] = w
        cfg2["window"]["mini_height"] = h
        try:
            app.apply_mini_geometry(cfg2)
        except Exception as e:
            log(f"TEST {i} {w}x{h} 调用异常: {e}")
            all_pass = False
            continue
        time.sleep(1.2)
        st = get_mini_state()
        vis, l, t, r, b = st
        # 屏内判定：窗口 rect 与所在显示器物理工作区同坐标系比较
        hwnd = app._window_hwnd(app.mini_window)
        mw = app._monitor_work(hwnd) if hwnd else None
        in_screen = False
        if mw:
            wl, wt, ww, wh = mw
            in_screen = bool(vis) and wl <= l and wt <= t and r <= wl + ww and b <= wt + wh
        else:
            in_screen = bool(vis)
        ok = in_screen and (r - l) > 100 and (b - t) > 80
        log(f"TEST {i} {w}x{h}: visible={vis} rect=({l},{t},{r},{b}) 实际={r-l}x{b-t} work={mw} 屏内={in_screen} {'PASS' if ok else 'FAIL'}")
        if not ok:
            all_pass = False
    cfg2 = json.load(open("config.json", encoding="utf-8"))
    cfg2["window"]["mini_width"] = 300
    cfg2["window"]["mini_height"] = 170
    json.dump(cfg2, open("config.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    app.apply_mini_geometry(cfg2)
    log(f"总体: {'全部 PASS' if all_pass else '存在 FAIL'}")
    log("测试完成")


threading.Thread(target=test_loop, daemon=True).start()
app.run()  # 创建窗口 + 阻塞（webview.start 必须在主线程）
