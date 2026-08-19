@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Build 3DE Electrical Utility

echo ============================================================
echo   BUILD 3DE Electrical Utility.exe
echo ============================================================
echo.

set "PYCMD="

REM Prefer Python Launcher because Windows Store may hijack "python".
py -3.11 --version >nul 2>nul
if not errorlevel 1 set "PYCMD=py -3.11"

if not defined PYCMD (
  py -3 --version >nul 2>nul
  if not errorlevel 1 set "PYCMD=py -3"
)

if not defined PYCMD (
  python --version >nul 2>nul
  if not errorlevel 1 set "PYCMD=python"
)

if not defined PYCMD goto NO_PYTHON

echo Python command:
%PYCMD% --version
echo.

echo [1/4] Creating build virtual environment...
if not exist ".venv_build\Scripts\python.exe" %PYCMD% -m venv ".venv_build"
if errorlevel 1 goto ERROR

echo.
echo [2/4] Installing dependencies...
".venv_build\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto ERROR
".venv_build\Scripts\python.exe" -m pip install -r "requirements.txt"
if errorlevel 1 goto ERROR

echo.
echo [3/4] Building EXE...
".venv_build\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --windowed --name "3DE_Electrical_Utility_v5" --collect-all ezdxf --collect-all pymupdf "3DE_Electrical_Utility.pyw"
if errorlevel 1 goto ERROR

echo.
echo [4/4] BUILD COMPLETE
echo.
echo EXE:
echo "%CD%\dist\3DE_Electrical_Utility_v5.exe"
echo.
if exist "%CD%\dist\3DE_Electrical_Utility_v5.exe" explorer "%CD%\dist"
pause
exit /b 0

:NO_PYTHON
echo.
echo ERROR: Python 3.11/3.x was not found.
echo.
echo Test these commands manually:
echo   py -3.11 --version
echo   py --version
echo.
echo If "py" works, send me the output.
echo If neither works, reinstall Python 3.11 x64 and enable:
echo   Add python.exe to PATH
echo   Install launcher for all users
echo.
pause
exit /b 1

:ERROR
echo.
echo ERROR: Build failed.
echo See the messages above.
echo.
pause
exit /b 1
