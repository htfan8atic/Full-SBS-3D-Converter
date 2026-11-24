@echo off
rem Builds a standalone "Full 3D FSBS and MVC Converter.exe" (no Python needed to run it afterwards).
cd /d "%~dp0"
py -m pip install --upgrade pyinstaller || python -m pip install --upgrade pyinstaller
py -m PyInstaller --noconfirm --onefile --windowed --icon glasses.ico --name "Full 3D FSBS and MVC Converter" fsbs_converter.py || python -m PyInstaller --noconfirm --onefile --windowed --icon glasses.ico --name "Full 3D FSBS and MVC Converter" fsbs_converter.py
copy /y "dist\Full 3D FSBS and MVC Converter.exe" . >nul
echo.
echo Done: "Full 3D FSBS and MVC Converter.exe" is in this folder. Keep the ffmpeg and FRIM folders next to it.
pause
