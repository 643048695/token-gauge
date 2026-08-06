# -*- coding: utf-8 -*-
"""查 opencode 卡柱状图"""
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
    f.write("=== opencode 卡图表诊断 %s ===\n" % time.strftime("%Y-%m-%d %H:%M:%S"))

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
    try:
        app.kernel.refresh_now()
    except Exception as e:
        log("refresh_now 异常: %s" % e)
    time.sleep(3)
    try:
        app.main_window.evaluate_js("window.location.reload()")
    except Exception:
        pass
    time.sleep(6)
    js = """JSON.stringify((function(){
      var oc = Array.prototype.slice.call(document.querySelectorAll('.pcard')).find(function(c){
        return (c.querySelector('.pcard-name')||{}).textContent === 'OpenCode Go';
      });
      if(!oc) return {noCard: true, cards: document.querySelectorAll('.pcard').length};
      return {
        sparkCharts: oc.querySelectorAll('.spark-chart').length,
        sparkTitle: (oc.querySelector('.spark-title')||{}).textContent || null,
        err: (oc.querySelector('.chip.danger')||{}).textContent || null,
        metaCells: Array.prototype.slice.call(oc.querySelectorAll('.meta-cell .meta-k')).map(function(x){return x.textContent;})
      };
    })())"""
    try:
        r = app.main_window.evaluate_js(js)
        log("opencode 卡: " + str(r))
    except Exception as e:
        log("evaluate 异常: %s" % e)
    log("诊断完成")


threading.Thread(target=test_loop, daemon=True).start()
app.run()
