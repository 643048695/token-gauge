# -*- coding: utf-8 -*-
"""TokenGauge 应用包。

多模块架构：
- settings : 配置读写（config.json）
- kernel   : 调度内核（多供应商抓取、缓存、通知判断）
- notifier : 通知层（托盘气泡 / 系统通知 / 关闭）
- providers: 供应商实现（Agent A）
- themes   : 主题定义（Agent D）
"""

__version__ = "0.2.0"
