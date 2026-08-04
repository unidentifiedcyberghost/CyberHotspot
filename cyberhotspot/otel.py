"""Optional OpenTelemetry bridge.

Disabled by default. When enabled, it exports only to the configured endpoint,
which defaults to loopback. This module never selects a cloud/vendor endpoint.
"""
from __future__ import annotations
import os
from typing import Optional
from urllib.parse import urlparse


class OpenTelemetryBridge:
    def __init__(self):
        self.enabled = os.environ.get("CYBERHOTSPOT_OTEL_ENABLED", "0").lower() in {"1", "true", "yes"}
        self.meter = None
        self._cpu = self._memory = self._clients = None
        self.error: Optional[str] = None

    def start(self):
        if not self.enabled:
            return False
        try:
            from opentelemetry import metrics
            from opentelemetry.sdk.metrics import MeterProvider
            from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
            from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
            from opentelemetry.sdk.resources import Resource

            endpoint = os.environ.get("CYBERHOTSPOT_OTEL_ENDPOINT", "http://127.0.0.1:4317")
            parsed = urlparse(endpoint if "://" in endpoint else "http://" + endpoint)
            host = (parsed.hostname or "").lower()
            if host not in {"127.0.0.1", "localhost", "::1"}:
                raise ValueError("CyberHotspot OpenTelemetry is local-only; endpoint must resolve to loopback.")
            insecure = parsed.scheme == "http"
            exporter = OTLPMetricExporter(endpoint=endpoint, insecure=insecure)
            reader = PeriodicExportingMetricReader(
                exporter, export_interval_millis=int(os.environ.get("CYBERHOTSPOT_OTEL_INTERVAL_MS", "5000"))
            )
            resource = Resource.create({
                "service.name": "CyberHotspot",
                "service.version": "2.8.0",
                "service.environment": "local",
                "host.name": os.environ.get("COMPUTERNAME") or os.environ.get("HOSTNAME", "unknown"),
            })
            provider = MeterProvider(resource=resource, metric_readers=[reader])
            metrics.set_meter_provider(provider)
            self.meter = metrics.get_meter("cyberhotspot.telemetry", "2.8.0")
            self._cpu = self.meter.create_gauge("cyberhotspot.cpu.percent", unit="%")
            self._memory = self.meter.create_gauge("cyberhotspot.memory.percent", unit="%")
            self._clients = self.meter.create_gauge("cyberhotspot.hotspot.clients", unit="1")
            return True
        except Exception as exc:
            self.error = str(exc)
            return False

    def update(self, snapshot):
        if not self.meter:
            return
        attrs = {"os.type": os.name, "os.version": __import__("platform").platform()}
        try:
            self._cpu.set(snapshot.cpu_percent, attributes=attrs)
            self._memory.set(snapshot.memory_percent, attributes=attrs)
            self._clients.set(snapshot.client_count, attributes=attrs)
        except Exception as exc:
            self.error = str(exc)
