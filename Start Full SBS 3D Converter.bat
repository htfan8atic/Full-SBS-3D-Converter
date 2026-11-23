@echo off
cd /d "%~dp0"
where pyw >nul 2>nul && (start "" pyw "fsbs_converter.py" & exit /b)
where pythonw >nul 2>nul && (start "" pythonw "fsbs_converter.py" & exit /b)
echo Python was not found. Install it from https://www.python.org/downloads/ (tick "Add python.exe to PATH").
pause
