# -*- coding: utf-8 -*-
"""DIY 功能验证：模块开关显隐 + 迷你窗供应商切换"""
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
    f.write("=== DIY 功能验证 %s ===\n" % time.strftime("%Y-%m-%d %H:%M:%S"))

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

    # 1) 默认全开
    js = """JSON.stringify((function(){
      var ds = document.querySelector('.pcard .bal-main') ? document.querySelector('.pcard .bal-main').closest('.pcard') : null;
      return {
        hasMain: !!document.querySelector('.bal-main'),
        hasGrid: !!document.querySelector('.meta-grid'),
        hasTok: !!document.querySelector('.token-est'),
        hasChart: !!document.querySelector('.spark-chart')
      };
    })())"""
    try:
        r = app.main_window.evaluate_js(js)
        log("默认模块: " + str(r))
    except Exception as e:
        log("e1 异常: %s" % e)

    # 2) 关掉 token_est + chart（用 __app 测试接口）
    js2 = """JSON.stringify((function(){
      if(!window.__app) return {noTestable:true};
      window.__app.state.settings.diy = window.__app.state.settings.diy || {};
      window.__app.state.settings.diy.modules = window.__app.state.settings.diy.modules || {};
      window.__app.state.settings.diy.modules.balance = {bal_main:true, meta_grid:true, token_est:false, chart:false};
      window.__app.renderAll();
      return {
        hasMain: !!document.querySelector('.bal-main'),
        hasGrid: !!document.querySelector('.meta-grid'),
        hasTok: !!document.querySelector('.token-est'),
        hasChart: !!document.querySelector('.spark-chart')
      };
    })())"""
    try:
        r2 = app.main_window.evaluate_js(js2)
        log("关 token/chart 后: " + str(r2))
    except Exception as e:
        log("e2 异常: %s" % e)

    # 3) 迷你窗指定 deepseek（opencode 在前，指定 deepseek 看余额）
    js3 = """JSON.stringify((function(){
      if(!window.__mini) return {noMini:true};
      window.__mini.getViewData();
      return {hasMini:true};
    })())"""
    try:
        r3 = app.mini_window.evaluate_js(js3)
        log("mini 接口: " + str(r3))
    except Exception as e:
        log("e3 异常: %s" % e)

    # 直接推一个指定 diy 的 view 给迷你窗
    js4 = """JSON.stringify((function(){
      var v = window.__mini.getViewData();
      if(!v) return {noView:true};
      v.settings = v.settings || {};
      v.settings.diy = {mini_provider: 'deepseek'};
      window.__mini.render(v);
      var g = function(id){ var el=document.getElementById(id); return el?el.textContent:'--'; };
      return {todayBig: g('todayBig'), todayMeta: g('todayMeta')};
    })())"""
    try:
        r4 = app.mini_window.evaluate_js(js4)
        log("迷你窗指定 deepseek: " + str(r4))
    except Exception as e:
        log("e4 异常: %s" % e)

    # 恢复默认（清 diy 测试污染）
    app.main_window.evaluate_js(
        "if(window.__app){ window.__app.state.settings.diy = null; window.__app.renderAll(); }")
    log("测试完成")


threading.Thread(target=test_loop, daemon=True).start()
app.run()
