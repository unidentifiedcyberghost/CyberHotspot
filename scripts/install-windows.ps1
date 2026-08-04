$ErrorActionPreference = "Stop"
Write-Host "CYBERHOTSPOT // WINDOWS INSTALLER" -ForegroundColor Magenta
py -3 --version
if ($LASTEXITCODE -ne 0) { throw "Python 3 is required." }
if (-not (Test-Path ".venv")) { py -3 -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -e ".[qr]"
Write-Host "Installation complete." -ForegroundColor Green
Write-Host "Run: .\.venv\Scripts\cyberhotspot.exe capabilities"
Write-Host "Run: .\.venv\Scripts\cyberhotspot-gui.exe"
