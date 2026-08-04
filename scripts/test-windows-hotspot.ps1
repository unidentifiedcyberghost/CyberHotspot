# CyberHotspot Windows Mobile Hotspot smoke test.
# Run from an elevated or normal PowerShell window in most Windows 10 installations.
# This script uses the same WinRT backend as CyberHotspot.
param([string]$Ssid="CyberHotspot", [string]$Password="pinoyunknown")
& "$PSScriptRoot/windows_tethering.ps1" -Action probe
& "$PSScriptRoot/windows_tethering.ps1" -Action start -Json (@{ssid=$Ssid;password=$Password}|ConvertTo-Json -Compress)
& "$PSScriptRoot/windows_tethering.ps1" -Action status
