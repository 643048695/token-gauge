# -*- coding: utf-8 -*-
"""单元测试：纯逻辑层（推算/加密/存储/模板解析），不起 GUI。
运行：python -m unittest test_unit -v
"""
import json
import os
import sys
import time
import unittest

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
os.chdir(BASE)

from app import settings, store  # noqa: E402
from app.providers import api_provider as ap  # noqa: E402
from app.providers import api_templates as tpl  # noqa: E402
from app.providers.opencode_go import OpenCodeGoProvider  # noqa: E402

NOW = int(time.time())
DAY = 86400


def snap(ts, pct, balance=None):
    s = {"ts": ts, "monthly_pct": pct, "weekly_pct": 0, "rolling_pct": 0}
    if balance is not None:
        s["balance"] = balance
    return s


class TestDpapi(unittest.TestCase):
    def test_roundtrip(self):
        enc = settings._dpapi_encrypt("sk-secret-123")
        self.assertTrue(enc.startswith("DPAPI:") or enc == "sk-secret-123")
        self.assertEqual(settings._dpapi_decrypt(enc), "sk-secret-123")

    def test_plain_passthrough(self):
        self.assertEqual(settings._dpapi_decrypt("plain-value"), "plain-value")

    def test_walk_secrets(self):
        cfg = {"providers": {"d": {"config": {"api_key": "k1", "name": "x"}}}}
        settings._walk_secrets(cfg, settings._dpapi_encrypt)
        self.assertTrue(cfg["providers"]["d"]["config"]["api_key"].startswith("DPAPI:"))
        self.assertEqual(cfg["providers"]["d"]["config"]["name"], "x")
        settings._walk_secrets(cfg, settings._dpapi_decrypt)
        self.assertEqual(cfg["providers"]["d"]["config"]["api_key"], "k1")


class TestStore(unittest.TestCase):
    PID = "_unit_test_provider"

    def tearDown(self):
        try:
            os.remove(store._path(self.PID))
            os.remove(store._path(self.PID) + ".tmp")
        except OSError:
            pass

    def test_append_and_read(self):
        store.append(self.PID, {"ok": True, "limits": [{"id": "monthly", "used_pct": 42}], "balance": {"amount": 8.8}})
        snaps = store.snapshots(self.PID)
        self.assertEqual(len(snaps), 1)
        self.assertEqual(snaps[0]["monthly_pct"], 42)
        self.assertEqual(snaps[0]["balance"], 8.8)
        # 重复秒不落盘
        store.append(self.PID, {"ok": True, "limits": [{"id": "monthly", "used_pct": 43}], "balance": {"amount": 8.7}})
        self.assertEqual(len(store.snapshots(self.PID)), 1)
        # 原子写无 tmp 残留
        self.assertFalse(os.path.exists(store._path(self.PID) + ".tmp"))


class TestApiProvider(unittest.TestCase):
    def test_to_number(self):
        self.assertEqual(ap._to_number("12.5"), 12.5)
        self.assertEqual(ap._to_number(3), 3.0)
        self.assertIsNone(ap._to_number(True))
        self.assertIsNone(ap._to_number("abc"))

    def test_resolve_path(self):
        data = {"a": {"b": [{"c": 7}]}}
        self.assertEqual(ap._resolve_path(data, "a.b[0].c"), 7)
        self.assertIsNone(ap._resolve_path(data, "a.x"))

    def test_speed_meta(self):
        p = ap.ApiProvider({"api_key": "x"})
        p.id = "_unit_bal"
        # 直接写带自定义 ts 的快照（模拟 4 天余额下降：10→9→8→7，日均 1）
        os.makedirs(store.DATA_DIR, exist_ok=True)
        with open(store._path(p.id), "w", encoding="utf-8") as f:
            json.dump({"snapshots": [
                snap(NOW - 3 * DAY, 0, 10.0), snap(NOW - 2 * DAY, 0, 9.0),
                snap(NOW - 1 * DAY, 0, 8.0), snap(NOW, 0, 7.0),
            ]}, f)
        meta = p._speed_meta(7.0, NOW)
        self.assertTrue(meta["data_ready"])
        self.assertAlmostEqual(meta["daily_amount"], 1.0, delta=0.2)
        self.assertIsNotNone(meta["days_left"])
        self.assertIsNotNone(meta["total_consumed"])
        self.assertIsNotNone(meta["since_ts"])
        try:
            os.remove(store._path(p.id))
        except OSError:
            pass

    def test_peak_flag_templates(self):
        self.assertTrue(tpl.TEMPLATES["deepseek"].get("peak"))
        self.assertFalse(tpl.TEMPLATES["kimi"].get("peak"))
        self.assertTrue(tpl.TEMPLATES["deepseek"].get("static", {}).get("models"))


class TestOpencode(unittest.TestCase):
    def test_week_pct(self):
        prov = OpenCodeGoProvider({})
        snaps = [
            snap(NOW - 4 * DAY, 10), snap(NOW - 3 * DAY, 15),
            snap(NOW - 2 * DAY, 18), snap(NOW - 1 * DAY, 20),
        ]
        wp = prov._week_pct(25, snaps, NOW)  # 今日 25
        self.assertEqual(len(wp), 5)
        self.assertEqual(wp[-1], 5.0)  # 25-20
        self.assertEqual(wp[-2], 2.0)  # 20-18

    def test_today_meta(self):
        prov = OpenCodeGoProvider({})
        snaps = [snap(NOW - 2 * DAY, 10), snap(NOW - DAY, 14)]
        t = prov._today_meta(20, snaps, NOW)
        # 今日基准 = 昨天 14 → delta 6
        self.assertAlmostEqual(t["delta_pct"], 6.0, delta=0.1)

    def test_models(self):
        prov = OpenCodeGoProvider({"est_model": "glm-5.2"})
        self.assertEqual(prov._build_meta(50, NOW)["est_model_label"], "GLM-5.2")


if __name__ == "__main__":
    unittest.main(verbosity=2)
