@echo off
rem Builds a standalone "Full SBS 3D Converter.exe" (no Python needed to run it afterwards).
cd /d "%~dp0"
py -m pip install --upgrade pyinstaller || python -m pip install --upgrade pyinstaller
py -m PyInstaller --noconfirm --onefile --windowed --icon glasses.ico --name "Full SBS 3D Converter" fsbs_converter.py || python -m PyInstaller --noconfirm --onefile --windowed --icon glasses.ico --name "Full SBS 3D Converter" fsbs_converter.py
copy /y "dist\Full SBS 3D Converter.exe" . >nul
echo.
echo Done: "Full SBS 3D Converter.exe" is in this folder. Keep the ffmpeg and FRIM folders next to it.
pause
