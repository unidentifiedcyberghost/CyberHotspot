import json
import sys
import time
from pathlib import Path

from PyQt5.QtCore import QTimer, Qt, QSize
from PyQt5.QtGui import QColor, QFont, QTextCharFormat, QTextCursor
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QCheckBox, QPlainTextEdit, QTableWidget,
    QTableWidgetItem, QMessageBox, QGroupBox, QDialog, QDialogButtonBox,
    QToolButton, QFrame, QSizePolicy, QGridLayout, QSpinBox
)

from .diagnostics import doctor
from .capabilities import scan_capabilities
from .backend_manager import BackendManager
from .models import HotspotConfig
from .network import wireless_interfaces
from .monitor import HotspotMonitor
from .telemetry import TelemetryEngine


STYLE = """
QWidget {
    background:#05050b;
    color:#f4eaff;
    font-family:"DejaVu Sans";
    font-size:10px;
}
QWidget#root {
    background:#04070c;
    border:2px solid #d82cff;
    border-radius:4px;
}
QLabel#title { color:#ff4fd8; font-size:21px; font-weight:bold; }
QLabel#subtitle { color:#9d7cff; font-size:8px; }
QLabel#headerStatus { color:#62ffcf; font-size:9px; font-weight:bold; }
QLabel#state { color:#ff66e8; font-size:11px; font-weight:bold; }
QLabel#footer { color:#c85dff; font-size:8px; }
QLabel#count { color:#61ffd2; font-size:9px; font-weight:bold; }
QLabel#sectionStatus { color:#a96cff; font-size:8px; font-weight:bold; }
QLabel#metric { color:#d7c7ff; font-family:"Consolas","Courier New",monospace; font-size:9px; }
QLabel#metricValue { color:#67ffd8; font-family:"Consolas","Courier New",monospace; font-size:10px; font-weight:bold; }
QLabel#metricWarn { color:#ffd34d; font-family:"Consolas","Courier New",monospace; font-size:10px; font-weight:bold; }
QLabel#metricCritical { color:#ff5c8a; font-family:"Consolas","Courier New",monospace; font-size:10px; font-weight:bold; }

QGroupBox {
    background:#090812;
    border:1px solid #6d2397;
    border-radius:5px;
    margin-top:11px;
    padding:7px;
}
QGroupBox::title {
    color:#ff4fd8;
    background:#090812;
    left:10px;
    padding:0 5px;
    font-size:8px;
    font-weight:bold;
}

QLineEdit, QComboBox, QPlainTextEdit, QTableWidget, QSpinBox {
    background:#03050a;
    border:1px solid #54206f;
    border-radius:3px;
    padding:3px 5px;
    color:#efffff;
    selection-background-color:#8e28b8;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border:1px solid #ff4fd8;
}
QComboBox, QLineEdit, QSpinBox {
    min-height:20px;
    max-height:23px;
}
QPlainTextEdit {
    font-family:"Consolas","Courier New",monospace;
    font-size:9px;
}
QTableWidget {
    gridline-color:#20102b;
    font-size:8px;
    padding:0;
}
QHeaderView::section {
    background:#11091a;
    color:#ff70df;
    border:0;
    border-bottom:1px solid #70238f;
    padding:4px;
    font-size:7px;
    font-weight:bold;
}
QTableCornerButton::section {
    background:#11091a;
    border:0;
}
QPushButton {
    background:#0c0913;
    border:1px solid #a62bd1;
    border-radius:2px;
    padding:3px 6px;
    min-height:21px;
    color:#ffb5f0;
    font-size:8px;
    font-weight:bold;
}
QPushButton:hover {
    background:#21102c;
    border:1px solid #ff4fd8;
    color:#ffd7f6;
}
QPushButton:pressed { background:#361143; }
QPushButton:disabled {
    color:#59435f;
    border-color:#302034;
    background:#09070d;
}
QPushButton[active="true"] {
    background:#261035;
    border:1px solid #5dffd1;
    color:#72ffd5;
}
QPushButton[warn="true"] {
    border:1px solid #ffd34d;
    color:#ffe58a;
}
QToolButton {
    background:#0b0811;
    border:1px solid #57206f;
    border-radius:2px;
    color:#cda8ff;
    padding:3px 6px;
    font-size:8px;
    font-weight:bold;
    text-align:left;
}
QToolButton:hover {
    border:1px solid #ff4fd8;
    color:#ffb5f0;
}
QCheckBox {
    color:#d9b7ff;
    spacing:5px;
    font-size:8px;
}
QCheckBox::indicator {
    width:11px;
    height:11px;
    border:1px solid #a62bd1;
    background:#05050b;
}
QCheckBox::indicator:checked { background:#e33ccf; }
QScrollBar:vertical {
    background:#07050b;
    width:8px;
}
QScrollBar::handle:vertical {
    background:#61207d;
    min-height:20px;
}
"""


class HardwareDialog(QDialog):
    def __init__(self, report, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CyberHotspot // Hardware Diagnostics")
        self.resize(650, 430)
        self.setStyleSheet(STYLE)
        layout = QVBoxLayout(self)
        title = QLabel("HARDWARE / AP CAPABILITY SCAN")
        title.setObjectName("title")
        layout.addWidget(title)
        if report.vm_detected:
            vm_label = QLabel(f"VM ENVIRONMENT: {report.vm_vendor.upper()}")
            vm_label.setObjectName("hwWarn")
        else:
            vm_label = QLabel("ENVIRONMENT: PHYSICAL / VM NOT DETECTED")
            vm_label.setObjectName("hwGood")
        layout.addWidget(vm_label)
        wifi = ", ".join(report.wifi_interfaces) if report.wifi_interfaces else "NONE"
        ap = ", ".join(report.ap_interfaces) if report.ap_interfaces else "NONE"
        eth = ", ".join(report.ethernet_interfaces) if report.ethernet_interfaces else "NONE"
        layout.addWidget(QLabel(f"Wi-Fi interfaces: {wifi}"))
        layout.addWidget(QLabel(f"AP-capable interfaces: {ap}"))
        layout.addWidget(QLabel(f"Ethernet interfaces: {eth}"))
        status = QLabel(
            "✓ READY: AP-capable Wi-Fi hardware detected." if report.ap_capable
            else ("⚠ WI-FI FOUND // AP MODE NOT DETECTED" if report.wifi_present
                  else "✕ NO WI-FI DEVICE: hotspot cannot start yet.")
        )
        status.setObjectName("hwGood" if report.ap_capable else ("hwWarn" if report.wifi_present else "hwBad"))
        layout.addWidget(status)
        details = QPlainTextEdit()
        details.setReadOnly(True)
        for warning in report.warnings:
            details.appendPlainText("[GUIDANCE] " + warning)
        layout.addWidget(details)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class CapabilityDialog(QDialog):
    def __init__(self, report, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CyberHotspot // Network Capability Engine")
        self.resize(720, 560)
        self.setStyleSheet(STYLE)
        layout = QVBoxLayout(self)
        title = QLabel("NETWORK CAPABILITY ENGINE")
        title.setObjectName("title")
        layout.addWidget(title)
        state = QLabel("✓ HOTSPOT READY" if report.ready else "✕ HOTSPOT NOT READY")
        state.setObjectName("hwGood" if report.ready else "hwBad")
        layout.addWidget(state)
        info = QPlainTextEdit()
        info.setReadOnly(True)
        lines = [
            f"Platform            : {report.platform}",
            f"Virtualization      : {report.virtualization}",
            f"NetworkManager      : {'YES' if report.network_manager else 'NO'}",
            f"nmcli               : {'YES' if report.nmcli else 'NO'}",
            f"iw                  : {'YES' if report.iw else 'NO'}",
            f"Wi-Fi interfaces    : {', '.join(report.wifi_interfaces) or 'NONE'}",
            f"AP-capable          : {', '.join(report.ap_interfaces) or 'NONE'}",
            f"Ethernet            : {', '.join(report.ethernet_interfaces) or 'NONE'}",
            f"rfkill              : {'BLOCKED' if (report.rfkill_blocked or report.rfkill_hard_blocked) else 'CLEAR'}",
            f"Regulatory domain   : {report.regulatory_domain}",
            f"Available backends  : {', '.join(report.backends) or 'NONE'}",
            f"Selected backend    : {report.selected_backend}",
        ]
        for line in lines:
            info.appendPlainText(line)
        info.appendPlainText("")
        for reason in report.reasons:
            info.appendPlainText("[REASON] " + reason)
        for recommendation in report.recommendations:
            info.appendPlainText("[NEXT] " + recommendation)
        layout.addWidget(info)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class CyberHotspotWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.backend = BackendManager()
        self.monitor = HotspotMonitor(self.backend, interval=1.5)
        self.telemetry = TelemetryEngine(interval=1.0, metrics_port=9464)
        self.hotspot_active = False
        self.reported_client_count = 0
        self.telemetry_font_scale = 1.0
        self._last_status_log = 0.0
        self.setObjectName("root")
        self.setWindowTitle("CyberHotspot // HUD Control Center")
        self.resize(1100, 700)
        self.setMinimumSize(900, 600)
        self.setStyleSheet(STYLE)
        self.build_ui()
        self.refresh()
        self.hardware_scan()
        self.monitor.start()
        try:
            self.telemetry.start()
            self.append_log("[TELEMETRY] LOCAL ENGINE ONLINE // SQLite + JSONL // /metrics: 127.0.0.1:9464")
        except Exception as exc:
            self.append_log(f"[WARN] Local telemetry engine unavailable: {exc}")

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.live_refresh)
        self.timer.start(1000)

    def build_ui(self):
        outer = QVBoxLayout()
        outer.setContentsMargins(12, 8, 12, 7)
        outer.setSpacing(4)
        self.setLayout(outer)

        top = QHBoxLayout()
        left = QVBoxLayout()
        left.setSpacing(1)
        title = QLabel("CYBERHOTSPOT // NETWORK CONTROL DECK")
        title.setObjectName("title")
        subtitle = QLabel("CROSS-PLATFORM HOTSPOT ENGINE  //  WINDOWS • LINUX  //  LOCAL OBSERVABILITY")
        subtitle.setObjectName("subtitle")
        left.addWidget(title)
        left.addWidget(subtitle)
        top.addLayout(left)
        top.addStretch()
        self.app_status = QLabel("● SYSTEM ONLINE")
        self.app_status.setObjectName("headerStatus")
        self.hotspot_status = QLabel("  ○ HOTSPOT OFF")
        self.hotspot_status.setObjectName("headerStatus")
        self.hw_status = QLabel("  HARDWARE: SCANNING...")
        self.hw_status.setObjectName("sectionStatus")
        top.addWidget(self.app_status)
        top.addWidget(self.hotspot_status)
        top.addWidget(self.hw_status)
        outer.addLayout(top)

        line = QLabel("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        line.setStyleSheet("color:#8b28b7;")
        outer.addWidget(line)

        config = QGroupBox("01 // HOTSPOT CONFIGURATION")
        form = QHBoxLayout(config)
        form.setContentsMargins(5, 1, 5, 1)
        form.setSpacing(4)
        form.addWidget(QLabel("SSID"))
        self.ssid = QLineEdit("CyberHotspot")
        self.ssid.setMaximumWidth(160)
        form.addWidget(self.ssid)
        form.addWidget(QLabel("PASSWORD"))
        self.password = QLineEdit()
        self.password.setPlaceholderText("8–63 chars")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setMaximumWidth(150)
        form.addWidget(self.password)
        self.wifi_toggle = QToolButton()
        self.wifi_toggle.setText("WI-FI NAVIGATION ▸")
        self.wifi_toggle.setCheckable(True)
        self.wifi_toggle.toggled.connect(self.toggle_wifi_settings)
        form.addWidget(self.wifi_toggle)
        self.interface = QComboBox()
        self.interface.setMaximumWidth(150)
        self.interface.setVisible(False)
        form.addWidget(self.interface)
        self.shared = QCheckBox("SHARING")
        self.shared.setVisible(False)
        form.addWidget(self.shared)
        form.addStretch()
        outer.addWidget(config)

        action = QGroupBox("02 // NETWORK CONTROL")
        buttons = QHBoxLayout(action)
        buttons.setContentsMargins(5, 1, 5, 1)
        buttons.setSpacing(3)
        self.start_btn = QPushButton("● START")
        self.stop_btn = QPushButton("○ STOP")
        self.status_btn = QPushButton("↻ STATUS")
        self.doctor_btn = QPushButton("⌁ DIAG")
        self.hardware_btn = QPushButton("⌬ HARDWARE")
        self.capability_btn = QPushButton("◈ CAP")
        for b, slot in [
            (self.start_btn, self.start),
            (self.stop_btn, self.stop),
            (self.status_btn, self.status),
            (self.doctor_btn, self.run_doctor),
            (self.hardware_btn, self.hardware_scan),
            (self.capability_btn, self.capability_scan),
        ]:
            b.setMinimumWidth(75)
            b.setMaximumHeight(24)
            b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            b.clicked.connect(slot)
            buttons.addWidget(b)
        outer.addWidget(action)

        panels = QHBoxLayout()
        panels.setSpacing(5)

        clients_box = QGroupBox("03 // CONNECTED CLIENTS")
        c_layout = QVBoxLayout(clients_box)
        c_layout.setContentsMargins(5, 4, 5, 4)
        c_top = QHBoxLayout()
        self.client_count = QLabel("● 00 ONLINE")
        self.client_count.setObjectName("count")
        c_top.addWidget(self.client_count)
        c_top.addStretch()
        self.client_refresh_label = QLabel("LIVE // 1.5s")
        self.client_refresh_label.setObjectName("sectionStatus")
        c_top.addWidget(self.client_refresh_label)
        c_layout.addLayout(c_top)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["IP ADDRESS", "MAC ADDRESS", "DEVICE / HOST", "STATE"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 110)
        self.table.setColumnWidth(1, 126)
        self.table.setColumnWidth(2, 140)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        c_layout.addWidget(self.table)
        panels.addWidget(clients_box, 1)

        log_box = QGroupBox("04 // SYSTEM TELEMETRY")
        l = QVBoxLayout(log_box)
        l.setContentsMargins(5, 4, 5, 4)

        metrics = QGridLayout()
        metrics.setHorizontalSpacing(10)
        metrics.setVerticalSpacing(2)
        self.metric_labels = {}
        metric_names = [
            ("CPU", "cpu_percent"), ("RAM", "memory_percent"),
            ("SWAP", "swap_percent"), ("RX", "net_rx_speed"),
            ("TX", "net_tx_speed"), ("DISK R", "disk_read_speed"),
            ("DISK W", "disk_write_speed"), ("PROC", "process_count"),
            ("THREADS", "thread_count"), ("PY RSS", "process_memory_rss"),
            ("GC", "gc_counts"), ("UPTIME", "uptime_seconds"),
        ]
        for i, (label, key) in enumerate(metric_names):
            row, col = divmod(i, 4)
            caption = QLabel(label)
            caption.setObjectName("metric")
            value = QLabel("--")
            value.setObjectName("metricValue")
            metrics.addWidget(caption, row, col * 2)
            metrics.addWidget(value, row, col * 2 + 1)
            self.metric_labels[key] = value
        l.addLayout(metrics)

        log_toolbar = QHBoxLayout()
        self.log_status = QLabel("LOCAL EVENT STREAM")
        self.log_status.setObjectName("sectionStatus")
        log_toolbar.addWidget(self.log_status)
        log_toolbar.addStretch()
        self.log_minus = QPushButton("A−")
        self.log_plus = QPushButton("A+")
        self.log_clear = QPushButton("CLEAR")
        self.log_minus.setFixedWidth(34)
        self.log_plus.setFixedWidth(34)
        self.log_clear.setFixedWidth(48)
        self.log_minus.clicked.connect(lambda: self.adjust_log_scale(-0.1))
        self.log_plus.clicked.connect(lambda: self.adjust_log_scale(0.1))
        self.log_clear.clicked.connect(self.clear_log)
        log_toolbar.addWidget(self.log_minus)
        log_toolbar.addWidget(self.log_plus)
        log_toolbar.addWidget(self.log_clear)
        l.addLayout(log_toolbar)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.log.document().setMaximumBlockCount(900)
        l.addWidget(self.log, 1)
        panels.addWidget(log_box, 2)
        outer.addLayout(panels, 1)

        status_bar = QHBoxLayout()
        self.state = QLabel("STATE: READY // INITIALIZING")
        self.state.setObjectName("state")
        status_bar.addWidget(self.state)
        status_bar.addStretch()
        self.telemetry_summary = QLabel("LOCAL: SQLite // /metrics // CLIENTS: 00")
        self.telemetry_summary.setObjectName("sectionStatus")
        status_bar.addWidget(self.telemetry_summary)
        outer.addLayout(status_bar)

        footer = QHBoxLayout()
        footer.addStretch()
        for text in ("www.instagram.com/pinoyunknown", "  //  ", "https://github.com/unidentifiedcyberghost"):
            label = QLabel(text)
            label.setObjectName("footer")
            footer.addWidget(label)
        footer.addStretch()
        outer.addLayout(footer)
        self._apply_log_scale()

    def toggle_wifi_settings(self, expanded):
        self.wifi_toggle.setText("WI-FI NAVIGATION ▾" if expanded else "WI-FI NAVIGATION ▸")
        self.interface.setVisible(expanded)
        self.shared.setVisible(expanded)

    def _set_button_active(self, button, active):
        button.setProperty("active", bool(active))
        button.style().unpolish(button)
        button.style().polish(button)
        button.update()

    def _set_hotspot_indicator(self, active):
        self.hotspot_active = active
        self.hotspot_status.setText("  ● HOTSPOT ACTIVE" if active else "  ○ HOTSPOT OFF")
        self._set_button_active(self.start_btn, active)
        self._set_button_active(self.stop_btn, not active)
        self.telemetry.set_hotspot(active, self.reported_client_count)

    def _apply_log_scale(self):
        h = max(600, self.height())
        # Responsive baseline: slightly larger on tall windows, capped for HUD density.
        size = max(8.0, min(13.0, 8.5 + (h - 600) / 260.0)) * self.telemetry_font_scale
        font = QFont("Consolas")
        font.setStyleHint(QFont.Monospace)
        font.setPointSizeF(max(7.0, min(16.0, size)))
        self.log.setFont(font)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_log_scale()

    def adjust_log_scale(self, delta):
        self.telemetry_font_scale = max(0.75, min(1.8, self.telemetry_font_scale + delta))
        self._apply_log_scale()

    def clear_log(self):
        self.log.clear()
        self.append_log("[SYSTEM] EVENT LOG CLEARED // LOCAL DATABASE RETAINED")

    @staticmethod
    def _log_color(message):
        text = str(message).upper()
        if "[ERROR]" in text or "CRITICAL" in text or "FAILED" in text:
            return "#ff5c8a"
        if "[WARN]" in text or "WARNING" in text:
            return "#ffd34d"
        if "[+]" in text or "[OK]" in text or "ONLINE" in text or "ACTIVE" in text:
            return "#61ffd2"
        if "[NET" in text or "CLIENT" in text:
            return "#59d7ff"
        if "[TELEMETRY]" in text or "[SYSTEM]" in text:
            return "#d58cff"
        return "#d7c7ff"

    def append_log(self, message):
        cursor = self.log.textCursor()
        cursor.movePosition(QTextCursor.End)
        if self.log.document().characterCount() > 2:
            cursor.insertText("\n")
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(self._log_color(message)))
        cursor.setCharFormat(fmt)
        cursor.insertText(str(message))
        self.log.setTextCursor(cursor)
        self.log.ensureCursorVisible()

    def hardware_scan(self):
        try:
            capability = scan_capabilities()
            self.interface.blockSignals(True)
            current = self.interface.currentText()
            self.interface.clear()
            for name in capability.wifi_interfaces:
                self.interface.addItem(name)
            if current:
                idx = self.interface.findText(current)
                if idx >= 0:
                    self.interface.setCurrentIndex(idx)
            self.interface.blockSignals(False)
            if capability.ready:
                self.hw_status.setText(f"HARDWARE: ✓ READY // {capability.selected_backend.upper()}")
                self.hw_status.setObjectName("hwGood")
                self.start_btn.setEnabled(True)
                if not self.hotspot_active:
                    self.state.setText(f"STATE: READY // {capability.selected_backend.upper()}")
            elif capability.wifi_interfaces:
                self.hw_status.setText("HARDWARE: ⚠ WI-FI FOUND // BACKEND LIMITED")
                self.hw_status.setObjectName("hwWarn")
                self.start_btn.setEnabled(False)
                if not self.hotspot_active:
                    self.state.setText("STATE: DIAGNOSTIC // BACKEND LIMITED")
            else:
                self.hw_status.setText("HARDWARE: ✕ NO WI-FI INTERFACE")
                self.hw_status.setObjectName("hwBad")
                self.start_btn.setEnabled(False)
                if not self.hotspot_active:
                    self.state.setText("STATE: BLOCKED // WI-FI NOT EXPOSED")
            self.append_log(
                f"[CAPABILITY] platform={capability.platform} env={capability.virtualization} "
                f"wifi={capability.wifi_interfaces or 'NONE'} backend={capability.selected_backend}"
            )
        except Exception as exc:
            self.start_btn.setEnabled(False)
            self.hw_status.setText("HARDWARE: ✕ SCAN FAILED")
            self.append_log(f"[ERROR] Capability scan failed: {exc}")

    def capability_scan(self):
        try:
            report = scan_capabilities()
            self.append_log(
                f"[CAPABILITY] ready={report.ready} backend={report.selected_backend} "
                f"wifi={report.wifi_interfaces or 'NONE'}"
            )
            CapabilityDialog(report, self).exec_()
            self.hardware_scan()
        except Exception as exc:
            self.append_log(f"[ERROR] Capability scan failed: {exc}")

    def refresh(self):
        try:
            self.interface.clear()
            for item in wireless_interfaces():
                self.interface.addItem(item.name)
        except Exception as exc:
            self.append_log(f"[WARN] {exc}")

    def live_refresh(self):
        # The background monitor does the expensive Windows/NetworkManager calls.
        snap = self.monitor.snapshot()
        if snap.updated_at:
            self.reported_client_count = snap.client_count
            self._set_hotspot_indicator(snap.active)
            if snap.active:
                self.state.setText(f"STATE: ONLINE // {snap.backend}")
            else:
                self.state.setText("STATE: READY // HOTSPOT OFF")
            self._render_clients(snap.clients, snap.client_count)
            self.telemetry_summary.setText(
                f"LOCAL: SQLite // /metrics // BACKEND: {snap.backend.upper()} // CLIENTS: {snap.client_count:02d}"
            )
            if snap.error and time.time() - self._last_status_log > 10:
                self._last_status_log = time.time()
                self.append_log(f"[WARN] BACKGROUND NETWORK MONITOR // {snap.error}")

        s = self.telemetry.snapshot()
        if s:
            self._render_metrics(s)
            self.telemetry.set_hotspot(snap.active, snap.client_count)

    def _render_clients(self, rows, authoritative):
        display_rows = list(rows)
        while len(display_rows) < authoritative:
            from .models import Client
            display_rows.append(Client("DETAILS PENDING", "WINDOWS TETHERING", "ENUMERATING DEVICE"))
        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(len(display_rows))
        for r, c in enumerate(display_rows):
            state = c.state or "ONLINE"
            device = "UNKNOWN DEVICE"
            if " // " in state:
                state, device = state.split(" // ", 1)
            values = (c.ip or "IP PENDING", c.mac or "MAC UNKNOWN", device, state)
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.table.setItem(r, col, item)
        self.table.setUpdatesEnabled(True)
        self.client_count.setText(f"● {authoritative:02d} ONLINE")

    @staticmethod
    def _human_bytes(value):
        value = float(value or 0)
        units = ("B/s", "KB/s", "MB/s", "GB/s")
        for unit in units:
            if value < 1024:
                return f"{value:.1f} {unit}"
            value /= 1024
        return f"{value:.1f} TB/s"

    @staticmethod
    def _human_size(value):
        value = float(value or 0)
        units = ("B", "KB", "MB", "GB", "TB")
        for unit in units:
            if value < 1024:
                return f"{value:.1f} {unit}"
            value /= 1024
        return f"{value:.1f} PB"

    @staticmethod
    def _uptime(value):
        value = int(value or 0)
        d, value = divmod(value, 86400)
        h, value = divmod(value, 3600)
        m, s = divmod(value, 60)
        return f"{d}d {h:02d}:{m:02d}:{s:02d}" if d else f"{h:02d}:{m:02d}:{s:02d}"

    def _render_metrics(self, s):
        values = {
            "cpu_percent": f"{s.cpu_percent:.1f}%",
            "memory_percent": f"{s.memory_percent:.1f}%",
            "swap_percent": f"{s.swap_percent:.1f}%",
            "net_rx_speed": self._human_bytes(s.net_rx_speed),
            "net_tx_speed": self._human_bytes(s.net_tx_speed),
            "disk_read_speed": self._human_bytes(s.disk_read_speed),
            "disk_write_speed": self._human_bytes(s.disk_write_speed),
            "process_count": f"{s.process_count}",
            "thread_count": f"{s.thread_count}",
            "process_memory_rss": self._human_size(s.process_memory_rss),
            "gc_counts": "/".join(map(str, s.gc_counts)),
            "uptime_seconds": self._uptime(s.uptime_seconds),
        }
        for key, value in values.items():
            label = self.metric_labels.get(key)
            if label:
                label.setText(value)
                if key in {"cpu_percent", "memory_percent"}:
                    num = float(str(value).rstrip("%"))
                    label.setObjectName("metricCritical" if num >= 95 else ("metricWarn" if num >= 85 else "metricValue"))
                    label.style().unpolish(label)
                    label.style().polish(label)
        self.log_status.setText(
            f"LOCAL EVENT STREAM // CPU {s.cpu_percent:.1f}% // RAM {s.memory_percent:.1f}% // "
            f"RX {self._human_bytes(s.net_rx_speed)} // TX {self._human_bytes(s.net_tx_speed)}"
        )

    def start(self):
        self.start_btn.setEnabled(False)
        try:
            capability = scan_capabilities()
            if not capability.ready:
                CapabilityDialog(capability, self).exec_()
                return
            config = HotspotConfig(
                ssid=self.ssid.text().strip(),
                password=self.password.text(),
                interface=self.interface.currentText() or None,
                shared=self.shared.isChecked(),
            )
            name = self.backend.start(config)
            self._set_hotspot_indicator(True)
            self.state.setText(f"STATE: ONLINE // {name}")
            self.append_log(f"[+] HOTSPOT STARTED // {self.backend.backend_name}")
            self.append_log(f"[HOTSPOT] SSID={config.ssid} // LIVE CLIENT MONITORING ENABLED")
            self.hardware_scan()
        except PermissionError as exc:
            QMessageBox.warning(self, "CyberHotspot // Administrator Required", str(exc))
            self.append_log(f"[WARN] {exc}")
        except Exception as exc:
            self._set_hotspot_indicator(False)
            QMessageBox.critical(self, "CyberHotspot // Start Failed", str(exc))
            self.append_log(f"[ERROR] START FAILED // {exc}")
        finally:
            self.start_btn.setEnabled(True)

    def stop(self):
        try:
            self.backend.stop()
            self._set_hotspot_indicator(False)
            self.state.setText("STATE: OFFLINE // HOTSPOT STOPPED")
            self.reported_client_count = 0
            self.client_count.setText("● 00 ONLINE")
            self.telemetry_summary.setText(f"LOCAL: SQLite // /metrics // CLIENTS: 00")
            self.table.setRowCount(0)
            self.append_log("[+] HOTSPOT STOPPED.")
        except Exception as exc:
            QMessageBox.warning(self, "CyberHotspot", str(exc))
            self.append_log(f"[ERROR] STOP FAILED // {exc}")

    def status(self):
        # Status is read from the already-running background monitor.
        snap = self.monitor.snapshot()
        self.append_log("[STATUS]")
        self.append_log(snap.raw_status or "No status sample yet.")
        self.append_log(
            f"[TELEMETRY] CPU={self.metric_labels['cpu_percent'].text()} "
            f"RAM={self.metric_labels['memory_percent'].text()} CLIENTS={snap.client_count}"
        )

    def run_doctor(self):
        report = doctor()
        self.append_log("[DOCTOR] Diagnostic scan")
        for x in report.checks:
            self.append_log("[OK] " + x)
        for x in report.warnings:
            self.append_log("[WARN] " + x)
        for x in report.errors:
            self.append_log("[ERROR] " + x)

    def closeEvent(self, event):
        try:
            self.monitor.stop()
            self.telemetry.stop()
        finally:
            event.accept()


def main():
    app = QApplication(sys.argv)
    window = CyberHotspotWindow()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
