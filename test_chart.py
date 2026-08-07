# -*- coding: utf-8 -*-
"""柱形图增强验证（任务B feature/chart-polish）：
1) 柱顶标数字：auto 模式下 .sb-val 数量 >= 7（近7日每天柱顶都有总数标签）
2) 多色柱体：rect fill 去重 >= 2（多供应商各一色，颜色不再单调）
3) 单位快捷切换：点统计区 .unit-btn → display.unit 变化 + 柱顶数字变化（auto 原币种和 ≠ usd 换算和）
4) 主题联动：切 8bit 后柱体圆角(0px)/配色/网格线随主题变化（paper 为 6px 圆角）；切回 paper 复原
5) 结束恢复 config.json（unit/theme 会写盘）
注意：GUI 测试必须提权跑（受限 token 下 WebView2 起不来）；跑前杀残留 + 清 Temp/tmp*
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
RESULT = os.path.join(BASE, "test_chart_result.txt")

import webview  # noqa: E402
from main import DashboardApp  # noqa: E402

CFG_PATH = os.path.join(BASE, "config.json")
BAK_PATH = os.path.join(BASE, "config.json.chart.bak")
shutil.copy(CFG_PATH, BAK_PATH)

CFG = json.load(open(CFG_PATH, encoding="utf-8"))
app = DashboardApp(CFG)

# 注入 4 供应商 mock view（2 balance + 2 quota），保证统计区有 7 日堆叠数据
MOCK_JS = (
    "(function(){var a=window.__app;if(!a)return 'noApp';"
    "var s=a.state.settings;"
    "var v=a.state.view={providers:{},fetched_at:Date.now()};"
    "var pids=Object.keys(s.providers||{}).slice(0,4);"
    "if(!pids.length)return 'noProviders';"
    "pids.forEach(function(pid,i){"
    "var wk=[];for(var d=1;d<=7;d++){wk.push((i+1)*d);}"
    "if(i%2===0){"
    "v.providers[pid]={ok:true,meta:{kind:'balance',"
    "speed:{today_amount:5+i,week:wk},models:[{output:2}]},"
    "balance:{amount:100+i,currency:'CNY'}};"
    "}else{"
    "v.providers[pid]={ok:true,meta:{kind:'quota',"
    "today_tokens:1000+i*100,week_tokens:wk},"
    "balance:{amount:100+i,currency:'USD'}};"
    "}"
    "});"
    "a.renderAll();"
    "return 'mock:'+pids.length;})()"
)


def ev(js):
    try:
        return app.main_window.evaluate_js(js)
    except Exception as e:
        return "EXC:" + str(e)[:100]


def test_loop():
    lines = []
    try:
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
        for _ in range(5):
            try:
                app.main_window.evaluate_js("window.location.reload()")
                break
            except Exception:
                time.sleep(0.5)
        app_ok = False
        for _ in range(120):
            if ev("typeof (window.__app||{}).statsInfo") == "function":
                app_ok = True
                break
            time.sleep(0.5)
        lines.append("__app_ready=" + str(app_ok))
        if not app_ok:
            raise RuntimeError("__app not ready: " + str(ev("typeof window.__app")))
        time.sleep(1)

        # ---- 1/2. 塞 mock（auto 单位）→ 柱顶数字 + 多色 ----
        lines.append("== 1/2 auto: top labels & colors ==")
        lines.append("mock=" + str(ev(MOCK_JS)))
        lines.append(str(ev(
            "(function(){var a=window.__app;"
            "var s=a.statsInfo();"
            "var uniq={};s.fills.forEach(function(f){uniq[f]=1;});"
            "return JSON.stringify({exists:s.exists,segs:s.segs,uniqFills:Object.keys(uniq).length,"
            "vals:s.vals,valCount:s.vals.length,unit:s.unit});})()")))

        # ---- 3. 单位快捷切换：点 usd 按钮 ----
        lines.append("== 3 unit switch btn ==")
        lines.append(str(ev(
            "(function(){var a=window.__app;"
            "var b=document.querySelector('.stats-unit .unit-btn[data-unit=\"usd\"]');"
            "if(!b)return 'noBtn';"
            "var before=a.statsInfo().vals.join(',');"
            "b.click();"
            "var s2=a.statsInfo();"
            "var after=s2.vals.join(',');"
            "var active=document.querySelector('.stats-unit .unit-btn.active');"
            "return JSON.stringify({before:before,after:after,changed:before!==after,"
            "unit:s2.unit,active:active?active.getAttribute('data-unit'):null});})()")))

        # ---- 4. 主题联动：paper → 8bit ----
        lines.append("== 4 theme paper->8bit ==")
        paper = ev(
            "(function(){var a=window.__app;a.applyTheme('paper',null);return 1;})()")
        time.sleep(3)   # 等 save → get_theme_css → injectTheme 完成
        ev(MOCK_JS)
        lines.append("paper=" + str(ev(
            "(function(){var a=window.__app;var s=a.statsInfo();"
            "return JSON.stringify({rx:s.segRx,grid:s.gridStroke,fills:s.fills.slice(0,4),style:document.body.getAttribute('data-style')});})()")))
        ev("(function(){var a=window.__app;a.applyTheme('8bit',null);return 1;})()")
        time.sleep(3)
        ev(MOCK_JS)
        lines.append("8bit=" + str(ev(
            "(function(){var a=window.__app;var s=a.statsInfo();"
            "return JSON.stringify({rx:s.segRx,grid:s.gridStroke,fills:s.fills.slice(0,4),style:document.body.getAttribute('data-style')});})()")))
        # 切回 paper（恢复现场 + 断言可逆）
        ev("(function(){var a=window.__app;a.applyTheme('paper',null);return 1;})()")
        time.sleep(3)
        ev(MOCK_JS)
        lines.append("back=" + str(ev(
            "(function(){var a=window.__app;var s=a.statsInfo();"
            "return JSON.stringify({rx:s.segRx,style:document.body.getAttribute('data-style')});})()")))

        # ---- 收尾：单位回 auto ----
        ev("(function(){var a=window.__app;if(a.setDisplayUnit)a.setDisplayUnit('auto');return 1;})()")
        time.sleep(2)   # 等异步写盘完成，再恢复 config
    except Exception as e:
        lines.append("EXC:" + str(e))

    with open(RESULT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines), flush=True)

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
