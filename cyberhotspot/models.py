from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class InterfaceInfo:
    name: str
    kind: str = ""
    state: str = ""
    connection: str = ""
    driver: str = ""
    supports_ap: Optional[bool] = None


@dataclass
class Client:
    ip: str
    mac: str
    state: str = ""
    interface: str = ""


@dataclass
class HotspotConfig:
    ssid: str
    password: str
    interface: Optional[str] = None
    connection_name: str = "CyberHotspot"
    shared: bool = False
    band: Optional[str] = None
    channel: Optional[int] = None

    def validate(self) -> None:
        if not 1 <= len(self.ssid) <= 32:
            raise ValueError("SSID must contain 1-32 characters.")
        if len(self.password) < 8:
            raise ValueError("WPA password must contain at least 8 characters.")
        if len(self.password) > 63:
            raise ValueError("WPA password must contain at most 63 characters.")
        if self.channel is not None and not 1 <= self.channel <= 196:
            raise ValueError("Wi-Fi channel is outside the supported numeric range.")


@dataclass
class DoctorReport:
    checks: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors
