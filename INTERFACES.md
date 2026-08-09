# OC-GO Dashboard 接口契约 v1

> 并行开发对齐文件。所有 Agent 必须严格遵循本契约；与契约冲突的代码在统筹阶段会被修正。
> 项目根：仓库根目录（沙箱已授权读写）

## 0. 文件边界（禁区）

| 归属 | 文件 | 其他 Agent 禁止写入 |
|---|---|---|
| Agent A | `app/providers/base.py`、`app/providers/opencode_go.py`、`app/store.py` | B/C/D |
| Agent B | `app/kernel.py`、`app/settings.py`、`app/notifier.py` | A/C/D |
| Agent C | `ui/main_panel.html`（单文件，CSS/JS 全内联） | A/B/D |
| Agent D | `main.py`、`app/themes.py`、`ui/mini_widget.html` | A/B/C |
| 统筹方 | `config.json`、`INTERFACES.md`、`PLAN.md`、`README.md` | 所有 Agent |

旧文件 `fetcher.py / estimator.py / widget.html / hana-plugin/` 由统筹方在集成期清理，各 Agent 不得引用旧文件，一律 import 新模块。

## 1. config.json schema（统筹方已写好，B 的 settings.py 只读写此结构）

```json
{
  "providers": {
    "opencode-go": {
      "enabled": true,
      "name": "OpenCode Go",
      "config": { "workspace_id": "wrk_...", "auth_cookie": "Fe26.2**..." }
    }
  },
  "refresh_interval_sec": 300,
  "theme": { "id": "neon-green", "accent_custom": null },
  "opacity": { "main": 0.95, "mini": 0.92 },
  "window": { "main_width": 920, "main_height": 600, "mini_width": 300, "mini_height": 170, "mini_corner": "bottom-right" },
  "mini_widget_enabled": true,
  "density": "compact",
  "currency": "usd",
  "notify": {
    "method": "tray",
    "threshold": 80,
    "urgent": 95,
    "events": { "threshold": true, "urgent": true, "cookie_fail": true, "fetch_fail": true }
  },
  "start_with_windows": false
}
```

- `settings.py` 提供：`load() -> dict`（深合并默认值）、`save(patch: dict)`、`get(path)`（点路径读取）、`set(path, value)`。
- 未知键保留，不做删除；patch 是浅合并（顶层 dict 替换语义：patch 里的顶层 key 整体替换对应子 dict）。

## 2. Provider 抽象（app/providers/base.py，Agent A）

```python
class Provider:
    id: str          # 唯一标识，如 "opencode-go"
    name: str        # 显示名
    schema: list     # 配置字段定义：[{"key":"workspace_id","label":"工作区 ID","type":"text","secret":False}, ...]
    plan_name: str   # 套餐名，如 "Go"

    def __init__(self, config: dict): ...   # config 为该 provider 的配置 dict
    def fetch(self) -> dict: ...            # 抓取一次，返回标准结果（见下）
    def verify(self) -> dict: ...           # 测试连接：{"ok":bool,"message":str,"detail":dict}
```

**标准化结果（fetch 返回）**：
```json
{
  "provider": "opencode-go",
  "ok": true,
  "fetched_at": 1785930000,
  "cookie_valid": true,
  "plan_name": "Go",
  "limits": [
    {"id": "rolling", "label": "5h 滚动", "used_pct": 6, "reset_in_sec": 1409},
    {"id": "weekly",  "label": "每周",    "used_pct": 21, "reset_in_sec": 390376},
    {"id": "monthly", "label": "每月",    "used_pct": 40, "reset_in_sec": 1489940}
  ],
  "balance": {"currency": "USD", "amount": 0.0},
  "meta": {
    "today": {"delta_pct": 3.0, "delta_usd": 1.8, "base_label": "19:38", "since_midnight": false},
    "speed": {"hourly_pct": 0.3, "days_left": 8.2, "days_left_text": "8.2 天", "source": "today"},
    "monthly_limit_usd": 60.0,
    "used_usd": 24.0
  }
}
```

- `ok:false` 时仍返回完整结构，含 `error` 字符串与 `cookie_valid` 布尔；`limits` 可为空数组。
- `meta` 是 provider 特有的增值信息（今日用量、速度推算等），没有则为 `{}`。
- `opencode_go.py` 从旧 `fetcher.py` + `estimator.py` 迁移逻辑：抓取解析、快照（用 store.py）、今日用量、三层速度推算（趋势回归/今日/短时，见 PLAN.md 1.1）。
- `store.py`（Agent A）接口：`append(provider_id, result)`、`snapshots(provider_id, hours=720)`、`clear(provider_id)`。快照文件 `app/data/snapshots/{provider_id}.json`。

## 3. 内核（app/kernel.py，Agent B）

```python
class Kernel:
    def __init__(self, config: dict): ...          # 依据 config.providers 实例化所有 enabled provider
    def start(self): ...                            # 启动调度线程
    def stop(self): ...                             # 停止调度线程
    def get_view(self) -> dict: ...                 # 全视图（见下）
    def refresh_now(self, provider_id: str | None = None) -> None   # 异步触发抓取
    def test_provider(self, provider_id: str) -> dict               # 同步测试连接
    def get_settings(self) -> dict                  # 当前 config 全量（给前端）
    def save_settings(self, patch: dict) -> dict    # 合并且持久化，返回新 settings
```

**get_view() 全视图**：
```json
{
  "ok": true,
  "fetched_at": 1785930000,
  "refresh_interval_sec": 300,
  "providers": { "opencode-go": { ...标准化结果... } },
  "settings": { ...config 全量... },
  "theme_css": "字符串（CSS 变量）"
}
```

- `providers` 按 config 顺序排列；`settings` 与 `theme_css` 由 B 从 settings.py + themes.py 获取（import 自 Agent D 的 `app/themes.py`——B 只 import，不写）。
- 调度线程：每 `refresh_interval_sec` 遍历所有 enabled provider 并行（ThreadPool）fetch，成功/失败都更新缓存，并触发 notifier 判断（见下）。
- 失败缓存保留上次成功结果；`get_view()` 的 provider 结果带 `"stale": true` 标记（若上次成功超过 2 个周期）。
- `notifier.py`：`set_tray_icon(icon)`（由 D 注入）、`notify(method, title, body)`、`check(provider_id, result, prev_result, settings)`（阈值/失效/失败判断，内部去重，事件状态存内存）。`method`：`"tray"`（pystray icon.notify，缺 icon 时静默降级 print）/ `"system"`（try import winotify，失败降级 tray）/ `"off"`。

## 4. 主题（app/themes.py，Agent D）

```python
THEMES: dict  # {"neon-green": {"name":"霓虹绿","accent":"#00ff9c","accent2":"#00c9ff","bg":"rgba(8,14,12,0.92)","text":"#d8ffef","muted":"#7fa896","glow":"rgba(0,255,156,0.55)"}, ...}
# 预置至少 6 套：neon-green / neon-cyan / neon-purple / amber / crimson / ice-blue

def build_css(theme_id: str, accent_custom: str | None) -> str:
    # 返回 CSS 变量字符串，如 ":root{--accent:#00ff9c;...}"
    # accent_custom 非空时覆盖 accent 与 glow
```

## 5. js_api 契约（main_panel.html 与 mini_widget.html 调用）

所有方法返回 JSON 可序列化 dict。前端用 `window.pywebview.api.<method>(...)`（返回 Promise）。

| 方法 | 参数 | 返回 |
|---|---|---|
| `get_view()` | — | 全视图（见 §3） |
| `refresh_now()` | `provider_id?` | `{"refreshing": true}` |
| `get_settings()` | — | settings dict |
| `save_settings(patch)` | patch dict | `{"ok": true, "settings": {...}}` |
| `test_provider(pid)` | str | `{"ok": bool, "message": str}` |
| `notify_test()` | — | `{"ok": true}` |
| `get_theme_css()` | — | `{"css": "...", "theme_id": "..."}` |

`main.py`（D）创建窗口时 `js_api` 注入以上全部方法（kernel 实例来自 B 的 `Kernel(config)`）。

## 6. 窗口与托盘（main.py，Agent D）

- 主面板：`webview.create_window("OC-GO", "ui/main_panel.html", width=920, height=600, frameless=True, easy_drag=True, js_api=...)`。关闭按钮（html 内的 ×）调 `window.pywebview.api.hide_window()`；D 需在 js_api 中补充实现（返回 `{"ok":true}`，内部 `window.hide()`）。
- 迷你窗：`ui/mini_widget.html`，尺寸/角落按 config，`transparent=True`，只有第一个 enabled provider 的核心数据；外观页可关（save_settings 后 D 负责联动 show/hide）。
- 托盘：双击 → 显示主面板（若主面板不可见则 show，否则 hide）；右键菜单：打开主面板 / 显示迷你窗 / 立即刷新 / 退出。
- `themes.py` 的 `build_css` 注入方式：js_api 的 `get_view()` 已带 `theme_css`；HTML 加载后执行 `document.documentElement.insertAdjacentHTML('afterbegin', css)`。
- 单实例锁、workarea 右下角定位、透明窗口参数沿用旧 main.py 经验。

## 7. 验收清单（统筹方执行）

1. `python app/... ` 各模块无 import 错误
2. `python main.py --once` 输出多 provider 视图 JSON
3. 启动 GUI：主面板打开、数据渲染、主题切换、透明度、通知设置、迷你窗开关
4. 通知事件：cookie 失效 / 连续失败 场景模拟
5. 旧文件清理后整体可运行
