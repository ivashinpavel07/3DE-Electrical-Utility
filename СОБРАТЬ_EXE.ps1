$ErrorActionPreference = "Stop"

Write-Host "Сборка 3DE Electrical Utility.exe" -ForegroundColor Cyan

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python Launcher (py.exe) не найден. Установите Python 3.11/3.12 x64."
}

if (-not (Test-Path ".venv_build")) {
    py -3 -m venv .venv_build
}

& ".\.venv_build\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv_build\Scripts\python.exe" -m pip install -r requirements.txt
& ".\.venv_build\Scripts\python.exe" -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name "3DE_Electrical_Utility_v5" `
    --collect-all ezdxf `
    --collect-all pymupdf `
    "3DE_Electrical_Utility.pyw"

Write-Host ""
Write-Host "Готово: dist\3DE_Electrical_Utility_v5.exe" -ForegroundColor Green
Start-Process explorer.exe ".\dist"
