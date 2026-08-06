# OC-GO Dashboard v0.2

OpenCode Go 额度监控桌面工具：多供应商额度仪表盘 + 设置中心（主题/透明度/通知 DIY）。

## 运行

```bash
python main.py
```

自测：`python test_integration.py`（settings/kernel/notifier 边界场景，21 项断言）

启动后：
- **双击托盘图标**（绿色圆点）→ 打开/隐藏主面板（920×600，五页：仪表盘 / 供应商 / 外观 / 通知 / 关于）
- **迷你悬浮窗**（默认右下角，可在外观页开关/调尺寸）常驻显示第一个供应商的核心额度
- 托盘右键：打开主面板 / 显示迷你窗 / 立即刷新 / 退出
- 主面板关闭按钮 = 隐藏到托盘，不退出

## 功能

- **多供应商**：`app/providers/` 插件化，加新供应商 = 新写一个 Provider 文件 + 界面填凭据
- **仪表盘**：每个供应商一张卡（限额进度条组 / 余额 / 重置倒计时 / 速度推算 / 今日用量 / 状态灯）
- **DIY 设置中心**：6 套霓虹主题 + 自定义主色、透明度滑条（主面板/迷你窗独立）、通知方式（托盘/系统/关闭）、阈值、刷新间隔、密度、货币显示
- **通知**：80% 预警 / 95% 紧急 / cookie 失效 / 连续失败，事件独立开关
- **速度推算**：三层估算（线性回归 / 今日平均 / 短时），带可信度来源

## 配置（config.json，界面改完即时保存）

| 字段 | 说明 |
|---|---|
| `providers.<id>.config` | 各供应商凭据（opencode-go: workspace_id + auth_cookie） |
| `refresh_interval_sec` | 抓取间隔（默认 300） |
| `theme` / `opacity` / `notify` / `window` | 主题、透明度、通知、窗口参数 |

## 架构

```
main.py              入口：托盘 + 窗口管理 + js_api
app/kernel.py        调度内核：多供应商并行抓取、缓存、stale 标记
app/settings.py      配置读写（深合并默认值、点路径）
app/notifier.py      通知（tray/system/off + 事件去重）
app/themes.py        6 套霓虹主题 + build_css
app/providers/       Provider 插件（base.py 抽象 + opencode_go.py 实现）
app/store.py         per-provider 快照（30 天，app/data/snapshots/）
ui/main_panel.html   主面板（单文件全内联）
ui/mini_widget.html  迷你悬浮窗
```

接口契约见 `INTERFACES.md`，完善路线见 `PLAN.md`。

## 跟 HanaAgent 联动

`hana-plugin/` 是 Hana 插件：Hana 启动时自动拉起小组件，退出时回收。安装到 Hana 用户插件目录后启用。

## 注意

- 只读访问 opencode.ai 官方页面，不上传数据到第三方
- auth_cookie 是账号钥匙，勿外传；失效时界面红色 EXPIRED + 通知提醒，更新 config.json 即可
