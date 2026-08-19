@echo off
setlocal
chcp 65001 >nul
title Сборка 3DE Electrical Utility

echo ============================================================
echo   СБОРКА 3DE Electrical Utility.exe
echo ============================================================
echo.

where py >nul 2>nul
if errorlevel 1 (
  echo [ОШИБКА] Python не найден.
  echo Установите Python 3.11 или 3.12 x64 с python.org,
  echo включив Add Python to PATH, затем запустите этот BAT снова.
  echo.
  pause
  exit /b 1
)

echo [1/4] Создание среды сборки...
if not exist .venv_build (
  py -3 -m venv .venv_build
  if errorlevel 1 goto :error
)

call .venv_build\Scripts\activate.bat
if errorlevel 1 goto :error

echo [2/4] Установка зависимостей...
python -m pip install --upgrade pip
if errorlevel 1 goto :error

python -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo [3/4] Сборка EXE...
python -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --windowed ^
  --name "3DE_Electrical_Utility_v5" ^
  --collect-all ezdxf ^
  --collect-all pymupdf ^
  "3DE_Electrical_Utility.pyw"

if errorlevel 1 goto :error

echo [4/4] Готово.
echo.
echo EXE находится здесь:
echo   %CD%\dist\3DE_Electrical_Utility_v5.exe
echo.
explorer "%CD%\dist"
pause
exit /b 0

:error
echo.
echo [ОШИБКА] Сборка не завершена.
echo Посмотрите сообщения выше.
pause
exit /b 1
