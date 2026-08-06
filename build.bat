@echo off
chcp 65001 >nul
cd /d %~dp0
echo ============================================
echo   OC-GO Dashboard 一键打包
echo   产物: dist\OC-GO-Dashboard.exe
echo ============================================
echo.
echo [1/3] 安装依赖（含 PyInstaller）...
pip install -r requirements.txt pyinstaller
if errorlevel 1 (
  echo 依赖安装失败，请检查网络
  pause
  exit /b 1
)
echo.
echo [2/3] PyInstaller 打包（约 1-3 分钟）...
pyinstaller --noconfirm --clean --onefile --windowed ^
  --name "OC-GO-Dashboard" ^
  --add-data "ui;ui" ^
  --hidden-import webview ^
  --hidden-import webview.platforms.winforms ^
  --hidden-import webview.platforms.edgechromium ^
  --hidden-import pystray ^
  --hidden-import PIL ^
  main.py
if errorlevel 1 (
  echo 打包失败，见上方错误
  pause
  exit /b 1
)
echo.
echo [3/3] 完成！
echo   可执行文件: dist\OC-GO-Dashboard.exe
echo   说明: 首次运行会自动创建 config.json（在 exe 同目录）
echo   注意: 杀毒软件可能误报（PyInstaller 单文件常见），添加信任即可
pause
