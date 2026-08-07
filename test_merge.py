# -*- coding: utf-8 -*-
"""合并整体回归 v3：主面板 → 重看引导 → 完成引导回主面板（验证导航修复）→ 双语"""
import json
import os
import sys
import threading
import time

BASE = r"C:\Users\A6430\Desktop\oc-go-dashboard"
sys.path.insert(0, BASE)
os.chdir(BASE)

RESULT = os.path.join(BASE, "test_merge_result.txt")


def log(msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    with open(RESULT, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line, flush=True)


with open(RESULT, "w", encoding="utf-8") as f:
    f.write("=== 合并整体回归 v3 %s ===\n" % time.strftime("%Y-%m-%d %H:%M:%S"))

import webview  # noqa: E402
from main import DashboardApp  # noqa: E402

CFG = json.load(open("config.json", encoding="utf-8"))
app = DashboardApp(CFG)  # config 里 ui.onboarded=True（C 已设置）→ 直进主面板


def ev(js, tag):
    try:
        return app.main_window.evaluate_js(js)
    except Exception as e:
        log("%s 异常: %s" % (tag, str(e)[:100]))
        return None


def test_loop():
    for _ in range(300):
        if app._mini_hwnd:
            break
        time.sleep(0.2)
    time.sleep(2)
    log("迷你窗就绪，reload 主窗口")
    try:
        app.main_window.evaluate_js("window.location.reload()")
    except Exception:
        pass
    time.sleep(8)

    # 1) 主面板（onboarded=true 直进）
    r1 = ev(
        "JSON.stringify({hasLangBtn:!!document.querySelector('.lang-switch'),"
        "langBtns:document.querySelectorAll('.lang-btn').length,"
        "hasNav:document.body.innerText.indexOf('仪表盘')>=0||document.body.innerText.indexOf('Dashboard')>=0})",
        "1)")
    log("1) 主面板: " + str(r1))

    # 2) 点「重新查看开屏引导」→ 应跳引导页（location 导航，不挂窗口）
    r2 = ev(
        "JSON.stringify((function(){var b=document.getElementById('btnReplayGuide');"
        "if(!b) return {noBtn:true};"
        "b.click();return {clicked:true};})())", "2)")
    log("2) 触发重看引导: " + str(r2))
    time.sleep(6)
    r2b = ev(
        "JSON.stringify({hasTopbar:!!document.querySelector('#topbar'),"
        "hasSteps:!!document.querySelector('.steps')||!!document.querySelector('.step'),"
        "text:document.body.innerText.slice(0,60)})", "2b)")
    log("2b) 引导页: " + str(r2b))

    # 3) 完整引导流程：下一步 ×4（五步引导）→ 开始使用 → 主面板
    r3 = ev(
        "JSON.stringify((function(){"
        "var next=document.getElementById('btnNext'); var start=document.getElementById('btnStart');"
        "if(!next||!start) return {noBtns:!!next+','+!!start};"
        "for(var i=0;i<4;i++){next.click();}"
        "return {next:true, clicks:4};})())", "3)")
    log("3) 下一步: " + str(r3))
    time.sleep(2)
    r3b = ev(
        "JSON.stringify((function(){"
        "var start=document.getElementById('btnStart');"
        "if(!start) return {noStart:true}; start.click(); return {start:true};})())", "3b)")
    log("3b) 开始使用: " + str(r3b))
    time.sleep(8)
    r3c = ev(
        "JSON.stringify({alive:true, hasLangBtn:!!document.querySelector('.lang-switch'),"
        "hasNav:document.body.innerText.indexOf('仪表盘')>=0||document.body.innerText.indexOf('Dashboard')>=0})",
        "3c)")
    log("3c) 回主面板: " + str(r3c))

    # 4) 切英文
    r4 = ev(
        "JSON.stringify((function(){"
        "var b=document.querySelectorAll('.lang-btn');var en=null;"
        "b.forEach(function(x){var t=x.textContent.trim().toUpperCase();"
        "if(t.indexOf('EN')>=0||x.getAttribute('data-lang')==='en')en=x;});"
        "if(!en) return {noEn:true, texts:Array.from(b).map(function(x){return x.textContent.trim();})};"
        "en.click();return {clicked:true};})())", "4)")
    log("4) 切英文: " + str(r4))
    time.sleep(4)
    r5 = ev(
        "JSON.stringify({hasEN:document.body.innerText.indexOf('Refresh')>=0||"
        "document.body.innerText.indexOf('Balance')>=0||"
        "document.body.innerText.indexOf('Theme')>=0,"
        "t:document.body.innerText.slice(0,100)})", "5)")
    log("5) 英文验证: " + str(r5))

    # 6) 切回中文 + 迷你窗语言跟随
    ev("(function(){var b=document.querySelectorAll('.lang-btn');var zh=null;"
       "b.forEach(function(x){var t=x.textContent.trim();if(t.indexOf('中')>=0||x.getAttribute('data-lang')==='zh')zh=x;});"
       "if(zh)zh.click();})()", "6)")
    time.sleep(3)
    try:
        r7 = app.mini_window.evaluate_js(
            "JSON.stringify({hasMini:true, langBtns:document.querySelectorAll('.lang-btn').length,"
            "text:document.body.innerText.slice(0,50)})")
        log("7) 迷你窗: " + str(r7))
    except Exception as e:
        log("7) 异常: %s" % str(e)[:80])

    log("整体回归完成")


threading.Thread(target=test_loop, daemon=True).start()
app.run()
