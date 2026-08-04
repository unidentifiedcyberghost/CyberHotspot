$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
Set-Location (Join-Path $PSScriptRoot "..\..")

$version = "2.8.0"
$root = Get-Location
$dist = Join-Path $root "dist"
$stage = Join-Path $dist "msix-stage"

Write-Host "CYBERHOTSPOT // WINDOWS MSIX BUILD" -ForegroundColor Magenta
Write-Host "Project: $root" -ForegroundColor DarkCyan

# IMPORTANT: use the active virtual environment instead of `py -3`.
# The previous build script ignored the user's activated .venv and installed
# packages into whichever global Python the launcher selected.
$pythonExe = $null
if ($env:VIRTUAL_ENV) {
    $candidate = Join-Path $env:VIRTUAL_ENV "Scripts\python.exe"
    if (Test-Path $candidate) { $pythonExe = $candidate }
}
if (-not $pythonExe) {
    $candidate = Join-Path $root ".venv\Scripts\python.exe"
    if (Test-Path $candidate) { $pythonExe = $candidate }
}
if (-not $pythonExe) {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { $pythonExe = $cmd.Source }
}
if (-not $pythonExe) {
    throw "Python was not found. Activate .venv or create it with: py -3 -m venv .venv"
}

$pyVersion = & $pythonExe -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
if ($LASTEXITCODE -ne 0) { throw "Unable to execute Python: $pythonExe" }
Write-Host "Python: $pyVersion" -ForegroundColor Cyan
Write-Host "Python executable: $pythonExe" -ForegroundColor DarkCyan

if ([version]$pyVersion -lt [version]"3.9") {
    throw "CyberHotspot requires Python 3.9 or newer. Found $pyVersion."
}

Remove-Item $stage -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $dist "CyberHotspot") -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $stage | Out-Null
New-Item -ItemType Directory -Force (Join-Path $stage "Assets") | Out-Null

Write-Host "[1/6] Installing build dependencies..." -ForegroundColor Yellow
& $pythonExe -m pip install --upgrade pip setuptools wheel
if ($LASTEXITCODE -ne 0) { throw "pip dependency installation failed." }
& $pythonExe -m pip install --upgrade "PyInstaller>=6.10" "PyQt5>=5.15" "psutil>=5.9" "qrcode[pil]>=7.4" "winrt-runtime==3.2.1" "winrt-Windows.Networking.Connectivity==3.2.1" "winrt-Windows.Networking.NetworkOperators==3.2.1" "winrt-Windows.Foundation==3.2.1"
if ($LASTEXITCODE -ne 0) { throw "CyberHotspot dependency installation failed." }

Write-Host "[2/6] Verifying Windows Runtime imports..." -ForegroundColor Yellow
& $pythonExe -c "from winrt.windows.networking.connectivity import NetworkInformation; from winrt.windows.networking.networkoperators import NetworkOperatorTetheringManager, NetworkOperatorTetheringAccessPointConfiguration; print('PyWinRT imports: OK')"
if ($LASTEXITCODE -ne 0) { throw "PyWinRT imports failed. See the error above." }
& $pythonExe -c "from PyQt5 import QtWidgets; print('PyQt5 import: OK')"
if ($LASTEXITCODE -ne 0) { throw "PyQt5 import failed. See the error above." }

Write-Host "[3/6] Building PyInstaller application..." -ForegroundColor Yellow
$pyiArgs = @(
    "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed",
    "--name", "CyberHotspot",
    "--paths", $root.Path,
    "--add-data", "cyberhotspot\assets;cyberhotspot\assets",
    "--hidden-import", "winrt.system",
    "--hidden-import", "winrt.windows.foundation",
    "--hidden-import", "winrt.windows.networking.connectivity",
    "--hidden-import", "winrt.windows.networking.networkoperators",
    "--collect-all", "winrt.windows.foundation",
    "--collect-all", "winrt.windows.networking.connectivity",
    "--collect-all", "winrt.windows.networking.networkoperators",
    "cyberhotspot\gui.py"
)
& $pythonExe @pyiArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller failed. Re-run the command shown below to capture the complete diagnostic:" -ForegroundColor Red
    Write-Host "& `"$pythonExe`" -m PyInstaller --clean --windowed --name CyberHotspot --paths `"$root`" --add-data `"cyberhotspot\assets;cyberhotspot\assets`" --hidden-import winrt.system --hidden-import winrt.windows.foundation --hidden-import winrt.windows.networking.connectivity --hidden-import winrt.windows.networking.networkoperators --collect-all winrt.windows.foundation --collect-all winrt.windows.networking.connectivity --collect-all winrt.windows.networking.networkoperators cyberhotspot\gui.py" -ForegroundColor DarkYellow
    throw "PyInstaller failed. The detailed PyInstaller error is immediately above this line."
}

Write-Host "[4/6] Staging MSIX contents..." -ForegroundColor Yellow
Copy-Item -Recurse -Force (Join-Path $dist "CyberHotspot\*") $stage
Copy-Item -Force (Join-Path $PSScriptRoot "AppxManifest.xml") $stage

# Generate self-contained placeholder logos.
Add-Type -AssemblyName System.Drawing
function New-Logo($path, $size) {
    $bmp = New-Object System.Drawing.Bitmap($size,$size)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.Clear([System.Drawing.Color]::FromArgb(7,7,17))
    $pen = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(255,79,216),3)
    $g.DrawRectangle($pen,3,3,$size-7,$size-7)
    $g.Dispose(); $bmp.Save($path,[System.Drawing.Imaging.ImageFormat]::Png); $bmp.Dispose()
}
New-Logo (Join-Path $stage "Assets\StoreLogo.png") 50
New-Logo (Join-Path $stage "Assets\Square150x150Logo.png") 150
New-Logo (Join-Path $stage "Assets\Square44x44Logo.png") 44

Write-Host "[5/6] Packaging MSIX..." -ForegroundColor Yellow
$makeappx = Get-ChildItem "$env:ProgramFiles(x86)\Windows Kits\10\bin" -Recurse -Filter makeappx.exe -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | Select-Object -First 1
if (-not $makeappx) { throw "makeappx.exe not found. Install the Windows 10/11 SDK." }

$msix = Join-Path $dist "CyberHotspot-$version.msix"
Remove-Item $msix -Force -ErrorAction SilentlyContinue
& $makeappx.FullName pack /d $stage /p $msix /o
if ($LASTEXITCODE -ne 0) { throw "MakeAppx failed." }

Write-Host "[6/6] Signing package..." -ForegroundColor Yellow
$signtool = Get-ChildItem "$env:ProgramFiles(x86)\Windows Kits\10\bin" -Recurse -Filter signtool.exe -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | Select-Object -First 1
if (-not $signtool) { throw "signtool.exe not found. Install the Windows SDK signing tools." }

$certPath = Join-Path $dist "CyberHotspot-TestCert.cer"
$pfxPath = Join-Path $dist "CyberHotspot-TestCert.pfx"
$existing = Get-ChildItem Cert:\CurrentUser\My | Where-Object { $_.Subject -eq "CN=CyberHotspot" } | Select-Object -First 1
if (-not $existing) {
    $existing = New-SelfSignedCertificate -Type Custom -Subject "CN=CyberHotspot" -KeyUsage DigitalSignature -FriendlyName "CyberHotspot Development Signing" -CertStoreLocation Cert:\CurrentUser\My
}
$pwd = ConvertTo-SecureString -String "CyberHotspotDev" -Force -AsPlainText
Export-Certificate -Cert $existing -FilePath $certPath -Force | Out-Null
Export-PfxCertificate -Cert $existing -FilePath $pfxPath -Password $pwd -Force | Out-Null

& $signtool.FullName sign /fd SHA256 /a /f $pfxPath /p CyberHotspotDev $msix
if ($LASTEXITCODE -ne 0) { throw "Signing failed." }
Import-Certificate -FilePath $certPath -CertStoreLocation Cert:\CurrentUser\TrustedPeople | Out-Null

Write-Host "" 
Write-Host "SUCCESS: $msix" -ForegroundColor Green
Write-Host "Install with:" -ForegroundColor Cyan
Write-Host "Add-AppxPackage -Path `"$msix`"" -ForegroundColor Yellow
