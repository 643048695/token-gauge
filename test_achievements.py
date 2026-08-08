# -*- coding: utf-8 -*-
"""成就引擎单测：模拟快照/settings 验证解锁逻辑、进度、幂等。"""
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta

# 让 achievements 的 DATA_DIR 指向临时目录（不污染真实数据）
import app.achievements as ach

_TMP = tempfile.mkdtemp(prefix="ach_test_")
ach.DATA_DIR = _TMP
ach.STATE_FILE = os.path.join(_TMP, "achievements.json")


def _ts(days_ago, hour=12):
    return int((datetime.now() - timedelta(days=days_ago)).replace(hour=hour, minute=0, second=0).timestamp())


def _snap(pct, days_ago, hour=12):
    return {"ts": _ts(days_ago, hour), "monthly_pct": pct, "balance": 0.0}


class TestAchievements(unittest.TestCase):
    def setUp(self):
        if os.path.exists(ach.STATE_FILE):
            os.remove(ach.STATE_FILE)

    def test_burn_tiers_and_usd(self):
        """57% 用量 → 冲榜者+破费者+挥金如土；token 阶梯按目标推进。"""
        settings = {"ui": {}, "providers": {}}
        snaps = {"ocg": [_snap(57, i) for i in range(3)]}  # 3 天 57%
        new = ach.check_and_unlock(settings, snaps)
        ids = {n["id"] for n in new}
        self.assertIn("burn_50pct", ids)          # 57% ≥ 50%
        self.assertIn("spend_5", ids)             # $60*57% ≈ $34 ≥ $5
        self.assertIn("spend_25", ids)            # ≥ $25
        self.assertNotIn("burn_90pct", ids)       # 57% < 90%
        # token 估算：60/2*1e6*0.57 = 1710 万 → 初燃/烈焰/熔炉都该解锁
        self.assertIn("burn_first", ids)
        self.assertIn("burn_mil", ids)
        self.assertIn("burn_10mil", ids)
        self.assertNotIn("burn_100mil", ids)      # 1710 万 < 1 亿 → 不解锁 ✓

    def test_streak_and_total_days(self):
        """连续 3 天 + 累计 4 天。"""
        settings = {"ui": {}, "providers": {}}
        snaps = {"ocg": [_snap(10, 3), _snap(10, 2), _snap(10, 1), _snap(10, 0)]}
        new = ach.check_and_unlock(settings, snaps)
        ids = {n["id"] for n in new}
        self.assertIn("stick_3", ids)
        self.assertIn("stick_7", ids) if False else None
        self.assertNotIn("stick_7", ids)          # 连续只有 4 天
        # 断开序列：隔天 → streak 断
        snaps2 = {"ocg": [_snap(10, 5), _snap(10, 3), _snap(10, 2)]}
        ids2 = {n["id"] for n in ach.check_and_unlock(settings, snaps2)}
        self.assertNotIn("stick_3", ids2)         # 5→3 断开，最长连续 2 天

    def test_night_and_weekend_flags(self):
        settings = {"ui": {}, "providers": {}}
        snaps = {"ocg": [_snap(5, 2, hour=1), _snap(5, 1, hour=12)]}
        new = ach.check_and_unlock(settings, snaps)
        ids = {n["id"] for n in new}
        self.assertIn("stick_night", ids)         # 凌晨 1 点
        # 周末：从今天往前找周六日
        d = datetime.now()
        while d.weekday() < 5:
            d -= timedelta(days=1)
        snaps2 = {"ocg": [_snap(5, (datetime.now() - d).days, hour=10)]}
        ids2 = {n["id"] for n in ach.check_and_unlock(settings, snaps2)}
        self.assertIn("stick_weekend", ids2)

    def test_setup_achievements(self):
        """配置类：初试锋芒 / 多面手 / 双料特工。"""
        settings = {
            "ui": {"onboarded": True},
            "providers": {
                "a": {"enabled": True, "type": "deepseek", "config": {"api_key": "sk-x"}},
                "b": {"enabled": True, "type": "openai-compatible", "config": {"api_key": "sk-y"}},
                "c": {"enabled": True, "type": "opencode-go", "config": {"auth_cookie": "Fe26.2"}},
            },
        }
        new = ach.check_and_unlock(settings, {})
        ids = {n["id"] for n in new}
        self.assertIn("setup_first", ids)
        self.assertIn("setup_3", ids)
        self.assertIn("setup_dual", ids)
        self.assertNotIn("setup_6", ids)          # 只有 3 个

    def test_explore_via_flags(self):
        """探索类：5 页面 → 全知者；托盘/迷你窗 flag。"""
        settings = {"ui": {}, "providers": {}}
        for p in ["dashboard", "providers", "appearance", "notify", "about"]:
            ach.record_flag("page_visited", p)
        ach.record_flag("hide_tray")
        ach.record_flag("mini")
        new = ach.check_and_unlock(settings, {})
        ids = {n["id"] for n in new}
        self.assertIn("explore_all", ids)
        self.assertIn("explore_tray", ids)
        self.assertIn("explore_mini", ids)

    def test_idempotent(self):
        """重复检查不重复解锁、状态持久化。"""
        settings = {"ui": {"onboarded": True},
                    "providers": {"a": {"enabled": True, "type": "deepseek",
                                        "config": {"api_key": "sk-x"}}}}
        snaps = {"ocg": [_snap(60, 1)]}
        first = ach.check_and_unlock(settings, snaps)
        self.assertTrue(first)
        second = ach.check_and_unlock(settings, snaps)
        self.assertEqual(second, [])
        state = ach.get_state()
        for n in first:
            self.assertIn(n["id"], state["unlocked"])
        # 进度接口
        full = ach.get_achievements(settings, snaps)
        self.assertEqual(full["total"], 23)
        self.assertEqual(full["unlocked_count"], len(first))

    def test_progress_bars(self):
        """进度条：未达标成就显示 progress。"""
        settings = {"ui": {}, "providers": {}}
        snaps = {"ocg": [_snap(30, 1)]}   # 30% → 900 万 token
        full = ach.get_achievements(settings, snaps)
        burn_bil = next(x for x in full["list"] if x["id"] == "burn_bil")
        self.assertFalse(burn_bil["unlocked"])
        self.assertGreater(burn_bil["progress"], 0)
        self.assertLess(burn_bil["progress"], burn_bil["target"])


if __name__ == "__main__":
    unittest.main()
