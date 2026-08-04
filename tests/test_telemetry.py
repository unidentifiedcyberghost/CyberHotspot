import time
from pathlib import Path
from tempfile import TemporaryDirectory

from cyberhotspot.telemetry import LocalTelemetryStore, TelemetryEngine


def test_local_store_snapshot_and_event():
    with TemporaryDirectory() as td:
        store = LocalTelemetryStore(Path(td))
        engine = TelemetryEngine(interval=0.5, store=store, metrics_port=0)
        engine.start()
        time.sleep(0.7)
        snap = engine.snapshot()
        assert snap is not None
        assert 0 <= snap.memory_percent <= 100
        text = engine.prometheus_text()
        assert "cyberhotspot_cpu_percent" in text
        engine.stop()


def test_event_is_structured():
    with TemporaryDirectory() as td:
        store = LocalTelemetryStore(Path(td))
        store.event("INFO", "test", "hello", "hello world", sample=1)
        rows = store.recent(1)
        assert rows[0]["component"] == "test"
        assert rows[0]["event"] == "hello"
