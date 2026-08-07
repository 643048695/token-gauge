# -*- coding: utf-8 -*-
"""快速诊断：主窗口页面状态"""
import json
import os
import sys
import threading
import time

BASE = r"C:\Users\A6430\Desktop\oc-go-dashboard"
sys.path.insert(0, BASE)
os.chdir(BASE)
RESULT = os.path.join(BASE, "test_stats_result.txt")

import webview  # noqa: E402
from main import DashboardApp  # noqa: E402

CFG = json.load(open("config.json", encoding="utf-8"))
app = DashboardApp(CFG)


def test_loop():
    for _ in range(300):
        if app._mini_hwnd:
            break
        time.sleep(0.2)
    time.sleep(2)
    try:
        app.main_window.evaluate_js("window.location.reload()")
    except Exception:
        pass
    time.sleep(8)
    try:
        r = app.main_window.evaluate_js(
            "JSON.stringify({url: location.href,"
            "bodyLen: document.body.innerHTML.length,"
            "hasApp: !!window.__app,"
            "hasI18N: !!window.I18N,"
            "head: document.body.innerHTML.slice(0,120)})")
        with open(RESULT, "a", encoding="utf-8") as f:
            f.write("DIAG: " + str(r) + "\n")
        print("DIAG:", r)
    except Exception as e:
        with open(RESULT, "a", encoding="utf-8") as f:
            f.write("DIAG 异常: %s\n" % str(e)[:200])
        print("DIAG 异常:", str(e)[:200])


threading.Thread(target=test_loop, daemon=True).start()
app.run()
