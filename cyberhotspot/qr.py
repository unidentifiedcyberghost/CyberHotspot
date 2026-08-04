from pathlib import Path


def wifi_payload(ssid: str, password: str, security: str = "WPA") -> str:
    def esc(value: str) -> str:
        return value.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace(":", "\\:")
    return f"WIFI:T:{security};S:{esc(ssid)};P:{esc(password)};;"


def write_png(ssid: str, password: str, output: str) -> str:
    try:
        import qrcode
    except ImportError as exc:
        raise RuntimeError("Install qrcode[pil] to create PNG QR codes.") from exc
    img = qrcode.make(wifi_payload(ssid, password))
    path = Path(output).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    return str(path)
