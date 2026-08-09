# TokenGauge — LLM Token Gauge · token 油表

> **Monitor your LLM quota at a glance** — how many tokens are left, how long you can keep burning, across multiple providers. / 多供应商 LLM 额度/余量监控桌面工具：一眼看清各家模型还剩多少 token、还能烧多久。

[中文版介绍见下](#中文) · English below

---

## 下载 Download

**Windows 一键版（免 Python 环境）**：[下载 TokenGauge.exe](https://github.com/643048695/token-gauge/releases)（GitHub Releases，解压即用）

源码运行见 [安装 Installation](#安装-installation)。

---

# 中文

## 截图 Screenshots

**主界面 · Matrix 主题**（暗色霓虹）：

![主界面 Matrix](assets/screenshot.png)

**主界面 · 纸面极简主题**（默认）：

![主界面 Paper](assets/shot-paper.png)

**右下角迷你悬浮窗**（HUD，可拖动调大小）：

![迷你窗](assets/mini.png)

**外观设置页 · 5 套主题**（纸面极简 / 8位像素 / 黑客帝国 / 粗野主义 / 机密档案）：

![外观-纸面](assets/shot-appearance.png)

**粗野主义主题**（纯黑白·硬边框）：

![外观-粗野](assets/shot-brutal.png)

**成就系统**（37 个成就 · 燃烧/坚持/配置/探索四大类）：

![成就](assets/shot-achievements.png)

**8bit 像素主题 · 英文界面**（界面中英双语可切换）：

![8bit 英文](assets/shot-8bit-en.png)

## 功能特性 Features

- **多供应商监控**：OpenCode Go（额度型）+ DeepSeek / Kimi / SiliconFlow 等（余额型 API）统一仪表盘；`app/providers/` 插件化，加新供应商 = 新写一个 Provider 文件
- **实时抓取**：默认每 30 分钟（可配 60–1800s），失败自动重试、STALE 标记、单实例防重复
- **限额进度条**：5h 滚动 / 每周 / 每月限额，含重置倒计时
- **三层速度推算**：线性回归趋势 / 今日平均 / 短时速度，带可信度来源（"还能撑 X 天"）
- **阈值通知**：80% 预警 / 95% 紧急 / cookie 失效 / 连续抓取失败，托盘 / 系统 / 关闭三档，事件独立开关
- **5 套主题**：纸面极简 / 8位像素 / 黑客帝国 / 粗野主义 / 机密档案，自定义主色 + 透明度（主面板/迷你窗独立）
- **碳足迹换算**：今日消耗 ≈ 几度电 / 几本书 / 手机充电几次 / LED 亮多久，数据不再抽象
- **激励系统**：37 个成就（解锁带礼花彩带）+ 基准对比（"已超越 X% 的开发者 · 约 Y 人"）+ 本月消耗进度
- **迷你悬浮窗**：右下角霓虹 HUD，常显核心额度，可调大小/透明度/拖动
- **中英双语**：界面一键切换，词条全量覆盖（含图表/通知/托盘）
- **成就 Toast**：解锁时彩色粒子礼花 + 图标弹跳（尊重系统"减少动态效果"）

## 与 Agent 联动 Agent Integration

这个项目**从第一天起就是 Agent 开发的**（Hermes / HanaAgent 等协作迭代），因此对 AI Agent 非常友好：

| 联动点 | 说明 |
|---|---|
| **HanaAgent 插件** | `hana-plugin/` 是 Hana 插件：Hana 启动时自动拉起右下角小组件，退出时回收进程。安装到 Hana 用户插件目录并启用即可 |
| **CLI 接口** | `cli.py` 提供 `add / set / rm / list / test` 五个子命令——Agent 可在终端里添加供应商、改配置、测试连接（如 `python cli.py add kimi-main --type kimi`） |
| **接口契约** | `INTERFACES.md` 定义了完整的文件边界与数据契约——多个 Agent 可并行开发互不踩踏（本项目的迭代方式） |
| **js_api 桥** | 前端通过 `window.pywebview.api` 暴露 15+ 方法（get_view / save_settings / refresh_now / get_achievements / …），外部可注入调用 |
| **数据快照** | `app/data/snapshots/` 每个供应商 30 天 JSON 快照——Agent 可直接读取做离线分析 |
| **单文件前端** | `ui/main_panel.html` 全内联单文件（CSS/JS/HTML 一体）——Agent 改界面零构建、零依赖 |
| **零配置启动** | `python main.py` 直接跑；无凭据时进开屏引导页，界面填完即时保存 |

## 工作原理 How It Works

1. **抓取**：按 `refresh_interval_sec` 周期并行抓取各供应商（额度型读官方页面、余额型调官方 API）
2. **快照**：每次成功抓取写入 `app/data/snapshots/<provider>.json`（保留 30 天）
3. **推算**：基于快照做三层估算（线性回归 / 今日平均 / 短时），输出"还能撑 X 天"及可信度
4. **呈现**：主面板 / 迷你窗 / 通知三端联动；凭据 DPAPI 加密落盘（仅本机可解）

## 安装 Installation

```bash
# Windows · Python 3.11+
git clone https://github.com/643048695/token-gauge.git
cd token-gauge
pip install -r requirements.txt
```

首次运行前：复制 `config.example.json` 为 `config.json`，填入供应商凭据（或在界面"供应商"页填写，即时保存）。

## 运行 Running

```bash
python main.py
```

- **双击托盘图标**（绿色圆点）→ 打开/隐藏主面板
- 主面板关闭按钮 = 隐藏到托盘，不退出
- 迷你悬浮窗默认右下角，外观页可开关/调尺寸/调透明度
- 托盘右键：打开主面板 / 显示迷你窗 / 立即刷新 / 退出

## 配置 Configuration（config.json）

| 字段 | 说明 |
|---|---|
| `providers.<id>.config` | 各供应商凭据（opencode-go: workspace_id + auth_cookie；api 型: api_key + base_url） |
| `refresh_interval_sec` | 抓取间隔（默认 300，可配 60–1800） |
| `theme` / `opacity` / `notify` / `window` | 主题、透明度、通知、窗口参数 |
| `display` | 单位显示（auto/usd/cny/tokens）、汇率 |
| `diy.modules` | 卡片模块开关（meta_grid / token_est / chart / …） |

界面改完即时保存，无需手编 JSON。

## 测试 Testing

```bash
python -m unittest test_achievements test_unit   # 36 项单测
python test_integration.py                        # 21 项边界断言（settings/kernel/notifier）
```

CI（GitHub Actions, windows-latest）每次 push 自动跑。

## 架构 Architecture

```
main.py              入口：托盘 + 窗口管理 + js_api（pywebview）
app/kernel.py        调度内核：多供应商并行抓取、缓存、stale 标记
app/settings.py      配置读写（深合并默认值、点路径）
app/notifier.py      通知（tray/system/off + 事件去重）
app/themes.py        5 套主题 + build_css
app/achievements.py  37 个成就定义与判定
app/providers/       Provider 插件（base.py 抽象 + opencode_go.py / api_provider.py）
app/store.py         per-provider 快照（30 天，app/data/snapshots/）
ui/main_panel.html   主面板（单文件全内联）
ui/mini_widget.html  迷你悬浮窗
ui/index.html        开屏引导
cli.py               命令行接口（Agent 可调用）
```

---

# English

## Screenshots

![Main (Matrix theme)](assets/screenshot.png)

![Main (Paper theme)](assets/shot-paper.png)

![Mini widget HUD](assets/mini.png)

![Appearance · themes](assets/shot-appearance.png)

![Brutalism theme](assets/shot-brutal.png)

![Achievements](assets/shot-achievements.png)

![8bit theme · English UI](assets/shot-8bit-en.png)

## Features

- **Multi-provider dashboard**: quota-based (OpenCode Go) and balance-based (DeepSeek / Kimi / SiliconFlow, etc.) providers on one screen; `app/providers/` is pluggable — add a provider by writing one file
- **Scheduled fetching** (default 30 min, configurable 60–1800s), retry on failure, STALE marking, single-instance lock
- **Quota progress bars** with reset countdowns (5h rolling / weekly / monthly)
- **3-layer burn-rate forecast** (linear regression / daily average / short-term) with confidence source ("days left")
- **Threshold notifications**: 80% warn / 95% urgent / cookie expiry / repeated failures; tray / system / off
- **5 themes** + custom accent color and transparency (main panel & mini widget independently)
- **Real-world equivalences**: today's burn ≈ kWh / books / phone charges / LED hours
- **Gamification**: 37 achievements (confetti on unlock) + dev percentile benchmark ("ahead of X% of developers")
- **Mini HUD widget** (bottom-right, resizable, draggable, transparent)
- **Bilingual UI** (中文/English, fully translated incl. charts, notifications, tray)
- **Accessibility**: respects `prefers-reduced-motion`

## Agent Integration

This project has been developed **by AI agents from day one** (Hermes / HanaAgent co-development), so it is agent-friendly:

| Integration | Description |
|---|---|
| **HanaAgent plugin** | `hana-plugin/` spawns the mini widget on Hana startup and reaps it on exit |
| **CLI** | `cli.py add / set / rm / list / test` — agents can manage providers from the terminal |
| **Interface contract** | `INTERFACES.md` defines file boundaries & data contracts for parallel agent development |
| **js_api bridge** | 15+ methods exposed via `window.pywebview.api` (get_view / save_settings / refresh_now / …) |
| **Data snapshots** | 30-day JSON snapshots per provider in `app/data/snapshots/` — readable offline by agents |
| **Single-file frontend** | `ui/main_panel.html` is fully inlined (HTML/CSS/JS) — zero build, zero deps |
| **Zero-config start** | `python main.py`; onboarding wizard when no credentials exist |

## How It Works

1. **Fetch**: parallel per-provider fetching on `refresh_interval_sec` (quota types read official pages; API types call official APIs)
2. **Snapshot**: every successful fetch → `app/data/snapshots/<provider>.json` (30-day retention)
3. **Forecast**: 3-layer estimation from snapshots → "days left" with confidence
4. **Render**: main panel / mini widget / notifications; credentials DPAPI-encrypted (machine-bound)

## Installation

```bash
# Windows · Python 3.11+
git clone https://github.com/643048695/token-gauge.git
cd token-gauge
pip install -r requirements.txt
```

Copy `config.example.json` to `config.json` and fill in provider credentials (or use the UI's Providers page — saved instantly).

## Running

```bash
python main.py
```

Double-click the tray icon (green dot) to toggle the main panel; closing the panel hides to tray. Mini widget lives bottom-right; toggle/size/opacity in Appearance.

## Configuration (config.json)

| Field | Description |
|---|---|
| `providers.<id>.config` | per-provider credentials (opencode-go: workspace_id + auth_cookie; api types: api_key + base_url) |
| `refresh_interval_sec` | fetch interval (default 300, 60–1800) |
| `theme` / `opacity` / `notify` / `window` | theme, transparency, notifications, window geometry |
| `display` | unit mode (auto/usd/cny/tokens), fx rate |
| `diy.modules` | per-card module toggles (meta_grid / token_est / chart / …) |

## Testing

```bash
python -m unittest test_achievements test_unit   # 36 unit tests
python test_integration.py                        # 21 integration assertions
```

CI runs on every push (windows-latest).

## Architecture

```
main.py              entry: tray + windows + js_api (pywebview)
app/kernel.py        scheduler: parallel fetch, cache, stale marking
app/settings.py      config read/write (deep-merge defaults, dot paths)
app/notifier.py      notifications (tray/system/off + dedup)
app/themes.py        5 themes + build_css
app/achievements.py  37 achievements
app/providers/       provider plugins (base.py + opencode_go.py / api_provider.py)
app/store.py         per-provider snapshots (30 days)
ui/main_panel.html   main panel (single inlined file)
ui/mini_widget.html  mini widget
ui/index.html        onboarding wizard
cli.py               CLI for agents
```

---

## 注意 / Notes

- 只读访问 opencode.ai 官方页面，不上传数据到第三方 / Read-only access to opencode.ai; no third-party uploads
- auth_cookie 是账号钥匙，勿外传 / auth_cookie is your account key — never share it
- 凭据仅保存在本机 `config.json`（已 gitignore）/ Credentials live only in local `config.json` (gitignored)

## 免责声明 / Disclaimer

- **非官方工具** / Unofficial: not affiliated with OpenCode, DeepSeek or any vendor; brand names & icons belong to their owners
- **仅供学习** / For learning: the opencode-go adapter reads public pages read-only; comply with third-party ToS; use at your own risk
- MIT licensed, no warranty / MIT 许可，不提供任何担保

## License

[MIT](LICENSE)
