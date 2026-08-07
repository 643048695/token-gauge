# -*- coding: utf-8 -*-
"""卡片分页验证（任务A feature/card-pager）：
1) 分页结构（.pager/.pager-page 数量=ceil(N/2)、每页<=2卡、指示点数量、active 唯一）
2) pagerGo 跳页（transform 平移 + active 切换 + pagerInfo）
3) 同页拖拽排序（合成 dragstart/drop，order 变化 + 重渲染后卡序变化）
4) DIY chart 开关仍控制底部统计区（原行为保留）
5) 结束恢复 config.json（drop 拖拽会写 order）
"""
import json
import os
import shutil
import sys
import threading
import time

BASE = r"C:\Users\A6430\Desktop\oc-go-dashboard"
sys.path.insert(0, BASE)
os.chdir(BASE)
RESULT = os.path.join(BASE, "test_pager_result.txt")

import webview  # noqa: E402
from main import DashboardApp  # noqa: E402

CFG_PATH = os.path.join(BASE, "config.json")
BAK_PATH = os.path.join(BASE, "config.json.pager.bak")
shutil.copy(CFG_PATH, BAK_PATH)

CFG = json.load(open(CFG_PATH, encoding="utf-8"))
app = DashboardApp(CFG)


def ev(js):
    try:
        return app.main_window.evaluate_js(js)
    except Exception as e:
        return "EXC:" + str(e)[:100]


def test_loop():
    lines = []
    try:
        # 等主窗口 js_api 就绪（不依赖 mini_hwnd）
        ready = False
        for _ in range(200):
            try:
                if app.main_window.evaluate_js("1+1") == 2:
                    ready = True
                    break
            except Exception:
                pass
            time.sleep(0.25)
        lines.append("js_api_ready=" + str(ready))
        if not ready:
            raise RuntimeError("main_window js_api not ready")
        # reload 页面重新挂 i18n/__app
        for _ in range(5):
            try:
                app.main_window.evaluate_js("window.location.reload()")
                break
            except Exception:
                time.sleep(0.5)
        # 等 __app 挂上
        app_ok = False
        for _ in range(120):
            if ev("typeof (window.__app||{}).renderDashboard") == "function":
                app_ok = True
                break
            time.sleep(0.5)
        lines.append("__app_ready=" + str(app_ok))
        if not app_ok:
            raise RuntimeError("__app not ready: " + str(ev("typeof window.__app")))
        time.sleep(1)

        lines.append("== 1 pager structure ==")
        lines.append(str(ev(
            "(function(){var a=window.__app;if(!a)return 'noApp';"
            "var pids=Object.keys(a.state.settings.providers||{});"
            "var pages=document.querySelectorAll('.pager-page').length;"
            "var cards=document.querySelectorAll('.pcard').length;"
            "var dots=document.querySelectorAll('.pager-dot').length;"
            "var active=document.querySelectorAll('.pager-dot.active').length;"
            "var per=[];document.querySelectorAll('.pager-page').forEach(function(p){per.push(p.querySelectorAll('.pcard').length);});"
            "var tr=document.querySelector('#dashTrack');"
            "return JSON.stringify({n:pids.length,pages:pages,cards:cards,dots:dots,active:active,per:per,"
            "transform:tr?tr.style.transform:null,info:a.pagerInfo(),stats:!!document.querySelector('.stats-section')});})()")))

        lines.append("== 2 pager go ==")
        lines.append(str(ev(
            "(function(){var a=window.__app;if(!a)return 'noApp';"
            "var pages=document.querySelectorAll('.pager-page').length;"
            "if(pages<2)return 'single-page:'+pages;"
            "a.pagerGo(1);"
            "var tr=document.querySelector('#dashTrack');"
            "var r1={info:a.pagerInfo(),transform:tr?tr.style.transform:null,"
            "actIdx:Array.prototype.indexOf.call(document.querySelectorAll('.pager-dot'),document.querySelector('.pager-dot.active'))};"
            "a.pagerGo(0);"
            "var r2={info:a.pagerInfo(),transform:tr?tr.style.transform:null,"
            "actIdx:Array.prototype.indexOf.call(document.querySelectorAll('.pager-dot'),document.querySelector('.pager-dot.active'))};"
            "return JSON.stringify({go1:r1,goBack:r2});})()")))

        lines.append("== 3 same-page drag ==")
        lines.append(str(ev(
            "(function(){var a=window.__app;if(!a)return 'noApp';"
            "var fp=document.querySelector('.pager-page');if(!fp)return 'noPage';"
            "var cs=fp.querySelectorAll('.pcard');"
            "if(cs.length<2)return 'one-per-page:'+cs.length;"
            "var c0=cs[0],c1=cs[1];"
            "var from=c0.getAttribute('data-pid'),to=c1.getAttribute('data-pid');"
            "c0.dispatchEvent(new Event('dragstart',{bubbles:true}));"
            "c1.dispatchEvent(new Event('dragover',{bubbles:true,cancelable:true}));"
            "c1.dispatchEvent(new Event('drop',{bubbles:true,cancelable:true}));"
            "c0.dispatchEvent(new Event('dragend',{bubbles:true}));"
            "var order=(a.state.settings.order||{}).providers||[];"
            "var ord=[];document.querySelectorAll('.pcard').forEach(function(c){ord.push(c.getAttribute('data-pid'));});"
            "return JSON.stringify({from:from,to:to,order:order.slice(0,4),ord:ord.slice(0,4),"
            "info:a.pagerInfo(),dots:document.querySelectorAll('.pager-dot').length});})()")))

        lines.append("== 4 diy chart off ==")
        lines.append(str(ev(
            "(function(){var a=window.__app;if(!a)return 'noApp';"
            "var s=a.state.settings;s.diy=s.diy||{};s.diy.modules=s.diy.modules||{};"
            "s.diy.modules.balance=s.diy.modules.balance||{};"
            "var old=s.diy.modules.balance.chart;"
            "s.diy.modules.balance.chart=false;a.renderAll();"
            "var gone=!document.querySelector('.stats-section');"
            "s.diy.modules.balance.chart=(old===undefined)?true:old;a.renderAll();"
            "var back=!!document.querySelector('.stats-section');"
            "return JSON.stringify({gone:gone,back:back});})()")))
    except Exception as e:
        lines.append("EXC:" + str(e))

    with open(RESULT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines), flush=True)

    # 恢复 config（drop 拖拽写了 order），再退出
    try:
        shutil.copy(BAK_PATH, CFG_PATH)
    except Exception as e:
        print("restore config fail:", e, flush=True)
    if os.path.exists(BAK_PATH):
        try:
            os.remove(BAK_PATH)
        except Exception:
            pass
    os._exit(0)


threading.Thread(target=test_loop, daemon=True).start()
try:
    app.run()
finally:
    if os.path.exists(BAK_PATH):
        try:
            shutil.copy(BAK_PATH, CFG_PATH)
            os.remove(BAK_PATH)
        except Exception:
            pass
