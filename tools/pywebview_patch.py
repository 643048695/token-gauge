# -*- coding: utf-8 -*-
"""pywebview 透明窗口 patch（重装 pywebview 后重跑本脚本恢复）

问题：pywebview+WebView2+Win11 下 transparent 只设 DefaultBackgroundColor，
窗口层不透明（显示主题色/深色块）。WS_EX_NOREDIRECTIONBITMAP 必须
在窗口创建时（CreateWindowEx 阶段）设置，后期 SetWindowLong 无效。

方案：patch winforms.py 的 BrowserForm，override CreateParams
（transparent 时 ExStyle |= WS_EX_NOREDIRECTIONBITMAP）→
WebView2 DirectComposition 直接合成 DWM → 页面透明区域真透明。
"""
import os
import sys

WV = os.path.join(os.path.dirname(sys.executable), "Lib", "site-packages", "webview", "platforms", "winforms.py")


def main():
    if not os.path.exists(WV):
        print("未找到 pywebview winforms.py:", WV)
        return 1
    src = open(WV, encoding="utf-8").read()
    if "OC-GO patch" in src:
        print("已打过 patch，跳过")
        return 0
    old = """    class BrowserForm(WinForms.Form):
        def __init__(self, window, cache_dir):
            super().__init__()"""
    new = """    class BrowserForm(WinForms.Form):
        @property
        def CreateParams(self):
            # [OC-GO patch] 透明窗口：创建时即带 WS_EX_NOREDIRECTIONBITMAP（Win10 1809+）
            cp = WinForms.Form.CreateParams.fget(self)
            if getattr(self, "pywebview_window", None) and self.pywebview_window.transparent:
                cp.ExStyle = int(cp.ExStyle) | 0x00200000
            return cp

        def __init__(self, window, cache_dir):
            super().__init__()"""
    assert old in src, "BrowserForm 定位失败，pywebview 版本可能已变"
    src = src.replace(old, new, 1)
    open(WV, "w", encoding="utf-8", newline="").write(src)
    print("winforms.py patched OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
