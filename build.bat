@echo off
rem pdf2png GUI を exe 化する (Windows 用)
cd /d %~dp0
python -m pip install --upgrade pymupdf pyinstaller || goto :error
python -m PyInstaller --noconfirm --clean --onefile --windowed --name pdf2png --exclude-module pymupdf.layout --exclude-module onnxruntime pdf2png_gui.py || goto :error
echo.
echo 完了: dist\pdf2png.exe
pause
exit /b 0
:error
echo ビルドに失敗しました。
pause
exit /b 1
