param(
  [string]$Prometheus = ".\prometheus.exe",
  [string]$Config = ".\prometheus\prometheus.yml"
)
$ErrorActionPreference = "Stop"
if (-not (Test-Path $Prometheus)) { throw "Prometheus binary not found: $Prometheus" }
if (-not (Test-Path $Config)) { throw "CyberHotspot Prometheus config not found: $Config" }
Write-Host "CYBERHOTSPOT // LOCAL PROMETHEUS"
Write-Host "Target: 127.0.0.1:9464"
& $Prometheus "--config.file=$Config"
