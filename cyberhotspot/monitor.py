"""Background hotspot polling so the PyQt GUI never blocks on network commands."""
from __future__ import annotations
import json
import threading
import time
from dataclasses import dataclass, field
from typing import List

from .models import Client


@dataclass
class HotspotSnapshot:
    raw_status: str = ""
    active: bool = False
    client_count: int = 0
    clients: List[Client] = field(default_factory=list)
    backend: str = ""
    error: str = ""
    updated_at: float = 0.0


class HotspotMonitor:
    def __init__(self, backend, interval=1.5):
        self.backend = backend
        self.interval = max(1.0, float(interval))
        self._lock = threading.RLock()
        self._snapshot = HotspotSnapshot(backend=getattr(backend, "backend_name", "unknown"))
        self._stop = threading.Event()
        self._thread = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="cyberhotspot-network-monitor", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def snapshot(self) -> HotspotSnapshot:
        with self._lock:
            s = self._snapshot
            return HotspotSnapshot(
                raw_status=s.raw_status, active=s.active, client_count=s.client_count,
                clients=list(s.clients), backend=s.backend, error=s.error,
                updated_at=s.updated_at,
            )

    @staticmethod
    def _parse_status(raw, fallback_backend):
        active = False
        count = 0
        backend = fallback_backend
        ssid = None
        try:
            data = json.loads(raw)
            state = str(data.get("state", ""))
            state_l = state.lower()
            active = any(x in state_l for x in ("active", "started", "running", "on"))
            count = max(0, int(data.get("client_count", 0) or 0))
            backend = str(data.get("backend", backend))
            ssid = data.get("ssid")
        except (ValueError, TypeError, json.JSONDecodeError):
            text = str(raw).lower()
            active = any(x in text for x in ("activated", "connected", "hotspot active"))
        return active, count, backend, ssid

    def _loop(self):
        while not self._stop.is_set():
            error = ""
            try:
                raw = self.backend.status()
                active, count, backend, _ssid = self._parse_status(raw, self.backend.backend_name)
                rows = self.backend.clients() if active or count else []
                count = max(count, len(rows))
                with self._lock:
                    self._snapshot = HotspotSnapshot(
                        raw_status=str(raw), active=active, client_count=count,
                        clients=rows, backend=backend, error="", updated_at=time.time(),
                    )
            except Exception as exc:
                error = str(exc)
                with self._lock:
                    old = self._snapshot
                    self._snapshot = HotspotSnapshot(
                        raw_status=old.raw_status, active=old.active,
                        client_count=old.client_count, clients=list(old.clients),
                        backend=old.backend, error=error, updated_at=time.time(),
                    )
            self._stop.wait(self.interval)
