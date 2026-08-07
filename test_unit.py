# -*- coding: utf-8 -*-
"""单元测试：纯逻辑层（推算/加密/存储/模板解析），不起 GUI。
运行：python -m unittest test_unit -v
"""
import json
import os
import sys
import tempfile
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


def _is_pending(t):
    """待校准模板：note 标注还需实测/自定义的，跳过严格契约。"""
    note = t.get("note", "") or ""
    return any(k in note for k in ("待实测", "待校准", "暂不支持", "自定义脚本", "需 AK/SK", "待确认"))


class TestSettingsPure(unittest.TestCase):
    """settings 纯逻辑：深合并/点路径（不碰真实 config.json）。"""

    def test_deep_merge_defaults(self):
        # override 部分覆盖时，默认值深层键被补齐
        merged = settings._deep_merge(
            settings.DEFAULTS,
            {"diy": {"mini_provider": "deepseek"}},
        )
        self.assertEqual(merged["diy"]["mini_provider"], "deepseek")
        self.assertTrue(merged["diy"]["modules"]["balance"]["bal_main"])

    def test_deep_merge_unknown_keys_kept(self):
        merged = settings._deep_merge({"a": 1}, {"b": 2})
        self.assertEqual(merged, {"a": 1, "b": 2})

    def test_deep_merge_scalar_replace(self):
        # 真深合并：同层键更新，未覆盖的键保留（settings._deep_merge 契约）
        merged = settings._deep_merge(
            {"notify": {"threshold": 80, "urgent": 95}},
            {"notify": {"threshold": 90}},
        )
        self.assertEqual(merged["notify"]["threshold"], 90)
        self.assertEqual(merged["notify"]["urgent"], 95)  # 深合并保留未覆盖键

    def test_split_path(self):
        self.assertEqual(settings._split_path(""), [])
        self.assertEqual(settings._split_path("a"), ["a"])
        self.assertEqual(settings._split_path("a.b.c"), ["a", "b", "c"])

    def test_set_path_creates_middle(self):
        cfg = {}
        settings._set_path(cfg, "diy.modules.balance.chart", False)
        self.assertEqual(cfg, {"diy": {"modules": {"balance": {"chart": False}}}})

    def test_set_path_overwrite(self):
        cfg = {"notify": {"threshold": 80}}
        settings._set_path(cfg, "notify.threshold", 99)
        self.assertEqual(cfg["notify"]["threshold"], 99)

    def test_get_dot_path_in_memory(self):
        # 用内存态验证 get，不读真实磁盘
        old = settings._current
        try:
            settings._current = {"notify": {"threshold": 80}}
            self.assertEqual(settings.get("notify.threshold"), 80)
            self.assertIsNone(settings.get("notify.nonexist"))
            self.assertEqual(settings.get("")["notify"]["threshold"], 80)
        finally:
            settings._current = old


class TestDiyDefaults(unittest.TestCase):
    """DIY 默认值回归保护：布尔必须是大写 True（曾误写小写 true 炸过）。"""

    def test_balance_modules_all_true(self):
        bal = settings.DEFAULTS["diy"]["modules"]["balance"]
        for key in ("bal_main", "meta_grid", "token_est", "chart"):
            self.assertIn(key, bal, f"balance.{key} 缺失")
            self.assertIs(bal[key], True, f"balance.{key} 必须是 True（bool）")

    def test_quota_modules_all_true(self):
        qua = settings.DEFAULTS["diy"]["modules"]["quota"]
        for key in ("progress", "tokens", "chart"):
            self.assertIn(key, qua)
            self.assertIs(qua[key], True)

    def test_mini_provider_default_empty(self):
        self.assertEqual(settings.DEFAULTS["diy"]["mini_provider"], "")


class TestDisplayOrderDefaults(unittest.TestCase):
    """计量单位/汇率/拖拽顺序默认值回归（统计重构新增配置）。"""

    def test_display_defaults(self):
        d = settings.DEFAULTS["display"]
        self.assertEqual(d["unit"], "auto")
        self.assertEqual(d["fx_rate"], 7.2)

    def test_order_defaults(self):
        self.assertEqual(settings.DEFAULTS["order"]["providers"], [])


class TestTemplates(unittest.TestCase):
    """供应商模板完整性：顺序/必填字段/形态契约。"""

    def test_order_matches_templates(self):
        self.assertEqual(len(tpl.TEMPLATE_ORDER), 13)
        for pid in tpl.TEMPLATE_ORDER:
            self.assertIn(pid, tpl.TEMPLATES, f"模板缺失: {pid}")
        for pid in tpl.TEMPLATES:
            self.assertIn(pid, tpl.TEMPLATE_ORDER, f"模板不在顺序表: {pid}")

    def test_required_fields(self):
        for pid, t in tpl.TEMPLATES.items():
            for field in ("name", "kind", "url", "method", "auth"):
                self.assertIn(field, t, f"{pid} 缺 {field}")
            self.assertIsInstance(t["name"], str)
            # url 可为真实地址、{base} 占位（中转模板）、或空（待校准，note 说明）
            self.assertTrue(
                t["url"].startswith("http") or "{base}" in t["url"] or _is_pending(t),
                f"{pid} url 非法")
            if "site" in t:
                self.assertIsInstance(t["site"], str)
            if "peak" in t:
                self.assertIsInstance(t["peak"], bool)

    def test_kind_contract(self):
        for pid, t in tpl.TEMPLATES.items():
            kind = t["kind"]
            self.assertIn(kind, ("balance", "relay", "quota"), f"{pid} kind 非法: {kind}")
            if kind == "balance":
                if _is_pending(t):
                    continue  # 待校准模板结构未定，跳过
                self.assertTrue(t.get("mapping", {}).get("remaining"),
                                f"{pid} balance 型必须有 mapping.remaining")
            elif kind == "relay":
                mp = t.get("mapping", {})
                self.assertTrue(mp.get("limit") or mp.get("used"),
                                f"{pid} relay 型必须有 limit/used")
            elif kind == "quota":
                wins = t.get("windows", [])
                if _is_pending(t):
                    continue  # 待校准模板结构未定，跳过
                self.assertTrue(wins, f"{pid} quota 型必须有 windows")
                for w in wins:
                    self.assertIn("id", w)
                    self.assertIn("label", w)
                    # 两种窗口结构：used_of.limit（kimi 系）或 pct（zai 系）
                    self.assertTrue(
                        w.get("used_of", {}).get("limit") or w.get("pct"),
                        f"{pid} window 必须有 used_of.limit 或 pct")

    def test_models_price_table(self):
        # 有 models 的模板，单价必须为正数
        for pid, t in tpl.TEMPLATES.items():
            for m in (t.get("static", {}) or {}).get("models", []) or []:
                for k in ("input", "output"):
                    if m.get(k) is not None:
                        self.assertGreater(m[k], 0, f"{pid}.{m.get('name')} {k} 单价非法")


class TestCliMarker(unittest.TestCase):
    """热重载标记：写操作后留 .config_changed（临时路径，不污染项目根）。"""

    def setUp(self):
        import cli
        # 沙箱对新建目录有限制，直接复用项目根可写路径（测后删除）
        self._old_marker = cli.CONFIG_MARKER
        self._test_marker = os.path.join(BASE, ".config_changed_unit_test")
        cli.CONFIG_MARKER = self._test_marker

    def tearDown(self):
        import cli
        cli.CONFIG_MARKER = self._old_marker
        try:
            os.remove(self._test_marker)
        except OSError:
            pass

    def test_marker_created(self):
        import cli
        cli._mark_changed()
        self.assertTrue(os.path.exists(cli.CONFIG_MARKER))
        with open(cli.CONFIG_MARKER, encoding="utf-8") as f:
            content = f.read().strip()
        self.assertTrue(content, "标记内容不应为空")
        self.assertTrue(float(content) > 0, "标记应为时间戳")


if __name__ == "__main__":
    unittest.main(verbosity=2)
