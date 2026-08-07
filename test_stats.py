# -*- coding: utf-8 -*-
"""统计重构验证 v3：底部区 + 单位换算（DOM 层验证 bal-amount 变化）"""
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


def ev(js):
    try:
        return app.main_window.evaluate_js(js)
    except Exception as e:
        return "EXC:" + str(e)[:80]


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
    time.sleep(10)
    lines = []
    lines.append("1) " + str(ev(
        "JSON.stringify({hasStats:!!document.querySelector('.stats-section'),"
        "hasBar:!!document.querySelector('.stats-bar'),"
        "hasPie:document.querySelectorAll('.stats-card svg').length>=1,"
        "cardSpark:document.querySelectorAll('.pcard .spark-chart').length,"
        "cardCount:document.querySelectorAll('.pcard').length,"
        "appApi:typeof (window.__app||{}).moneyUnit})"))
    lines.append("2) " + str(ev(
        "(function(){var a=window.__app;if(!a)return 'noApp';"
        "var m={models:[{output:2}]};"
        "var r={auto:a.moneyUnit(4.46,'CNY',m)};"
        "a.state.settings.display=a.state.settings.display||{};"
        "a.state.settings.display.unit='tokens';"
        "r.tokens=a.moneyUnit(4.46,'CNY',m);"
        "a.state.settings.display.unit='usd';"
        "r.usd=a.moneyUnit(4.46,'CNY',m);"
        "a.state.settings.display.unit='cny';"
        "r.cny=a.moneyUnit(1.5,'USD',m);"
        "a.state.settings.display.unit='auto';"
        "a.renderAll();"
        "return JSON.stringify(r);})()"))
    # 3) 排序（反序）
    lines.append("3) " + str(ev(
        "(function(){var a=window.__app;if(!a)return 'noApp';"
        "var pids=Object.keys(a.state.settings.providers||{});"
        "if(pids.length<2)return 'few:'+pids.length;"
        "a.state.settings.order={providers:pids.slice().reverse()};"
        "a.renderAll();"
        "var cards=document.querySelectorAll('.pcard');"
        "var ord=[];for(var i=0;i<cards.length;i++){ord.push(cards[i].getAttribute('data-pid'));}"
        "a.state.settings.order=null;a.renderAll();"
        "return JSON.stringify({order:ord});})()"))
    with open(RESULT, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines), flush=True)


threading.Thread(target=test_loop, daemon=True).start()
app.run()
