# -*- coding: utf-8 -*-
"""诊断 mini __mini 未挂载"""
import json
import os
import sys
import threading
import time

BASE = r"C:\Users\A6430\Desktop\oc-go-dashboard"
sys.path.insert(0, BASE)
os.chdir(BASE)

RESULT = os.path.join(BASE, "test_deepseek_result.txt")


def log(msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    with open(RESULT, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line, flush=True)


with open(RESULT, "w", encoding="utf-8") as f:
    f.write("=== mini __mini 诊断 %s ===\n" % time.strftime("%Y-%m-%d %H:%M:%S"))

import webview  # noqa: E402
from main import DashboardApp  # noqa: E402

CFG = json.load(open("config.json", encoding="utf-8"))
app = DashboardApp(CFG)


def test_loop():
    for _ in range(250):
        if app._mini_hwnd:
            break
        time.sleep(0.2)
    time.sleep(2)
    js = """JSON.stringify({
      mini: typeof window.__mini,
      render: typeof render,
      scriptEnd: !!window.__scriptEnd,
      initErr: window.__initErr,
      errLog: window.__errLog || null
    })"""
    try:
        r = app.mini_window.evaluate_js(js)
        log("mini 状态: " + str(r))
    except Exception as e:
        log("evaluate 异常: %s" % e)
    log("诊断完成")


threading.Thread(target=test_loop, daemon=True).start()
app.run()
