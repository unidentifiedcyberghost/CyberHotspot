import os
from .hotspot import NetworkManagerBackend
from .windows_backend import start as windows_start, stop as windows_stop, status as windows_status, clients as windows_clients


class BackendManager:
    def __init__(self):
        self.platform = "windows" if os.name == "nt" else "linux"
        self.backend_name = "windows-mobile-hotspot" if self.platform == "windows" else "networkmanager"
        self._linux = NetworkManagerBackend()

    def start(self, config):
        return windows_start(config) if self.platform == "windows" else self._linux.start(config)

    def stop(self, connection_name=None):
        return windows_stop() if self.platform == "windows" else self._linux.stop(connection_name)

    def status(self):
        return windows_status() if self.platform == "windows" else self._linux.status()

    def clients(self):
        if self.platform == "windows":
            return windows_clients()
        from .network import clients
        return clients()
