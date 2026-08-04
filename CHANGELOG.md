# Changelog

## v2.8.0 — Local Observability + Performance HUD

- Added a background hotspot/network monitor so expensive Windows/Linux backend calls no longer run on the PyQt GUI thread.
- Added a local `psutil` telemetry engine with CPU, RAM, swap, disk I/O, network throughput/packets/errors, process/thread/runtime and GC metrics.
- Added local SQLite retention storage and JSONL event/telemetry files.
- Added a loopback-only Prometheus-compatible `/metrics` endpoint on `127.0.0.1:9464`.
- Added optional OpenTelemetry metrics support; disabled by default and restricted to an explicitly configured endpoint.
- Added threshold warnings for CPU and memory with cooldowns.
- Added structured event records with timestamp, level, component, event, message and JSON payload.
- Reworked the System Telemetry HUD to show live metrics plus a color-coded, scalable event log.
- Added responsive telemetry font sizing and A−/A+ controls.
- Reduced GUI polling and table redraw overhead.
- Preserved the Windows Mobile Hotspot client-count authority and live client details.
- No Docker, cloud telemetry, remote exporter, or automatic external transmission is required.
