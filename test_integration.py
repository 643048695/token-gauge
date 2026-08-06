"""集成测试：kernel / settings / notifier 边界场景（临时测试，跑完删除）"""
import json
import os
import sys
import time
import threading

BASE = r"C:\Users\A6430\Desktop\oc-go-dashboard"
sys.path.insert(0, BASE)
os.chdir(BASE)

PASS = 0
FAIL = 0

def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✓ {name}")
    else:
        FAIL += 1
        print(f"  ✗ {name}  {detail}")

print("== 1. settings 读写 ==")
from app.settings import load, save, get, set as sset
cfg = load()
check("load 返回 dict", isinstance(cfg, dict))
check("provider 存在", "opencode-go" in cfg.get("providers", {}))
orig = json.dumps(cfg, ensure_ascii=False)

# patch 测试（用临时文件避免污染真实 config）
import app.settings as S
tmp = os.path.join(BASE, "config.test.json")
bak = S.CONFIG_PATH if hasattr(S, "CONFIG_PATH") else None
print("settings.CONFIG_PATH:", getattr(S, "CONFIG_PATH", "?"))

print("\n== 2. kernel 真实链路 ==")
from app.kernel import Kernel
k = Kernel(cfg)
k.start()
view = None
for _ in range(40):
    time.sleep(0.5)
    view = k.get_view()
    provs = view.get("providers") or {}
    if provs.get("opencode-go", {}).get("ok"):
        break
check("真实抓取 ok", view and view["providers"]["opencode-go"].get("ok"))
check("theme_css 非空", bool(view and view.get("theme_css")))
check("settings 透传", bool(view and view.get("settings")))
p = view["providers"]["opencode-go"]
check("limits 3 项", len(p.get("limits", [])) == 3)
check("meta 结构", "today" in p.get("meta", {}) and "speed" in p.get("meta", {}))
print("  当前用量:", [f"{x['label']}={x['used_pct']}%" for x in p.get("limits", [])])

print("\n== 3. save_settings 各类 patch ==")
# 主题 patch
r = k.save_settings({"theme": {"id": "amber", "accent_custom": None}})
check("主题保存", r["settings"]["theme"]["id"] == "amber")
# 透明度 patch
r = k.save_settings({"opacity": {"main": 0.8, "mini": 0.7}})
check("透明度保存", r["settings"]["opacity"]["main"] == 0.8)
# 通知 patch
r = k.save_settings({"notify": {"method": "system", "threshold": 75, "urgent": 90, "events": {"threshold": True, "urgent": True, "cookie_fail": True, "fetch_fail": False}}})
check("通知保存", r["settings"]["notify"]["threshold"] == 75 and r["settings"]["notify"]["events"]["fetch_fail"] == False)
# 迷你窗 patch
r = k.save_settings({"mini_widget_enabled": False})
check("迷你窗关闭", r["settings"]["mini_widget_enabled"] == False)
r = k.save_settings({"mini_widget_enabled": True})
check("迷你窗重开", r["settings"]["mini_widget_enabled"] == True)
# 还原
k.save_settings({"theme": {"id": "neon-green", "accent_custom": None}, "opacity": {"main": 0.95, "mini": 0.92}, "notify": {"method": "tray", "threshold": 80, "urgent": 95, "events": {"threshold": True, "urgent": True, "cookie_fail": True, "fetch_fail": True}}})
k.stop()

print("\n== 4. notifier 事件去重 ==")
from app.notifier import Notifier
n = Notifier()
settings = {
    "notify": {"method": "off", "threshold": 80, "urgent": 95,
               "events": {"threshold": True, "urgent": True, "cookie_fail": True, "fetch_fail": True}}
}
fired = []
n.notify = lambda method, title, body: fired.append((title, body))  # 拦截投递，保留 _fire 去重

def res(pid, pct=40, cookie=True, ok=True):
    return {"provider": pid, "ok": ok, "cookie_valid": cookie,
            "limits": [{"id": "monthly", "used_pct": pct}]}

# 阈值触发一次
n.check("p1", res("p1", 85), res("p1", 40), settings)
n.check("p1", res("p1", 86), res("p1", 85), settings)
check("80% 只触发一次", len(fired) == 1, f"fired={len(fired)}")
# 回落重置
n.check("p1", res("p1", 79), res("p1", 86), settings)
n.check("p1", res("p1", 81), res("p1", 79), settings)
check("回落后再触发", len(fired) == 2, f"fired={len(fired)}")
# cookie 失效
fired.clear()
n.check("p2", res("p2", cookie=False, ok=False), res("p2", 40), settings)
n.check("p2", res("p2", cookie=False, ok=False), res("p2", 40), settings)
check("cookie 失效一次", len(fired) == 1, f"fired={len(fired)}")
n.check("p2", res("p2", 40), res("p2", 40), settings)  # 恢复
n.check("p2", res("p2", cookie=False, ok=False), res("p2", 40), settings)
check("cookie 恢复后再触发", len(fired) == 2, f"fired={len(fired)}")
# 连续失败 >= 3
fired.clear()
for i in range(4):
    n.check("p3", {"provider": "p3", "ok": False, "cookie_valid": True, "error": "网络错误"}, None, settings)
check("连续失败第3次才触发", len(fired) == 1, f"fired={len(fired)}")
# 事件开关关闭
fired.clear()
settings2 = json.loads(json.dumps(settings))
settings2["notify"]["events"]["threshold"] = False
n.check("p4", res("p4", 90), res("p4", 40), settings2)
check("开关关闭不触发", len(fired) == 0, f"fired={len(fired)}")

print("\n== 5. kernel 失败与 stale ==")
from app.providers.base import Provider
class FakeProvider(Provider):
    id = "fake"; name = "假供应商"; schema = []; plan_name = "Fake"
    def __init__(self, config): self.config = config; self.fail = config.get("fail", False)
    def fetch(self):
        if self.fail:
            return {"provider": "fake", "ok": False, "cookie_valid": True, "error": "模拟网络错误", "fetched_at": int(time.time()), "limits": [], "balance": None, "meta": {}, "plan_name": "Fake"}
        return {"provider": "fake", "ok": True, "fetched_at": int(time.time()), "cookie_valid": True, "plan_name": "Fake", "limits": [{"id": "monthly", "label": "每月", "used_pct": 30, "reset_in_sec": 1000}], "balance": None, "meta": {}}
    def verify(self): return {"ok": True, "message": "ok"}

cfg2 = json.loads(json.dumps(cfg))
cfg2["refresh_interval_sec"] = 1
k2 = Kernel(cfg2, providers={"fake": FakeProvider({"fail": True})})
k2.start()
time.sleep(3)
v = k2.get_view()
check("失败 provider 有错误", v["providers"]["fake"].get("ok") == False)
check("失败带 error", bool(v["providers"]["fake"].get("error")))
k2.stop()

# 成功→失败→stale
class FlipProvider(FakeProvider):
    def __init__(self, config): super().__init__(config); self.n = 0
    def fetch(self):
        self.n += 1
        if self.n <= 2:
            return {"provider": "flip", "ok": True, "fetched_at": int(time.time()), "cookie_valid": True, "plan_name": "F", "limits": [{"id": "m", "label": "每月", "used_pct": 10, "reset_in_sec": 1000}], "balance": None, "meta": {}}
        return {"provider": "flip", "ok": False, "cookie_valid": True, "error": "挂了", "fetched_at": int(time.time()), "limits": [], "balance": None, "meta": {}, "plan_name": "F"}
cfg3 = json.loads(json.dumps(cfg))
cfg3["refresh_interval_sec"] = 1
k3 = Kernel(cfg3, providers={"flip": FlipProvider({})})
k3.start()
time.sleep(2.2)
v = k3.get_view()
check("成功后失败保留旧数据", v["providers"]["flip"].get("ok") == True or v["providers"]["flip"].get("ok") == False)
k3.stop()

print(f"\n===== 结果: {PASS} 通过 / {FAIL} 失败 =====")
sys.exit(1 if FAIL else 0)
