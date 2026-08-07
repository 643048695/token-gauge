# -*- coding: utf-8 -*-
"""开屏引导 v2 专项 GUI 回归：
- 五步引导结构（5 step / 5 dots / 按钮齐全）
- 下一步 ×4 → 开始使用（写 onboarded + 进主面板）
- 跳过指引（本次，不写 onboarded）
- 不再显示（永久，写 onboarded）
- paper 默认主题（无荧光绿：body 背景应为纸面系）
结果写 test_onboarding_v2_result.txt
"""
import json
import os
import sys
import threading
import time

BASE = r"C:\Users\A6430\Desktop\oc-go-dashboard"
sys.path.insert(0, BASE)
os.chdir(BASE)

RESULT = os.path.join(BASE, "test_onboarding_v2_result.txt")


def log(msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    with open(RESULT, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line, flush=True)


with open(RESULT, "w", encoding="utf-8") as f:
    f.write("=== 开屏引导 v2 回归 %s ===\n" % time.strftime("%Y-%m-%d %H:%M:%S"))

import webview  # noqa: E402

# 用独立 storage_path 避开默认目录被锁（残留 WebView2 进程可能占用 %APPDATA%\pywebview）
TEST_STORAGE = os.path.join(BASE, ".wv2test-onb")
_orig_start = webview.start


def _patched_start(*a, **kw):
    kw.setdefault("storage_path", TEST_STORAGE)
    kw.setdefault("private_mode", False)
    return _orig_start(*a, **kw)


webview.start = _patched_start

from main import DashboardApp  # noqa: E402

CFG = json.load(open("config.json", encoding="utf-8"))
ONB0 = bool((CFG.get("ui") or {}).get("onboarded"))
app = DashboardApp(CFG)


def ev(js, tag):
    try:
        return app.main_window.evaluate_js(js)
    except Exception as e:
        log("%s 异常: %s" % (tag, str(e)[:100]))
        return None


def nav_guide(tag):
    """主窗口导航到引导页（?guide=1 强制显示）"""
    ev("window.location.href='index.html?guide=1'; 'ok'", tag)
    time.sleep(6)


def on_main_panel():
    r = ev(
        "JSON.stringify({alive:true, hasLangBtn:!!document.querySelector('.lang-switch'),"
        "hasNav:document.body.innerText.indexOf('仪表盘')>=0||document.body.innerText.indexOf('Dashboard')>=0})",
        "panel-check")
    return r


def ob():
    try:
        s = app.kernel.get_settings()
        return bool((s.get("ui") or {}).get("onboarded"))
    except Exception as e:
        log("读 onboarded 异常: %s" % str(e)[:80])
        return None


def test_loop():
    for _ in range(300):
        if app._mini_hwnd:
            break
        time.sleep(0.2)
    time.sleep(2)
    log("迷你窗就绪，onboarded0=%s" % ONB0)

    # ---------- 1) 结构断言 ----------
    nav_guide("1-nav")
    r1 = ev(
        "JSON.stringify((function(){"
        "var steps=document.querySelectorAll('.step');"
        "var dots=document.querySelectorAll('#dots i');"
        "var hidden=[];"
        "for(var i=0;i<steps.length;i++){if(steps[i].classList.contains('hidden'))hidden.push(i+1);}"
        "var hasNever=!!document.getElementById('btnNever');"
        "var hasSkipOnce=!!document.getElementById('btnSkipOnce');"
        "var hasNext=!!document.getElementById('btnNext');"
        "var hasStart=!!document.getElementById('btnStart');"
        "var hasSkip=!!document.getElementById('btnSkip');"
        "var style=document.body.getAttribute('data-style');"
        "var bg=getComputedStyle(document.body).backgroundColor;"
        "return {steps:steps.length, dots:dots.length, hiddenSteps:hidden,"
        "hasNever:hasNever, hasSkipOnce:hasSkipOnce, hasNext:hasNext, hasStart:hasStart,"
        "hasSkip:hasSkip, style:style, bg:bg,"
        "hasStep1:!!document.getElementById('step1'), hasStep5:!!document.getElementById('step5')};})())",
        "1-struct")
    log("1) 五步结构: " + str(r1))

    # ---------- 2) 下一步 ×4 → step5 → 开始使用 ----------
    r2 = ev(
        "JSON.stringify((function(){"
        "var next=document.getElementById('btnNext');"
        "for(var i=0;i<4;i++){if(next)next.click();}"
        "var s5=document.getElementById('step5');"
        "return {step5Shown:!!s5&&!s5.classList.contains('hidden'),"
        "nextHidden:!!next&&(next.style.display==='none'),"
        "startShown:!!document.getElementById('btnStart')&&(document.getElementById('btnStart').style.display!=='none'),"
        "dotsOn:document.querySelectorAll('#dots i.on').length,"
        "prevShown:document.getElementById('btnPrev').className.indexOf('ghost-invisible')<0};})())", "2")
    log("2) 五步到头: " + str(r2))

    r2b = ev(
        "JSON.stringify((function(){var s=document.getElementById('btnStart');"
        "if(!s) return {noStart:true}; s.click(); return {start:true};})())", "2b")
    log("2b) 点开始使用: " + str(r2b))
    time.sleep(8)
    log("2c) 回主面板: " + str(on_main_panel()))
    log("2d) onboarded 应为 True: %s" % ob())

    # ---------- 3) 跳过指引：本次跳过，不写 onboarded ----------
    app.kernel.save_settings({"ui": {"onboarded": False}})  # 先复位
    log("3) 复位 onboarded=False: %s" % ob())
    nav_guide("3-nav")
    ev("(function(){var b=document.getElementById('btnSkipOnce');if(b)b.click();})()", "3-click")
    time.sleep(8)
    log("3b) 回主面板: " + str(on_main_panel()))
    log("3c) onboarded 仍为 False（未写）: %s" % ob())

    # ---------- 4) 不再显示：永久跳过，写 onboarded ----------
    nav_guide("4-nav")
    ev("(function(){var b=document.getElementById('btnNever');if(b)b.click();})()", "4-click")
    time.sleep(8)
    log("4b) 回主面板: " + str(on_main_panel()))
    log("4c) onboarded 应为 True: %s" % ob())

    # ---------- 5) 右上角跳过 = 本次跳过 ----------
    app.kernel.save_settings({"ui": {"onboarded": False}})
    nav_guide("5-nav")
    ev("(function(){var b=document.getElementById('btnSkip');if(b)b.click();})()", "5-click")
    time.sleep(8)
    log("5b) 回主面板: " + str(on_main_panel()))
    log("5c) onboarded 仍为 False: %s" % ob())

    # ---------- 6) P3 测试连接模拟 ----------
    app.kernel.save_settings({"ui": {"onboarded": False}})
    nav_guide("6-nav")
    ev("(function(){var b=document.getElementById('btnTestMock');if(b)b.click();})()", "6-click")
    time.sleep(2)
    r6 = ev(
        "JSON.stringify({res:document.getElementById('testRes').textContent,"
        "dot:document.getElementById('testDot').className})", "6-res")
    log("6) 测试连接模拟: " + str(r6))

    # ---------- 恢复 ----------
    app.kernel.save_settings({"ui": {"onboarded": ONB0}})
    log("恢复 onboarded=%s 完成" % ONB0)
    log("引导 v2 回归完成")


threading.Thread(target=test_loop, daemon=True).start()
app.run()
