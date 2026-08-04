"""Local-only telemetry engine for CyberHotspot.

The engine is deliberately self-contained:
- psutil for host/process metrics
- SQLite + JSONL for local persistence
- a localhost-only Prometheus-compatible /metrics endpoint
- optional OpenTelemetry SDK integration, disabled by default

No cloud endpoint, Docker, Grafana, or remote transmission is required.
"""
from __future__ import annotations

import gc
import json
import os
import platform
import socket
import sqlite3
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None


@dataclass
class TelemetrySnapshot:
    timestamp: str
    epoch: float
    cpu_percent: float
    memory_percent: float
    memory_used: int
    memory_available: int
    swap_percent: float
    disk_read_bytes: int
    disk_write_bytes: int
    disk_read_speed: float
    disk_write_speed: float
    net_rx_bytes: int
    net_tx_bytes: int
    net_rx_speed: float
    net_tx_speed: float
    net_rx_packets: int
    net_tx_packets: int
    net_rx_errors: int
    net_tx_errors: int
    net_rx_dropped: int
    net_tx_dropped: int
    process_count: int
    thread_count: int
    python_threads: int
    gc_counts: tuple
    process_cpu_percent: float
    process_memory_rss: int
    uptime_seconds: float
    boot_time: float
    hotspot_active: bool = False
    client_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LocalTelemetryStore:
    """Bounded local SQLite/JSONL storage.

    The database is stored under the application data directory. Nothing is
    transmitted unless an operator explicitly configures another component.
    """

    def __init__(self, root: Optional[Path] = None, retention_days: int = 7):
        if root is None:
            override = os.environ.get("CYBERHOTSPOT_DATA_DIR")
            if override:
                root = Path(override)
            elif os.name == "nt":
                root = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "CyberHotspot" / "data"
            else:
                root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "CyberHotspot"
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.db_path = self.root / "cyberhotspot.db"
        self.jsonl_path = self.root / "telemetry.jsonl"
        self.retention_days = max(1, int(retention_days))
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(str(self.db_path), timeout=5)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def _init_db(self):
        with self._connect() as db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS telemetry_samples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    epoch REAL NOT NULL,
                    cpu_percent REAL,
                    memory_percent REAL,
                    memory_used INTEGER,
                    memory_available INTEGER,
                    swap_percent REAL,
                    disk_read_bytes INTEGER,
                    disk_write_bytes INTEGER,
                    disk_read_speed REAL,
                    disk_write_speed REAL,
                    net_rx_bytes INTEGER,
                    net_tx_bytes INTEGER,
                    net_rx_speed REAL,
                    net_tx_speed REAL,
                    net_rx_packets INTEGER,
                    net_tx_packets INTEGER,
                    net_rx_errors INTEGER,
                    net_tx_errors INTEGER,
                    net_rx_dropped INTEGER,
                    net_tx_dropped INTEGER,
                    process_count INTEGER,
                    thread_count INTEGER,
                    python_threads INTEGER,
                    gc_counts TEXT,
                    process_cpu_percent REAL,
                    process_memory_rss INTEGER,
                    uptime_seconds REAL,
                    boot_time REAL,
                    hotspot_active INTEGER,
                    client_count INTEGER
                )"""
            )
            db.execute(
                """CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    epoch REAL NOT NULL,
                    level TEXT NOT NULL,
                    component TEXT NOT NULL,
                    event TEXT NOT NULL,
                    message TEXT NOT NULL,
                    payload TEXT
                )"""
            )
            db.execute(
                "CREATE INDEX IF NOT EXISTS idx_telemetry_epoch ON telemetry_samples(epoch)"
            )
            db.execute("CREATE INDEX IF NOT EXISTS idx_events_epoch ON events(epoch)")
            db.commit()

    def write_snapshot(self, snap: TelemetrySnapshot):
        d = snap.to_dict()
        with self._lock:
            with self._connect() as db:
                db.execute(
                    """INSERT INTO telemetry_samples VALUES (
                        NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
                    )""",
                    (
                        d["timestamp"], d["epoch"], d["cpu_percent"],
                        d["memory_percent"], d["memory_used"], d["memory_available"],
                        d["swap_percent"], d["disk_read_bytes"], d["disk_write_bytes"],
                        d["disk_read_speed"], d["disk_write_speed"], d["net_rx_bytes"],
                        d["net_tx_bytes"], d["net_rx_speed"], d["net_tx_speed"],
                        d["net_rx_packets"], d["net_tx_packets"], d["net_rx_errors"],
                        d["net_tx_errors"], d["net_rx_dropped"], d["net_tx_dropped"],
                        d["process_count"], d["thread_count"], d["python_threads"],
                        json.dumps(list(d["gc_counts"])), d["process_cpu_percent"],
                        d["process_memory_rss"], d["uptime_seconds"], d["boot_time"],
                        int(d["hotspot_active"]), d["client_count"],
                    ),
                )
                db.execute(
                    "DELETE FROM telemetry_samples WHERE epoch < ?",
                    (time.time() - self.retention_days * 86400,),
                )
                db.commit()
            try:
                with self.jsonl_path.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(d, separators=(",", ":")) + "\n")
            except OSError:
                pass

    def event(self, level: str, component: str, event: str, message: str, **payload):
        now = time.time()
        ts = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        record = {
            "timestamp": ts, "epoch": now, "level": level.upper(),
            "component": component, "event": event, "message": message,
            "payload": payload,
        }
        with self._lock:
            with self._connect() as db:
                db.execute(
                    "INSERT INTO events(timestamp,epoch,level,component,event,message,payload) VALUES(?,?,?,?,?,?,?)",
                    (ts, now, record["level"], component, event, message,
                     json.dumps(payload, separators=(",", ":"))),
                )
                db.execute("DELETE FROM events WHERE epoch < ?", (now - self.retention_days * 86400,))
                db.commit()
            try:
                with (self.root / "events.jsonl").open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(record, separators=(",", ":")) + "\n")
            except OSError:
                pass

    def recent(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT timestamp,level,component,event,message,payload FROM events ORDER BY id DESC LIMIT ?",
                (max(1, min(limit, 1000)),),
            ).fetchall()
        return [
            {"timestamp": r[0], "level": r[1], "component": r[2],
             "event": r[3], "message": r[4], "payload": r[5]}
            for r in rows
        ]


class _MetricsHandler(BaseHTTPRequestHandler):
    server_version = "CyberHotspotMetrics/1.0"

    def do_GET(self):
        if self.path != "/metrics":
            self.send_response(404)
            self.end_headers()
            return
        body = self.server.telemetry.prometheus_text().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        return


class LocalMetricsServer:
    """Prometheus-compatible exporter bound strictly to loopback."""

    def __init__(self, telemetry, host="127.0.0.1", port=9464):
        self.telemetry = telemetry
        self.host = host
        self.port = int(port)
        self.httpd = None
        self.thread = None

    def start(self):
        if self.httpd:
            return
        self.httpd = ThreadingHTTPServer((self.host, self.port), _MetricsHandler)
        self.httpd.telemetry = self.telemetry
        self.thread = threading.Thread(
            target=self.httpd.serve_forever, name="cyberhotspot-metrics", daemon=True
        )
        self.thread.start()

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None
            self.thread = None


class TelemetryEngine:
    def __init__(self, interval=1.0, store=None, metrics_port=9464):
        self.interval = max(0.5, float(interval))
        self.store = store or LocalTelemetryStore()
        self.metrics_server = LocalMetricsServer(self, port=metrics_port)
        self._lock = threading.RLock()
        self._snapshot = None
        self._hotspot_active = False
        self._client_count = 0
        self._stop = threading.Event()
        self._thread = None
        self._prev_disk = None
        self._prev_net = None
        self._prev_time = None
        self._last_event = {}
        self._last_process_sample = 0.0
        self._cached_process_count = 0
        try:
            from .otel import OpenTelemetryBridge
            self.otel = OpenTelemetryBridge()
        except Exception:
            self.otel = None

    def start(self):
        if psutil is None:
            raise RuntimeError("psutil is required for local telemetry. Install with: pip install psutil")
        if self._thread and self._thread.is_alive():
            return
        # Prime psutil's CPU sampler without blocking the GUI.
        psutil.cpu_percent(interval=None)
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="cyberhotspot-telemetry", daemon=True)
        self._thread.start()
        try:
            if self.otel:
                self.otel.start()
            self.metrics_server.start()
        except OSError:
            # Metrics endpoint is useful but must never prevent the GUI/hotspot
            # from working if the port is occupied.
            self.store.event("WARN", "telemetry", "metrics_bind_failed",
                             "Local metrics endpoint could not bind", port=self.metrics_server.port)

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)
        self.metrics_server.stop()

    def set_hotspot(self, active: bool, client_count: int = 0):
        with self._lock:
            self._hotspot_active = bool(active)
            self._client_count = max(0, int(client_count))

    def snapshot(self) -> Optional[TelemetrySnapshot]:
        with self._lock:
            return self._snapshot

    def _loop(self):
        self.store.event("INFO", "telemetry", "engine_started",
                         "Local telemetry engine started", interval=self.interval)
        while not self._stop.wait(self.interval):
            try:
                snap = self._collect()
                with self._lock:
                    self._snapshot = snap
                self.store.write_snapshot(snap)
                if self.otel:
                    self.otel.update(snap)
                self._thresholds(snap)
            except Exception as exc:
                self.store.event("ERROR", "telemetry", "collection_error", str(exc))

    def _collect(self):
        now = time.time()
        stamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        disk = psutil.disk_io_counters()
        net = psutil.net_io_counters()
        dt = max(0.001, now - self._prev_time) if self._prev_time else self.interval

        disk_r = getattr(disk, "read_bytes", 0) if disk else 0
        disk_w = getattr(disk, "write_bytes", 0) if disk else 0
        net_rx = getattr(net, "bytes_recv", 0) if net else 0
        net_tx = getattr(net, "bytes_sent", 0) if net else 0

        prev_d = self._prev_disk or (disk_r, disk_w)
        prev_n = self._prev_net or (net_rx, net_tx)
        self._prev_disk, self._prev_net, self._prev_time = (disk_r, disk_w), (net_rx, net_tx), now

        vm = psutil.virtual_memory()
        swap = psutil.swap_memory()
        proc = psutil.Process(os.getpid())
        try:
            proc_cpu = proc.cpu_percent(interval=None)
        except Exception:
            proc_cpu = 0.0
        try:
            proc_mem = proc.memory_info().rss
        except Exception:
            proc_mem = 0
        if now - self._last_process_sample >= 5.0 or not self._cached_process_count:
            try:
                self._cached_process_count = len(psutil.pids())
            except Exception:
                self._cached_process_count = 0
            self._last_process_sample = now
        process_count = self._cached_process_count
        try:
            thread_count = threading.active_count()
        except Exception:
            thread_count = 0

        with self._lock:
            active, clients = self._hotspot_active, self._client_count

        return TelemetrySnapshot(
            timestamp=stamp, epoch=now,
            cpu_percent=round(psutil.cpu_percent(interval=None), 1),
            memory_percent=round(vm.percent, 1), memory_used=vm.used,
            memory_available=vm.available, swap_percent=round(swap.percent, 1),
            disk_read_bytes=disk_r, disk_write_bytes=disk_w,
            disk_read_speed=max(0, (disk_r - prev_d[0]) / dt),
            disk_write_speed=max(0, (disk_w - prev_d[1]) / dt),
            net_rx_bytes=net_rx, net_tx_bytes=net_tx,
            net_rx_speed=max(0, (net_rx - prev_n[0]) / dt),
            net_tx_speed=max(0, (net_tx - prev_n[1]) / dt),
            net_rx_packets=getattr(net, "packets_recv", 0) if net else 0,
            net_tx_packets=getattr(net, "packets_sent", 0) if net else 0,
            net_rx_errors=getattr(net, "errin", 0) if net else 0,
            net_tx_errors=getattr(net, "errout", 0) if net else 0,
            net_rx_dropped=getattr(net, "dropin", 0) if net else 0,
            net_tx_dropped=getattr(net, "dropout", 0) if net else 0,
            process_count=process_count,
            thread_count=thread_count,
            python_threads=threading.active_count(),
            gc_counts=tuple(gc.get_count()),
            process_cpu_percent=round(proc_cpu, 1),
            process_memory_rss=proc_mem,
            uptime_seconds=max(0, now - psutil.boot_time()),
            boot_time=psutil.boot_time(),
            hotspot_active=active, client_count=clients,
        )

    def _thresholds(self, s):
        cpu_limit = float(os.environ.get("CYBERHOTSPOT_CPU_WARN", "85"))
        mem_limit = float(os.environ.get("CYBERHOTSPOT_MEMORY_WARN", "85"))
        for key, value, limit in (("cpu", s.cpu_percent, cpu_limit), ("memory", s.memory_percent, mem_limit)):
            if value >= limit and self._last_event.get(key, 0) < time.time() - 30:
                self._last_event[key] = time.time()
                self.store.event("WARN", "telemetry", f"{key}_threshold",
                                 f"{key.upper()} reached {value:.1f}%", value=value, threshold=limit)

    def prometheus_text(self) -> str:
        s = self.snapshot()
        if not s:
            return "# CyberHotspot telemetry is warming up.\n"
        lines = [
            "# HELP cyberhotspot_cpu_percent Current system CPU utilization.",
            "# TYPE cyberhotspot_cpu_percent gauge",
            f"cyberhotspot_cpu_percent {s.cpu_percent}",
            "# HELP cyberhotspot_memory_percent Current system memory utilization.",
            "# TYPE cyberhotspot_memory_percent gauge",
            f"cyberhotspot_memory_percent {s.memory_percent}",
            "# TYPE cyberhotspot_swap_percent gauge",
            f"cyberhotspot_swap_percent {s.swap_percent}",
            "# TYPE cyberhotspot_network_rx_bytes_total counter",
            f"cyberhotspot_network_rx_bytes_total {s.net_rx_bytes}",
            "# TYPE cyberhotspot_network_tx_bytes_total counter",
            f"cyberhotspot_network_tx_bytes_total {s.net_tx_bytes}",
            "# TYPE cyberhotspot_network_rx_bytes_per_second gauge",
            f"cyberhotspot_network_rx_bytes_per_second {s.net_rx_speed:.3f}",
            "# TYPE cyberhotspot_network_tx_bytes_per_second gauge",
            f"cyberhotspot_network_tx_bytes_per_second {s.net_tx_speed:.3f}",
            "# TYPE cyberhotspot_disk_read_bytes_per_second gauge",
            f"cyberhotspot_disk_read_bytes_per_second {s.disk_read_speed:.3f}",
            "# TYPE cyberhotspot_disk_write_bytes_per_second gauge",
            f"cyberhotspot_disk_write_bytes_per_second {s.disk_write_speed:.3f}",
            "# TYPE cyberhotspot_process_count gauge",
            f"cyberhotspot_process_count {s.process_count}",
            "# TYPE cyberhotspot_thread_count gauge",
            f"cyberhotspot_thread_count {s.thread_count}",
            "# TYPE cyberhotspot_process_cpu_percent gauge",
            f"cyberhotspot_process_cpu_percent {s.process_cpu_percent}",
            "# TYPE cyberhotspot_process_memory_bytes gauge",
            f"cyberhotspot_process_memory_bytes {s.process_memory_rss}",
            "# TYPE cyberhotspot_hotspot_active gauge",
            f"cyberhotspot_hotspot_active {int(s.hotspot_active)}",
            "# TYPE cyberhotspot_hotspot_clients gauge",
            f"cyberhotspot_hotspot_clients {s.client_count}",
            "# TYPE cyberhotspot_uptime_seconds gauge",
            f"cyberhotspot_uptime_seconds {s.uptime_seconds:.3f}",
        ]
        return "\n".join(lines) + "\n"
