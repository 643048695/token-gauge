"""OC-GO Dashboard 入口：托盘 + 主面板 + 迷你窗（v0.2 多模块架构）。

职责（Agent D，契约 §5/§6）：
- 从 app.settings 读取 config，实例化 app.kernel.Kernel 并注入 js_api
- 主面板（ui/main_panel.html，frameless）为默认入口，关闭 = 隐藏到托盘
- 迷你窗（ui/mini_widget.html，transparent on_top）可按 config 开关/定位/调透明度
- 托盘：双击切换主面板显隐；右键菜单含 打开主面板 / 显示迷你窗 / 立即刷新 / 退出
- 单实例锁（端口 48321）、workarea 定位、Win32 透明度 fallback

用法：
  python main.py            正常启动（主面板 + 迷你窗 + 托盘）
  python main.py --once     冒烟测试：抓取一次并打印 get_view() JSON
"""
import ctypes
import json
import os
import socket
import sys
import threading
import time

import webview

from app.kernel import Kernel
from app.window_ops import DragController, Pusher
from app.settings import load as load_settings

# 主面板用 CSS 拖拽区（#titlebar），迷你窗用顶部拖拽区，避免 easy_drag 拦截滑条/把手等交互控件
webview.settings['DRAG_REGION_SELECTOR'] = '#titlebar, .pywebview-drag-region'
webview.settings['DRAG_REGION_DIRECT_TARGET_ONLY'] = True

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCK_PORT = 48321  # 单实例锁端口
UI_STATE_FILE = os.path.join(BASE_DIR, ".ui_state.json")

# 运行日志（pythonw 无控制台，写文件便于诊断）
import logging as _logging
_LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(_LOG_DIR, exist_ok=True)
_logging.basicConfig(
    filename=os.path.join(_LOG_DIR, "app.log"),
    level=_logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    encoding="utf-8",
)
log = _logging.getLogger("oc-go")


def read_ui_state():
    """读取界面显隐状态文件；失败返回 None（调用方应保持现状）。"""
    try:
        with open(UI_STATE_FILE, encoding="utf-8") as f:
            import json as _json
            st = _json.load(f)
        return {"main_hidden": bool(st.get("main_hidden")),
                "mini_hidden": bool(st.get("mini_hidden"))}
    except Exception:
        return None

# 模块级持有锁 socket：socket 对象不允许动态加属性保活，必须靠引用持有
_lock_socket = None


def single_instance():
    """尝试占用锁端口；失败说明已有实例在跑。"""
    global _lock_socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", LOCK_PORT))
        s.listen(1)
        _lock_socket = s
        return True
    except OSError:
        s.close()
        return False


def workarea():
    """返回 (width, height) 工作区尺寸（排除任务栏）。非 Windows 给保守默认值。"""
    if os.name != "nt":
        return 1920, 1040

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", ctypes.c_long), ("top", ctypes.c_long),
            ("right", ctypes.c_long), ("bottom", ctypes.c_long),
        ]

    r = RECT()
    ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(r), 0)
    return r.right - r.left, r.bottom - r.top


class _Api:
    """pywebview JS API：契约 §5 全部方法 + hide_window。"""

    def __init__(self, app):
        self._app = app

    def get_view(self):
        return self._app.kernel.get_view()

    def refresh_now(self, provider_id=None):
        self._app.kernel.refresh_now(provider_id)
        # 手动刷新后立即推送迷你窗（数据同步不等 8s 轮询）
        try:
            if self._app.pusher:
                self._app.pusher.push_once()
        except Exception:
            pass
        return {"refreshing": True}

    def mini_ping(self, tag):
        """迷你窗诊断探针：前端上报桥状态/按钮点击（记日志，便于定位真实环境问题）。"""
        log.info("MINI-PROBE %s", str(tag)[:160])
        return {"ok": True}

    def get_settings(self):
        return self._app.kernel.get_settings()

    def save_settings(self, patch):
        result = self._app.kernel.save_settings(patch)
        # kernel 返回包装结构 {"ok", "settings": new_cfg}，解包取真实配置
        settings = result.get("settings") if isinstance(result, dict) else result
        # 联动迷你窗：开关 / 尺寸角落 / 透明度 分开处理，互不干扰
        if "mini_widget_enabled" in patch:
            self._app.sync_mini_window(settings)
        if "window" in patch:
            self._app.apply_mini_geometry(settings)
        if "opacity" in patch:
            # 透明度只作用于迷你窗（主面板透明度已取消）
            self._app.apply_opacity(self._app.mini_window,
                                    settings.get("opacity", {}).get("mini", 0.92))
        # 主题/供应商变化后立即推送给迷你窗，让悬浮窗即时跟随
        if any(k in patch for k in ("theme", "providers")):
            self._app.pusher.push_once()
        # 成就：外观/语言行为检测
        try:
            if any(k in patch for k in ("theme", "display", "density", "diy", "notify",
                                        "mini_style", "opacity", "window", "currency", "order")):
                self._app.kernel.ach_event("appearance")
            if isinstance(patch.get("ui"), dict) and "lang" in patch["ui"]:
                self._app.kernel.ach_event("lang")
        except Exception:
            pass
        return {"ok": True, "settings": settings}

    def remove_provider(self, pid):
        """删除供应商实例。"""
        return self._app.kernel.remove_provider(pid)

    def refresh_provider(self, pid):
        """立即抓取单个供应商。"""
        return self._app.kernel.refresh_provider(pid)

    def test_provider(self, pid):
        # 异步测试：立即返回，避免网络请求阻塞 UI 线程（"点了显示延迟"）
        self._app._test_threads[pid] = True
        threading.Thread(target=self._run_test_bg, args=(pid,), daemon=True).start()
        return {"running": True, "pid": pid}

    def _run_test_bg(self, pid):
        import time as _t
        try:
            _t0 = _t.time()
            result = self._app.kernel.test_provider(pid)
            _latency = int((_t.time() - _t0) * 1000)
            self._app._test_results[pid] = {
                "ok": bool(result.get("ok")),
                "message": result.get("message", ""),
                "latency_ms": _latency,
            }
        except Exception as e:
            self._app._test_results[pid] = {"ok": False, "message": f"测试异常: {e}",
                                            "latency_ms": None}

    def test_provider_result(self, pid):
        r = self._app._test_results.get(pid)
        if r is None:
            return {"done": False}
        return {"done": True, "ok": r["ok"], "message": r["message"],
                "latency_ms": r.get("latency_ms")}

    def test_provider_config(self, ptype, config, token):
        """引导页：测试一个「还没保存」的供应商配置（异步，前端按 token 轮询结果）。"""
        key = "cfg:" + str(token)
        self._app._test_threads[key] = True
        threading.Thread(target=self._run_test_cfg_bg,
                         args=(ptype, config, key), daemon=True).start()
        return {"running": True, "token": token}

    def _run_test_cfg_bg(self, ptype, config, key):
        try:
            _t0 = time.time()
            result = self._app.kernel.test_provider_config(ptype, config)
            _latency = int((time.time() - _t0) * 1000)
            self._app._test_results[key] = {
                "ok": bool(result.get("ok")),
                "message": result.get("message", ""),
                "latency_ms": _latency,
            }
        except Exception as e:
            self._app._test_results[key] = {"ok": False,
                                            "message": f"测试异常: {e}",
                                            "latency_ms": None}

    def test_provider_config_result(self, token):
        r = self._app._test_results.get("cfg:" + str(token))
        if r is None:
            return {"done": False}
        return {"done": True, "ok": r["ok"], "message": r["message"],
                "latency_ms": r.get("latency_ms")}

    def get_achievements(self):
        return self._app.kernel.achievements_state()

    def ach_event(self, name, value=None):
        return self._app.kernel.ach_event(name, value)

    def get_provider_types(self):
        return self._app.kernel.get_provider_types()

    def get_styles(self):
        return self._app.kernel.get_styles()

    def notify_test(self):
        settings = self._app.kernel.get_settings()
        method = settings.get("notify", {}).get("method", "tray")
        self._app.kernel.notifier.notify(method, "OC-GO 测试通知", "通知通道工作正常")
        return {"ok": True}

    def get_theme_css(self):
        view = self._app.kernel.get_view()
        settings = view.get("settings") or {}
        theme_id = settings.get("theme", {}).get("id", "paper")
        return {"css": view.get("theme_css", ""), "theme_id": theme_id}

    def resize_mini(self, w, h, save=False):
        return self._app.resize_mini(w, h, save)

    def move_mini(self, x, y):
        """JS 拖拽回调：把迷你窗移到绝对坐标 (x,y)。"""
        ok = self._app._win32_move(self._app.mini_window, x, y)
        return {"ok": bool(ok)}

    def move_mini_by(self, dx, dy):
        """JS 拖拽回调（增量）：基于当前物理位置 + 屏幕像素增量移动。"""
        ok = self._app.move_mini_by(dx, dy)
        return {"ok": bool(ok)}

    def resize_mini_by(self, dw, dh, save=False):
        """JS 拖拽回调（增量）：基于当前物理尺寸 + 屏幕像素增量改尺寸。"""
        return self._app.resize_mini_by(dw, dh, save)

    def resize_mini_main(self, width):
        """主窗口滑条：按逻辑宽度等比改迷你窗尺寸（实时预览+写回）。"""
        return self._app.resize_mini_main(width)

    def drag_start(self, kind, target="mini"):
        """JS mousedown：启动 Python 鼠标轮询拖拽（kind: move/resizeX/resizeY/resize）。target: mini/main。"""
        return self._app.drag.drag_start(kind, target)

    def drag_stop(self):
        """JS mouseup：停止轮询拖拽并写回配置。"""
        return self._app.drag.drag_stop()

    def native_drag(self, hit, target="mini"):
        """JS mousedown：启动 Win32 原生系统拖拽（hit: caption/right/bottom/bottomright; target: main/mini）。"""
        return self._app.drag.native_drag(hit, target)

    def push_mini(self):
        """立即推送一次迷你窗数据（形态/设置切换后即时生效，不等 8 秒轮询）。"""
        try:
            if self._app.pusher:
                self._app.pusher.push_once()
            return {"ok": True}
        except Exception as e:
            log.warning(f"push_mini 异常: {e}")
            return {"ok": False, "message": str(e)}

    def hide_mini(self):
        """隐藏迷你悬浮窗（SW_HIDE；恢复走外观页迷你窗开关）。"""
        try:
            hwnd = self._app._window_hwnd(self._app.mini_window)
            if hwnd:
                import ctypes
                ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE
            return {"ok": True}
        except Exception as e:
            log.warning(f"hide_mini 异常: {e}")
            return {"ok": False, "message": str(e)}

    def minimize_main(self):
        """主窗口最小化（Win32 ShowWindow SW_MINIMIZE）。"""
        try:
            hwnd = self._app._window_hwnd(self._app.main_window)
            if not hwnd:
                return {"ok": False, "message": "无句柄"}
            import ctypes
            ctypes.windll.user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE
            return {"ok": True}
        except Exception as e:
            log.warning(f"minimize_main 异常: {e}")
            return {"ok": False, "message": str(e)}

    def maximize_main(self):
        """主窗口最大化/还原切换（Win32 IsZoomed + ShowWindow）。"""
        try:
            hwnd = self._app._window_hwnd(self._app.main_window)
            if not hwnd:
                return {"ok": False, "message": "无句柄"}
            import ctypes
            u32 = ctypes.windll.user32
            maxed = bool(u32.IsZoomed(hwnd))
            u32.ShowWindow(hwnd, 9 if maxed else 3)  # SW_RESTORE / SW_MAXIMIZE
            return {"ok": True, "maxed": not maxed}
        except Exception as e:
            log.warning(f"maximize_main 异常: {e}")
            return {"ok": False, "message": str(e)}

    def open_url(self, url):
        """用系统默认浏览器打开官网链接。"""
        try:
            import webbrowser
            webbrowser.open(url or "")
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def hide_window(self):
        self._app.hide_main()
        return {"ok": True}

    def enter_dashboard(self):
        """引导/索引页 → 主面板。

        返回主面板路径由前端 location 导航：js_api 线程里 load_url
        跨线程操作窗口会挂掉主窗口（WinForms 限制，与 drag 同坑）。
        """
        try:
            # 相对路径：前端 location.href 在 file:// 下同目录导航
            return {"ok": True, "url": "main_panel.html"}
        except Exception as e:
            log.warning(f"enter_dashboard 异常: {e}")
            return {"ok": False, "message": str(e)}

    def replay_guide(self):
        """关于页「重看引导」：带 ?guide=1 强制引导页显示教学（返回 URL 由前端导航）。"""
        try:
            return {"ok": True, "url": "index.html?guide=1"}
        except Exception as e:
            log.warning(f"replay_guide 异常: {e}")
            return {"ok": False, "message": str(e)}


class DashboardApp:
    """窗口 / 托盘 / 透明度 / JS API 编排。"""

    def __init__(self, config):
        self.cfg = config
        self.kernel = Kernel(config)
        self.main_window = None
        self.mini_window = None
        self.tray_icon = None
        self.api = _Api(self)
        self._stop_push = threading.Event()
        self.drag = DragController(self)
        self.pusher = Pusher(self)
        self._test_threads = {}   # pid -> True（测试线程运行中）
        self._test_results = {}   # pid -> {ok, message}
        self._mini_hwnd = None    # 迷你窗句柄（loaded 时在主窗口线程获取，供外部使用）

    # ---------- 主面板 ----------
    def create_main_window(self):
        win = self.cfg.get("window", {})
        w = int(win.get("main_width", 920))
        h = int(win.get("main_height", 600))
        # 首次启动（未完成开屏引导）先加载引导页 index.html；
        # 完成后直接进主面板。后续索引页接入时在此扩展 start_page。
        ui_cfg = self.cfg.get("ui") or {}
        if not ui_cfg.get("onboarded"):
            url = os.path.join(BASE_DIR, "ui", "index.html")
        else:
            url = os.path.join(BASE_DIR, "ui", "main_panel.html")
        self.main_window = webview.create_window(
            "OC-GO Dashboard",
            url,
            width=w, height=h,
            frameless=True,
            js_api=self.api,
        )
        try:  # 关闭按钮（含 Alt+F4）统一走隐藏到托盘
            self.main_window.events.closing += self._on_main_closing
        except Exception as _e: log.debug(f"main.py 异常: {_e}")

    def _on_main_closing(self):
        """关闭按钮（含 Alt+F4）统一走隐藏到托盘。

        pywebview 6.2 closing 事件回调**无参数**（与 loaded 同坑）：签名带 event
        会抛 TypeError，隐藏逻辑不执行、窗口直接关闭。取消关闭 = handler 有返回值
        （返回 False 也会被收集进返回值集合，非空集合即触发 args.Cancel=True）。
        """
        try:
            self.hide_main()
        except Exception as _e: log.debug(f"main.py 异常: {_e}")
        return False

    def hide_main(self):
        """隐藏主窗口到托盘（成就 flag + 窗口隐藏）。"""
        try:
            self.kernel.ach_event("hide_tray")
        except Exception:
            pass
        if self.main_window is not None:
            try:
                self.main_window.hide()
            except Exception as e:
                log.warning(f'drag_loop 异常: {e}')

    def toggle_main(self):
        """托盘双击 / 菜单：主面板 show/hide 切换。"""
        if self.main_window is None:
            return
        try:
            if getattr(self.main_window, "visible", False):
                self.main_window.hide()
            else:
                self.main_window.show()
        except Exception:
            try:
                self.main_window.show()
            except Exception as _e: log.debug(f"main.py 异常: {_e}")

    # ---------- 迷你窗 ----------
    def create_mini_window(self, settings=None):
        settings = settings or self.cfg
        win = settings.get("window", {})
        w = int(win.get("mini_width", 340))
        h = int(win.get("mini_height", 180))
        # 缓存破坏：URL 带文件 mtime 版本号，WebView2 磁盘缓存旧页面时强制重新加载
        _mini_html = os.path.join(BASE_DIR, "ui", "mini_widget.html")
        try:
            _mini_html = "%s?v=%d" % (_mini_html, int(os.path.getmtime(_mini_html)))
        except Exception:
            pass
        self.mini_window = webview.create_window(
            "OC-GO Mini",
            _mini_html,
            width=w, height=h,
            frameless=True,
            # 不置顶：悬浮窗只待在桌面层，不盖在游戏/其他软件上层
            # 拖动走顶部 .pywebview-drag-region 拖拽区，避免整窗 easy_drag 拦截 resize 把手
            js_api=self.api,
        )
        try:
            self.kernel.ach_event("mini")
        except Exception:
            pass
        # 窗口创建后统一用 move 定位（move 的坐标换算已实测：输入 = 物理 / scale）
        try:
            self.mini_window.events.loaded += lambda: (
                self._on_mini_loaded(settings))
        except Exception as _e: log.debug(f"main.py 异常: {_e}")
        try:
            self.mini_window.events.loaded += lambda: self.apply_opacity(
                self.mini_window, settings.get("opacity", {}).get("mini", 0.92))
        except Exception as _e: log.debug(f"main.py 异常: {_e}")
        try:
            # 迷你窗不出现在任务栏：加 WS_EX_TOOLWINDOW、去 WS_EX_APPWINDOW
            self.mini_window.events.loaded += self._mini_toolwindow
        except Exception as _e: log.debug(f"main.py 异常: {_e}")



    def _monitor_work(self, hwnd):
        """窗口所在显示器的工作区（绝对坐标 left/top/width/height）。"""
        if os.name != "nt" or not hwnd:
            return None
        try:
            user32 = ctypes.windll.user32
            hmon = user32.MonitorFromWindow(ctypes.c_void_p(hwnd), 2)  # MONITOR_DEFAULTTONEAREST

            class MONITORINFO(ctypes.Structure):
                _fields_ = [
                    ("cbSize", ctypes.c_uint32),
                    ("rcMonitor", ctypes.wintypes.RECT),
                    ("rcWork", ctypes.wintypes.RECT),
                    ("dwFlags", ctypes.c_uint32),
                ]

            mi = MONITORINFO()
            mi.cbSize = ctypes.sizeof(MONITORINFO)
            if user32.GetMonitorInfoW(hmon, ctypes.byref(mi)):
                r = mi.rcWork
                return (r.left, r.top, r.right - r.left, r.bottom - r.top)
        except Exception as _e: log.debug(f"main.py 异常: {_e}")
        return None

    def _mini_position(self, settings, w=None, h=None):
        """计算迷你窗位置（返回 pywebview move 的输入坐标 = 物理目标 / DPI scale）。
        物理坐标：GetWindowRect 窗口尺寸 + rcWork 显示器工作区，直接相减。"""
        win = settings.get("window", {})
        margin = 12
        corner = win.get("mini_corner", "bottom-right")
        hwnd = self._window_hwnd(self.mini_window)
        # 窗口当前实际物理尺寸
        cw, ch = 0, 0
        if hwnd:
            try:
                user32 = ctypes.windll.user32
                rect = ctypes.wintypes.RECT()
                user32.GetWindowRect(ctypes.c_void_p(hwnd), ctypes.byref(rect))
                cw = rect.right - rect.left
                ch = rect.bottom - rect.top
            except Exception as _e: log.debug(f"main.py 异常: {_e}")
        if cw <= 0:
            cw, ch = 300, 170
        # 所在显示器物理工作区
        left, top, ww, wh = 0, 0, *(workarea())
        if hwnd:
            mw = self._monitor_work(hwnd)
            if mw:
                left, top, ww, wh = mw
        # 物理目标位置
        if corner == "top":
            px, py = left + (ww - cw) // 2, top + margin
        else:
            right = corner in ("top-right", "bottom-right")
            bottom = corner in ("bottom-left", "bottom-right")
            px = left + ww - cw - margin if right else left + margin
            py = top + wh - ch - margin if bottom else top + margin
        # pywebview move 输入 = 物理 / scale（实测 move(100,100) -> 窗口在物理 125）
        scale = self._get_scale(hwnd) or 1.0
        return round(px / scale), round(py / scale)

    def sync_mini_window(self, settings):
        """save_settings 后联动：开关只控制显示/隐藏（Win32 直调，跨线程安全）。"""
        enabled = bool(settings.get("mini_widget_enabled", True))
        if self.mini_window is None:
            return
        hwnd = self._window_hwnd(self.mini_window)
        log.info(f"sync_mini_window: enabled={enabled} hwnd={hwnd}")
        self._win32_show(hwnd, enabled)

    @staticmethod
    def _win32_move(window, x, y):
        """Win32 SetWindowPos 移动窗口（跨线程安全）。"""
        if os.name != "nt" or window is None:
            return False
        try:
            hwnd = DashboardApp._window_hwnd(window)
            if not hwnd:
                return False
            SWP_NOSIZE = 0x0001
            SWP_NOZORDER = 0x0004
            SWP_NOACTIVATE = 0x0010
            ctypes.windll.user32.SetWindowPos(
                ctypes.c_void_p(hwnd), None,
                int(x), int(y), 0, 0,
                SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE)
            return True
        except Exception:
            return False

    @staticmethod
    def _win32_show(hwnd, show):
        """ShowWindow 显示/隐藏窗口（跨线程安全）。"""
        if os.name != "nt" or not hwnd:
            return
        try:
            ctypes.windll.user32.ShowWindow(ctypes.c_void_p(hwnd), 5 if show else 0)
        except Exception as _e: log.debug(f"main.py 异常: {_e}")

    @staticmethod
    def _get_scale(hwnd):
        """获取窗口 DPI 缩放比例（物理像素 / 逻辑像素）。"""
        if os.name != "nt" or not hwnd:
            return 1.0
        try:
            dpi = ctypes.windll.user32.GetDpiForWindow(ctypes.c_void_p(hwnd))
            return (dpi / 96.0) if dpi else 1.0
        except Exception:
            return 1.0

    def apply_mini_geometry(self, settings):
        """应用迷你窗尺寸/角落变化。统一物理像素：config 逻辑尺寸 × DPI scale。"""
        if self.mini_window is None:
            return
        try:
            win = settings.get("window", {})
            nw_log = int(win.get("mini_width", 340))
            nh_log = int(win.get("mini_height", 180))
            hwnd = self._window_hwnd(self.mini_window)
            scale = self._get_scale(hwnd)
            phys_w = int(round(nw_log * scale))
            phys_h = int(round(nh_log * scale))
            cur = self.mini_window
            cw = getattr(cur, "width", None)   # 物理像素
            ch = getattr(cur, "height", None)
            log.info(f"apply_mini_geometry: 当前物理 {cw}x{ch}, 目标 {phys_w}x{phys_h} (scale={scale:.2f})")
            if cw is not None and ch is not None and (cw != phys_w or ch != phys_h):
                log.info(f"尺寸变化: 物理 {cw}x{ch} -> 逻辑 {nw_log}x{nh_log} 物理目标 {phys_w}x{phys_h}")
                # Win32 物理直设（SetWindowPos 跨线程安全，不依赖 pywebview 主线程）
                ok = self._win32_resize(cur, phys_w, phys_h)
                log.info(f"win32 resize: {ok}")
        except Exception as e:
            log.warning(f"apply_mini_geometry 异常: {e}")
        try:  # 按与创建一致的逻辑坐标重新定位（避免坐标系混用导致窗口被移出屏幕）
            win = settings.get("window", {})
            x, y = self._mini_position(settings)
            self.mini_window.move(x, y)
            # 诊断 + 自愈：查窗口真实状态，若被隐藏/失效则恢复
            time.sleep(0.2)
            hwnd2 = self._window_hwnd(self.mini_window)
            if hwnd2:
                user32 = ctypes.windll.user32
                vis = user32.IsWindowVisible(ctypes.c_void_p(hwnd2))
                rect = ctypes.wintypes.RECT()
                user32.GetWindowRect(ctypes.c_void_p(hwnd2), ctypes.byref(rect))
                log.info(f"mini 状态: visible={vis} rect=({rect.left},{rect.top},{rect.right},{rect.bottom})")
                if not vis:
                    log.warning("mini 窗口不可见，尝试恢复")
                    self.mini_window.show()
        except Exception as e:
            log.warning(f"mini 定位异常: {e}")
        except Exception as _e: log.debug(f"main.py 异常: {_e}")
        try:  # 仅角落变化时重新定位
            x, y = self._mini_position(settings)
            self.mini_window.move(x, y)
        except Exception as _e: log.debug(f"main.py 异常: {_e}")

    def resize_mini(self, w, h, save=False):
        """迷你窗实时改尺寸（拖拽条/把手用）；支持单维度（w 或 h 传 0 表示不改变）。
        save=True 时同步写回配置。统一物理像素。"""
        if self.mini_window is None:
            return {"ok": False, "message": "迷你窗未创建"}
        try:
            w = max(160, min(600, int(w))) if w else None
            h = max(100, min(400, int(h))) if h else None
            # 当前物理尺寸（GetWindowRect，与 win32 操作同坐标系）
            cw, ch = 0, 0
            hwnd = self._window_hwnd(self.mini_window)
            if hwnd:
                rect = ctypes.wintypes.RECT()
                ctypes.windll.user32.GetWindowRect(ctypes.c_void_p(hwnd), ctypes.byref(rect))
                cw = rect.right - rect.left
                ch = rect.bottom - rect.top
            if cw <= 0:
                cw, ch = 375, 212
            tw = w if w else cw
            th = h if h else ch
            if not self._win32_resize(self.mini_window, tw, th):
                try:
                    self.mini_window.resize(tw, th)
                except Exception as _e: log.debug(f"main.py 异常: {_e}")
            if save:
                settings = self.kernel.get_settings()
                win = dict(settings.get("window") or {})
                if hwnd:
                    scale = self._get_scale(hwnd) or 1.0
                    win["mini_width"] = int(round(tw / scale))
                    win["mini_height"] = int(round(th / scale))
                self.kernel.save_settings({"window": win})
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def resize_mini_by(self, dw, dh, save=False):
        """增量改尺寸：GetWindowRect 当前物理 + 屏幕像素增量（JS 侧只传差值，坐标系统一为物理）。"""
        if self.mini_window is None:
            return {"ok": False, "message": "迷你窗未创建"}
        try:
            hwnd = self._window_hwnd(self.mini_window)
            cw, ch = 0, 0
            if hwnd:
                rect = ctypes.wintypes.RECT()
                ctypes.windll.user32.GetWindowRect(ctypes.c_void_p(hwnd), ctypes.byref(rect))
                cw = rect.right - rect.left
                ch = rect.bottom - rect.top
            if cw <= 0:
                cw, ch = 375, 212
            tw = max(160, min(600, cw + int(dw))) if dw else cw
            th = max(100, min(400, ch + int(dh))) if dh else ch
            log.info(f"resize_mini_by: dw={dw} dh={dh} cw={cw} ch={ch} -> tw={tw} th={th} save={save}")
            if not self._win32_resize(self.mini_window, tw, th):
                try:
                    self.mini_window.resize(tw, th)
                except Exception as _e: log.debug(f"main.py 异常: {_e}")
            if save:
                settings = self.kernel.get_settings()
                win = dict(settings.get("window") or {})
                if hwnd:
                    scale = self._get_scale(hwnd) or 1.0
                    win["mini_width"] = int(round(tw / scale))
                    win["mini_height"] = int(round(th / scale))
                self.kernel.save_settings({"window": win})
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def move_mini_by(self, dx, dy):
        """增量移动：GetWindowRect 当前物理位置 + 屏幕像素增量。"""
        if self.mini_window is None:
            return {"ok": False, "message": "迷你窗未创建"}
        try:
            hwnd = self._window_hwnd(self.mini_window)
            if not hwnd:
                return {"ok": False, "message": "无句柄"}
            rect = ctypes.wintypes.RECT()
            ctypes.windll.user32.GetWindowRect(ctypes.c_void_p(hwnd), ctypes.byref(rect))
            nx = rect.left + int(dx)
            ny = rect.top + int(dy)
            log.info(f"move_mini_by: dx={dx} dy={dy} cur=({rect.left},{rect.top}) -> ({nx},{ny})")
            ok = self._win32_move(self.mini_window, nx, ny)
            return {"ok": bool(ok)}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def resize_mini_main(self, width):
        """主窗口尺寸滑条：逻辑宽度 → 物理像素，高度按当前宽高比等比，SetWindowPos + 写回配置。"""
        if self.mini_window is None:
            return {"ok": False, "message": "迷你窗未创建"}
        try:
            width = max(160, min(600, int(width)))
            hwnd = self._window_hwnd(self.mini_window)
            scale = self._get_scale(hwnd) or 1.0
            w = int(width * scale)
            # 当前物理尺寸求宽高比
            cw, ch = 375, 212
            if hwnd:
                rect = ctypes.wintypes.RECT()
                ctypes.windll.user32.GetWindowRect(ctypes.c_void_p(hwnd), ctypes.byref(rect))
                cw = rect.right - rect.left
                ch = rect.bottom - rect.top
            ratio = ch / cw if cw > 0 else 170.0 / 300.0
            h = max(100, min(400, int(w * ratio)))
            if hwnd:
                self._win32_resize(self.mini_window, w, h)
            # 写回配置（逻辑）
            settings = self.kernel.get_settings()
            win = dict(settings.get("window") or {})
            win["mini_width"] = width
            win["mini_height"] = int(round(h / scale))
            self.kernel.save_settings({"window": win})
            return {"ok": True, "width": width, "height": int(round(h / scale))}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    # ---------- Win32 原生系统拖拽（绕开 WebView2 事件流，系统级拖动/缩放） ----------
    HITS = {"caption": 2, "right": 11, "bottom": 15, "bottomright": 17}  # HTCAPTION/HTRIGHT/HTBOTTOM/HTBOTTOMRIGHT

    def _mini_toolwindow(self, *_a, **_k):
        """迷你窗不进任务栏：WS_EX_TOOLWINDOW。"""
        try:
            hwnd = self._window_hwnd(self.mini_window)
            if not hwnd:
                return
            import ctypes
            GWL_EXSTYLE = -20
            WS_EX_TOOLWINDOW = 0x00000080
            WS_EX_APPWINDOW = 0x00040000
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            style = (style | WS_EX_TOOLWINDOW) & ~WS_EX_APPWINDOW
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
            log.debug("mini 已设为 toolwindow（不出现在任务栏）")
        except Exception as e:
            log.warning(f"_mini_toolwindow 异常: {e}")

    def _on_mini_loaded(self, settings):
        """迷你窗 loaded 时（窗口线程）记录 hwnd 并定位到角落。"""
        try:
            self._mini_hwnd = self._window_hwnd(self.mini_window)
            log.info(f"迷你窗 loaded, hwnd={self._mini_hwnd}")
        except Exception as _e: log.debug(f"main.py 异常: {_e}")
        self._move_mini_to_corner(settings)
        # 窗口显示后 pywebview 可能重设位置：延迟重试归位（1.5s/3s 双保险）
        try:
            import threading as _th
            for _d in (1.5, 3.0):
                _th.Timer(_d, lambda: self._move_mini_to_corner(settings)).start()
        except Exception as _e: log.debug(f"main.py 异常: {_e}")

    def _move_mini_to_corner(self, settings):
        """把迷你窗移到角落（Win32 SetWindowPos 直设，物理坐标，不依赖 pywebview move）。"""
        try:
            hwnd = self._window_hwnd(self.mini_window)
            if not hwnd:
                return
            import ctypes
            u32 = ctypes.windll.user32
            rect = ctypes.wintypes.RECT()
            u32.GetWindowRect(hwnd, ctypes.byref(rect))
            cw = rect.right - rect.left
            ch = rect.bottom - rect.top
            if cw <= 0:
                cw, ch = 300, 170
            mw = self._monitor_work(hwnd)
            if mw:
                left, top, ww, wh = mw
            else:
                left = top = 0
                ww = u32.GetSystemMetrics(0)
                wh = u32.GetSystemMetrics(1)
            win = settings.get("window", {}) or {}
            corner = win.get("mini_corner", "bottom-right")
            margin = 12
            if corner == "top":
                px, py = left + (ww - cw) // 2, top + margin
            else:
                right = corner in ("top-right", "bottom-right")
                bottom = corner in ("bottom-left", "bottom-right")
                px = left + ww - cw - margin if right else left + margin
                py = top + wh - ch - margin if bottom else top + margin
            u32.SetWindowPos(hwnd, 0, px, py, 0, 0, 0x0001 | 0x0010)  # SWP_NOSIZE | SWP_NOZORDER
            log.info(f"mini 定位到 ({px},{py}) {cw}x{ch}")
        except Exception as e:
            log.warning(f"_move_mini_to_corner 异常: {e}")

    def destroy_mini(self):
        if self.mini_window is not None:
            try:
                self.mini_window.destroy()
            except Exception as _e: log.debug(f"main.py 异常: {_e}")
            self.mini_window = None

    def show_mini(self):
        if self.mini_window is None:
            if self.cfg.get("mini_widget_enabled", True):
                self.create_mini_window()
        else:
            self._win32_show(self._window_hwnd(self.mini_window), True)
            # JS 桥自检：显示时若 pywebview.api 未就绪则重载页面（修复按钮/数据失效）
            try:
                self.mini_window.evaluate_js(
                    "if(!(window.pywebview&&window.pywebview.api)){location.reload();}")
            except Exception:
                pass

    def hide_mini(self):
        if self.mini_window is not None:
            self._win32_show(self._window_hwnd(self.mini_window), False)

    # ---------- 透明度 ----------
    @staticmethod
    def apply_opacity(window, alpha):
        """Win32 窗口透明度：SetLayeredWindowAttributes（pywebview 6.2 无原生 opacity）。
        窗口需已创建（hwnd 可用）；非 layered 窗口先加 WS_EX_LAYERED。"""
        if alpha is None or os.name != "nt":
            return
        alpha = max(0.4, min(1.0, float(alpha)))
        try:
            hwnd = DashboardApp._window_hwnd(window)
            if not hwnd:
                return
            user32 = ctypes.windll.user32
            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x00080000
            style = user32.GetWindowLongW(ctypes.c_void_p(hwnd), GWL_EXSTYLE)
            if not (style & WS_EX_LAYERED):
                user32.SetWindowLongW(ctypes.c_void_p(hwnd), GWL_EXSTYLE,
                                      style | WS_EX_LAYERED)
            user32.SetLayeredWindowAttributes(
                ctypes.c_void_p(hwnd), 0, int(round(alpha * 255)), 0x02)
        except Exception as _e: log.debug(f"main.py 异常: {_e}")

    @staticmethod
    def _window_hwnd(window):
        """从 window.native 提取 HWND（WinForms 的 Handle 是 System.IntPtr，需 ToInt32()）。"""
        native = getattr(window, "native", None)
        if native is None:
            log.warning("_window_hwnd: native 为 None")
            return None
        for attr in ("Handle", "hwnd"):
            try:
                val = getattr(native, attr)
                if hasattr(val, "ToInt32"):   # System.IntPtr → int
                    hwnd = int(val.ToInt32())
                else:
                    hwnd = int(val() if callable(val) else val)
                log.info(f"_window_hwnd: native.{attr} = {hwnd}")
                return hwnd
            except Exception:
                continue
        try:
            hwnd = int(native)
            log.info(f"_window_hwnd: int(native) = {hwnd}")
            return hwnd
        except Exception:
            log.warning(f"_window_hwnd: 提取失败 (native type={type(native)})")
            return None

    @staticmethod
    def _win32_resize(window, w, h):
        """Win32 SetWindowPos 直接改窗口尺寸（不动窗口对象，最稳）。返回是否成功。"""
        if os.name != "nt" or window is None:
            return False
        try:
            hwnd = DashboardApp._window_hwnd(window)
            if not hwnd:
                log.warning(f"win32_resize: 无法提取 hwnd (native={getattr(window, 'native', None)})")
                return False
            SWP_NOMOVE = 0x0002
            SWP_NOZORDER = 0x0004
            SWP_NOACTIVATE = 0x0010
            r = ctypes.windll.user32.SetWindowPos(
                ctypes.c_void_p(hwnd), None, 0, 0,
                int(w), int(h),
                SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE)
            log.info(f"win32_resize: hwnd={hwnd} SetWindowPos 返回 {r}")
            return bool(r)
        except Exception as e:
            log.warning(f"win32_resize 异常: {e}")
            return False

    # ---------- 托盘 ----------
    def start_tray(self):
        import pystray
        from PIL import Image, ImageDraw

        def make_icon():
            img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
            d = ImageDraw.Draw(img)
            d.ellipse([6, 6, 58, 58], fill=(0, 255, 156, 255))
            d.ellipse([14, 14, 50, 50], fill=(8, 14, 12, 255))
            d.ellipse([24, 24, 40, 40], fill=(0, 255, 156, 255))
            return img

        def refresh_all(icon=None, item=None):
            self.kernel.refresh_now()

        def quit_app(icon=None, item=None):
            icon.stop()
            self.kernel.stop()
            for w in (self.mini_window, self.main_window):
                if w is not None:
                    try:
                        w.destroy()
                    except Exception as _e: log.debug(f"main.py 异常: {_e}")
            time.sleep(0.3)
            os._exit(0)

        menu = pystray.Menu(
            # default=True：托盘双击触发，行为 = 主面板显隐切换
            pystray.MenuItem("打开主面板",
                             lambda i, it: self.toggle_main(), default=True),
            pystray.MenuItem("显示迷你窗",
                             lambda i, it: self.show_mini()),
            pystray.MenuItem("隐藏迷你窗",
                             lambda i, it: self.hide_mini()),
            pystray.MenuItem("立即刷新", refresh_all),
            pystray.MenuItem("退出", quit_app),
        )
        self.tray_icon = pystray.Icon(
            "oc-go", make_icon(), "OC-GO Dashboard", menu)
        self.kernel.set_tray_icon(self.tray_icon)  # 注入给通知层（气泡用）
        self.tray_icon.run()

    def _ui_state_loop(self):
        """轮询界面状态文件，响应 main_hidden / mini_hidden 变化。
        读取失败时保持现状，绝不回退默认导致窗口弹回。"""
        last = read_ui_state() or {}
        cfg_marker = os.path.join(BASE_DIR, ".config_changed")
        while not self._stop_push.wait(3):
            try:
                # CLI 配置变更标记：热重载供应商并刷新
                if os.path.exists(cfg_marker):
                    try:
                        os.remove(cfg_marker)
                        self.kernel._rebuild_providers()
                        self.kernel.refresh_now()
                        self.pusher.push_once()
                        log.info("检测到 CLI 配置变更，已热重载供应商")
                    except Exception as _e:
                        log.warning(f"CLI 配置热重载失败: {_e}")
                cur = read_ui_state()
                if cur is None:
                    continue
                if cur == last:
                    continue
                last = cur
                if cur["mini_hidden"] and self.mini_window is not None:
                    try:
                        self.mini_window.hide()
                    except Exception as _e: log.debug(f"main.py 异常: {_e}")
                elif not cur["mini_hidden"] and self.mini_window is not None:
                    try:
                        self.mini_window.show()
                    except Exception as _e: log.debug(f"main.py 异常: {_e}")
                if cur["main_hidden"] and self.main_window is not None:
                    try:
                        self.main_window.hide()
                    except Exception as _e: log.debug(f"main.py 异常: {_e}")
                elif not cur["main_hidden"] and self.main_window is not None:
                    try:
                        self.main_window.show()
                    except Exception as _e: log.debug(f"main.py 异常: {_e}")
            except Exception as _e: log.debug(f"main.py 异常: {_e}")

    # ---------- 启动 ----------
    def _notify_main_failed(self, err: str):
        """WebView2/主面板启动失败的用户可见提示（QA #6：此前仅日志，用户无感知）。"""
        try:
            log.error("主面板启动失败: %s", err)
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                0,
                f"主面板启动失败：{err}\n\n请确认 WebView2 Runtime 已安装/可初始化（可在「设置-应用」查 Edge WebView2），修复后重启本程序。\n提示框关闭后应用仍在托盘运行。",
                "OC-GO 额度监控", 0x10)
        except Exception as _e:
            log.error("启动失败提示弹出异常: %s", _e)

    def run(self):
        self.kernel.start()
        self.kernel.check_achievements()   # 启动即检查成就（历史数据解锁 + 记录基线）
        try:
            self.create_main_window()
            # 迷你窗启动时总是创建（webview.start 前创建可靠），开关只控制显隐
            self.create_mini_window()
        except Exception as _e:
            # QA #6：窗口创建失败（如 CO_E_SERVER_EXEC_FAILURE）给用户可见提示，应用仍托盘运行
            self._notify_main_failed(str(_e))
        # 初始显隐状态（游戏/免打扰场景由 agent 或用户通过 .ui_state.json 控制）
        st = read_ui_state() or {}
        if st.get("main_hidden"):
            self.hide_main()
        if not self.cfg.get("mini_widget_enabled", True) or st.get("mini_hidden"):
            try:
                self.mini_window.hide()
            except Exception as _e: log.debug(f"main.py 异常: {_e}")
        threading.Thread(target=self.start_tray, daemon=True).start()
        self.pusher.start()
        threading.Thread(target=self._ui_state_loop, daemon=True).start()
        try:
            webview.start()  # 阻塞主线程；窗口隐藏时 WebView 继续运行（默认行为）
        except Exception as _e:
            # QA #6：WebView2 初始化失败（如 CO_E_SERVER_EXEC_FAILURE）用户可见提示
            self._notify_main_failed(str(_e))
            self._keep_alive_after_webview_fail()


    def _keep_alive_after_webview_fail(self):
        """WebView2 初始化失败后保持进程存活（托盘仍在，用户可托盘退出/稍后手动重启）。"""
        try:
            import time as _t
            while True:
                _t.sleep(5)
        except KeyboardInterrupt:
            pass


def run_once():
    """--once 冒烟：抓取一次并打印 get_view() JSON（无界面）。"""
    config = load_settings()
    kernel = Kernel(config)
    kernel.start()
    view = None
    deadline = time.time() + 30
    while time.time() < deadline:
        view = kernel.get_view()
        providers = view.get("providers") or {}
        if providers and any(p.get("fetched_at") for p in providers.values()):
            break
        time.sleep(0.5)
    kernel.stop()
    print(json.dumps(view or {"ok": False, "error": "30s 内未取到数据"},
                     ensure_ascii=False, indent=2))


def main():
    if "--once" in sys.argv:
        run_once()
        return

    if not single_instance():
        try:
            print("已有实例在运行，本进程退出。")
        except Exception as _e: log.debug(f"main.py 异常: {_e}")
        return

    config = load_settings()
    DashboardApp(config).run()


if __name__ == "__main__":
    main()
