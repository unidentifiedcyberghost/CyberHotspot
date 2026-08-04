# Windows Mobile Hotspot deployment

CyberHotspot uses the supported Windows `NetworkOperatorTetheringManager` API for the built-in Mobile Hotspot. Microsoft requires the `wiFiControl` device capability for creating the tethering manager. A normal unpackaged Python process does not have that package capability, so the deployable Windows build is an MSIX package.

## Build on Windows

Requirements:

- Windows 10 19041+ or Windows 11
- Python 3.14 x64
- Visual Studio Build Tools or Windows SDK (for `makeappx.exe`)
- Internet access for Python packages

From the repository root in PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\packaging\windows\build-msix.ps1
```

The script creates `dist\CyberHotspot-2.6.1.msix`.

## Install

For local development/testing, the package is unsigned. Windows will require a trusted development certificate. The build script can create and trust a local test certificate when run elevated.

## Why this is necessary

The legacy command:

```text
netsh wlan show drivers
Hosted network supported : No
```

is not the same thing as Windows Mobile Hotspot. CyberHotspot does not require the legacy Hosted Network feature when the modern Windows tethering API is available.


## Build troubleshooting

The MSIX builder uses the currently active `.venv` Python instead of the global `py -3` launcher. If PyInstaller fails, the script prints the complete import/build diagnostic. Python 3.14 is supported by the current PyWinRT 3.2.1 wheels; PyQt5 5.15.11 publishes a CPython 3.8+ ABI3 Windows wheel.
