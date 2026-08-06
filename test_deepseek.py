# -*- coding: utf-8 -*-
"""验证：各供应商 token 量 + 已用 + 起点标注"""
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
    f.write("=== token 量全面验证 %s ===\n" % time.strftime("%Y-%m-%d %H:%M:%S"))

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

    # mock relay + quota（塞缓存）
    from app.providers import PROVIDERS
    app.kernel._cache["openrouter-mock"] = {
        "provider": "openrouter-mock", "ok": True, "fetched_at": int(time.time()),
        "plan_name": "OpenRouter", "limits": [{"id": "quota", "label": "总量", "used_pct": 30, "reset_in_sec": None}],
        "balance": {"currency": "USD", "amount": 5.5},
        "site": "https://openrouter.ai", "peak": False,
        "meta": {"kind": "relay", "template": "openrouter", "unit": "amount",
                 "speed": {"data_ready": True, "total_consumed": 2.3, "since_ts": int(time.time()) - 86400 * 3,
                           "today_amount": 0.2, "week": [0.1, 0.2, 0.1, 0.1, 0.3, 0.1, 0.2]}},
    }
    app.kernel._cache["kc-mock"] = {
        "provider": "kc-mock", "ok": True, "fetched_at": int(time.time()),
        "plan_name": "Kimi Coding", "limits": [{"id": "weekly", "label": "周", "used_pct": 55, "reset_in_sec": 86400}],
        "balance": {"currency": "", "amount": 55.0},
        "site": "https://platform.moonshot.cn", "peak": False,
        "meta": {"kind": "quota", "template": "kimi-coding", "unit": "tokens",
                 "remaining_tokens": 260000000, "available_tokens": 260000000,
                 "used_tokens": 310000000, "total_tokens": 570000000},
    }
    time.sleep(2)
    try:
        app.main_window.evaluate_js("window.location.reload()")
    except Exception:
        pass
    time.sleep(6)

    js = """JSON.stringify((function(){
      var cards = Array.prototype.slice.call(document.querySelectorAll('.pcard'));
      return cards.map(function(c){
        var name = (c.querySelector('.pcard-name')||{}).textContent || '?';
        var rec = {name:name};
        rec.teHead = (c.querySelector('.te-head')||{}).textContent || null;
        rec.teRows = Array.prototype.slice.call(c.querySelectorAll('.te-row')).map(function(r){return r.textContent.trim();});
        rec.cells = Array.prototype.slice.call(c.querySelectorAll('.meta-cell .meta-k')).map(function(x){return x.textContent;});
        rec.vals = Array.prototype.slice.call(c.querySelectorAll('.meta-cell .meta-v')).map(function(x){return x.textContent;});
        rec.err = (c.querySelector('.chip.danger')||{}).textContent || null;
        return rec;
      });
    })())"""
    try:
        r = app.main_window.evaluate_js(js)
        log("各卡 token: " + str(r))
    except Exception as e:
        log("evaluate 异常: %s" % e)
    log("测试完成")


threading.Thread(target=test_loop, daemon=True).start()
app.run()
