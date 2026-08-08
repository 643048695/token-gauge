# -*- coding: utf-8 -*-
"""独立服务模块：迷你窗拖拽控制器 + 数据推送器（从 main.py 拆出）。

- DragController：Python 轮询鼠标位置实现拖拽/缩放（绕开 WebView2 拖动事件断流）
- Pusher：主进程主动向迷你窗推送视图数据（绕开第二窗口 js_api 不可靠问题）
"""
import ctypes
import ctypes.wintypes
import threading
import time

import logging

log = logging.getLogger(__name__)


class DragController:
    """迷你窗拖拽/缩放（move/resizeX/resizeY/resize）。

    方案：JS mousedown → drag_start 记录起点 → 后台线程每 20ms 读真实鼠标位置
    （GetCursorPos 物理像素）SetWindowPos 移动/改尺寸；GetAsyncKeyState 检测左键
    松开即停；结束写回配置。完全不依赖 WebView2 鼠标事件流。
    """

    # Win32 系统拖拽命中区域（native_drag 用）
    HITS = {"caption": 2, "right": 11, "bottom": 15, "bottomright": 17}

    def __init__(self, app):
        self._app = app          # DashboardApp 引用（取 mini_window/kernel 等）
        self._drag = None        # 当前拖拽会话起点数据
        self._drag_stop_ev = None

    # ------------------------------------------------------------ 入口

    def drag_start(self, kind, target="mini"):
        """JS mousedown：启动轮询拖拽（kind: move/resizeX/resizeY/resize）。target: mini/main。"""
        win = self._app.mini_window if target == "mini" else self._app.main_window
        if win is None or kind not in ("move", "resizeX", "resizeY", "resize"):
            return {"ok": False, "message": "参数错误"}
        try:
            hwnd = self._app._window_hwnd(win)
            if not hwnd:
                return {"ok": False, "message": "无句柄"}
            pt = ctypes.wintypes.POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
            rect = ctypes.wintypes.RECT()
            ctypes.windll.user32.GetWindowRect(ctypes.c_void_p(hwnd), ctypes.byref(rect))
            self._drag_stop_ev = threading.Event()
            self._drag = {
                "kind": kind, "hwnd": hwnd,
                "cx": pt.x, "cy": pt.y,
                "x0": rect.left, "y0": rect.top,
                "w0": rect.right - rect.left, "h0": rect.bottom - rect.top,
            }
            log.info(f"drag_start: kind={kind} cursor=({pt.x},{pt.y}) "
                     f"rect=({rect.left},{rect.top},{rect.right-rect.left}x{rect.bottom-rect.top})")
            threading.Thread(target=self._drag_loop, daemon=True).start()
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def _drag_loop(self):
        d = self._drag
        SWP_NOSIZE, SWP_NOMOVE = 0x0001, 0x0002
        SWP_NOZORDER, SWP_NOACTIVATE = 0x0004, 0x0010
        SWP_NOZORDER2 = 0x0004 | 0x0010
        VK_LBUTTON = 0x01
        frames = 0
        while not self._drag_stop_ev.wait(0.02):
            # 系统级按键检测：左键松开即停止（不依赖 WebView2 mouseup 事件）
            if not (ctypes.windll.user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000):
                break
            try:
                pt = ctypes.wintypes.POINT()
                ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
                dx = pt.x - d["cx"]
                dy = pt.y - d["cy"]
                kind = d["kind"]
                if kind == "move":
                    ctypes.windll.user32.SetWindowPos(
                        ctypes.c_void_p(d["hwnd"]), None,
                        d["x0"] + dx, d["y0"] + dy, 0, 0,
                        SWP_NOSIZE | SWP_NOZORDER2)
                else:
                    w, h = d["w0"], d["h0"]
                    if kind == "resizeX":
                        w = max(160, min(600, d["w0"] + dx))
                    elif kind == "resizeY":
                        h = max(100, min(400, d["h0"] + dy))
                    else:
                        w = max(160, min(600, d["w0"] + dx))
                        h = max(100, min(400, d["h0"] + dy))
                    ctypes.windll.user32.SetWindowPos(
                        ctypes.c_void_p(d["hwnd"]), None, 0, 0, w, h,
                        SWP_NOMOVE | SWP_NOZORDER2)
            except Exception as e:
                import traceback as _tb
                log.warning('drag_loop 异常: %s\n%s' % (e, _tb.format_exc()))
            frames += 1
        log.info("drag_loop 结束: kind=%s frames=%d" % (d["kind"], frames))

    def drag_stop(self):
        ev = getattr(self, "_drag_stop_ev", None)
        if ev:
            ev.set()
        # 写回最终尺寸到配置（若发生 resize）
        d = getattr(self, "_drag", None)
        if d and d.get("kind") != "move":
            try:
                rect = ctypes.wintypes.RECT()
                ctypes.windll.user32.GetWindowRect(ctypes.c_void_p(d["hwnd"]), ctypes.byref(rect))
                w = rect.right - rect.left
                h = rect.bottom - rect.top
                scale = self._app._get_scale(d["hwnd"]) or 1.0
                settings = self._app.kernel.get_settings()
                win = dict(settings.get("window") or {})
                win["mini_width"] = int(round(w / scale))
                win["mini_height"] = int(round(h / scale))
                self._app.kernel.save_settings({"window": win})
            except Exception:
                pass
        return {"ok": True}

    # ------------------------------------------------------------ 系统级拖拽

    def native_drag(self, hit, target="mini"):
        """Win32 原生系统拖拽（WM_NCLBUTTONDOWN + 命中区域）。target: main/mini。"""
        if hit not in self.HITS:
            return {"ok": False, "message": "参数错误"}
        win = self._app.main_window if target == "main" else self._app.mini_window
        if win is None:
            return {"ok": False, "message": "窗口不存在"}
        try:
            hwnd = self._app._window_hwnd(win)
            if not hwnd:
                return {"ok": False, "message": "无句柄"}
            WM_NCLBUTTONDOWN = 0x00A1
            log.info(f"native_drag: hit={hit} hwnd={hwnd}")
            r = ctypes.windll.user32.SendMessageW(
                ctypes.c_void_p(hwnd), WM_NCLBUTTONDOWN, self.HITS[hit], 0)
            log.info(f"native_drag: SendMessage 返回 {r}")
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "message": str(e)}


class Pusher:
    """主动向迷你窗推送视图数据（绕开第二窗口 js_api 不可靠）。"""

    def __init__(self, app):
        self._app = app

    def start(self):
        """启动推送线程（8 秒周期）。"""
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while not self._app._stop_push.wait(8):
            self.push_once()

    def push_once(self):
        try:
            if self._app.mini_window is not None:
                import json as _json
                v = self._app.kernel.get_view()
                js = _json.dumps(v, ensure_ascii=False)
                self._app.mini_window.evaluate_js(
                    "window.__pushView && window.__pushView(%s)" % js)
                log.info("MINI-PUSH ok bytes=%d", len(js))
        except Exception as _e:
            log.warning("MINI-PUSH fail: %s", _e)
