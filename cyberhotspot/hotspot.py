from typing import Optional
from .models import HotspotConfig
from .network import require_nmcli
from .runner import CommandError, run


class NetworkManagerBackend:
    """NetworkManager-backed hotspot implementation.

    NetworkManager handles DHCP/NAT/DNS for `ipv4.method shared`, reducing
    fragile firewall manipulation and distro-specific service coordination.
    """

    def start(self, config: HotspotConfig) -> str:
        config.validate()
        require_nmcli()
        command = ["nmcli", "device", "wifi", "hotspot"]
        if config.interface:
            command += ["ifname", config.interface]
        command += ["ssid", config.ssid, "password", config.password]
        run(command)

        active = run(
            ["nmcli", "-t", "-f", "NAME,TYPE,DEVICE", "connection", "show", "--active"],
            check=False,
        )
        name = ""
        for line in active.stdout.splitlines():
            parts = line.split(":", 2)
            if len(parts) == 3 and parts[1] == "802-11-wireless":
                name = parts[0]
                break
        name = name or config.connection_name

        if config.connection_name and name != config.connection_name:
            run(["nmcli", "connection", "modify", name, "connection.id", config.connection_name], check=False)
            name = config.connection_name

        if config.shared:
            run(["nmcli", "connection", "modify", name, "ipv4.method", "shared"])
            run(["nmcli", "connection", "up", name])
        return name

    def stop(self, connection_name: Optional[str] = None) -> None:
        require_nmcli()
        name = connection_name or self.find_active()
        if not name:
            return
        run(["nmcli", "connection", "down", name], check=False)
        run(["nmcli", "connection", "delete", name], check=False)

    def restart(self, config: HotspotConfig) -> str:
        self.stop(config.connection_name)
        return self.start(config)

    def find_active(self) -> str:
        result = run(
            ["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show", "--active"],
            check=False,
        )
        for line in result.stdout.splitlines():
            parts = line.split(":", 1)
            if len(parts) == 2 and parts[1] == "802-11-wireless":
                return parts[0]
        return ""

    def status(self) -> str:
        require_nmcli()
        return run(["nmcli", "-f", "GENERAL,IP4,WIRED-PROPERTIES", "device", "show"], check=False).stdout
