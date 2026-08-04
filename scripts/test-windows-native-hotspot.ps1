$ErrorActionPreference = "Stop"
Write-Host "CYBERHOTSPOT // WINDOWS NATIVE MOBILE HOTSPOT TEST" -ForegroundColor Magenta
Write-Host "Legacy Hosted Network is intentionally ignored." -ForegroundColor DarkGray
py -3 -c "from cyberhotspot.windows_native import probe; import json; print(json.dumps(probe(), indent=2))"
