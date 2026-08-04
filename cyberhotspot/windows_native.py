"""Native Windows Mobile Hotspot backend using PyWinRT.

Requires a Windows package identity with the wiFiControl device capability.
This is the supported API used by Windows Mobile Hotspot, not legacy
netsh hostednetwork.
"""
import os
import asyncio
from typing import Dict, List


def _imports():
    from winrt.windows.networking.connectivity import NetworkInformation
    from winrt.windows.networking.networkoperators import (
        NetworkOperatorTetheringAccessPointConfiguration,
        NetworkOperatorTetheringManager,
    )
    return NetworkInformation, NetworkOperatorTetheringAccessPointConfiguration, NetworkOperatorTetheringManager


def _manager():
    NetworkInformation, _, Manager = _imports()
    profile = NetworkInformation.get_internet_connection_profile()
    if profile is None:
        raise RuntimeError("Windows has no active Internet connection profile.")
    return Manager.create_from_connection_profile(profile)


def _get_capability():
    NetworkInformation, _, Manager = _imports()
    profile = NetworkInformation.get_internet_connection_profile()
    if profile is None:
        return "NoInternetConnectionProfile"
    return str(Manager.get_tethering_capability_from_connection_profile(profile))


def probe() -> Dict:
    if os.name != "nt":
        raise RuntimeError("Windows Mobile Hotspot backend requires Windows.")
    try:
        manager = _manager()
        return {
            "available": True,
            "capability": _get_capability(),
            "state": str(manager.tethering_operational_state),
            "client_count": int(manager.client_count),
            "max_clients": int(manager.max_client_count),
            "package_identity_required": False,
        }
    except Exception as exc:
        message = str(exc)
        capability = "unknown"
        try:
            capability = _get_capability()
        except Exception:
            pass
        return {
            "available": False,
            "capability": capability,
            "state": "Unknown",
            "client_count": 0,
            "max_clients": 0,
            "package_identity_required": "DisabledBySystemCapability" in message or "capability" in message.lower(),
            "error": message,
        }


def start(ssid: str, password: str) -> Dict:
    if not (8 <= len(password) <= 63):
        raise ValueError("Windows Mobile Hotspot passphrase must contain 8–63 characters.")
    NetworkInformation, Config, _ = _imports()
    manager = _manager()
    cfg = Config()
    cfg.ssid = ssid
    cfg.passphrase = password
    cfg_result = manager.configure_access_point_async(cfg).get()
    result = manager.start_tethering_async().get()
    return {
        "status": str(result.status),
        "additional_error": str(result.additional_error_message),
        "ssid": ssid,
        "state": str(manager.tethering_operational_state),
    }


def stop() -> Dict:
    manager = _manager()
    result = manager.stop_tethering_async().get()
    return {"status": str(result.status), "additional_error": str(result.additional_error_message)}


def status() -> Dict:
    manager = _manager()
    cfg = manager.get_current_access_point_configuration()
    return {
        "capability": _get_capability(),
        "state": str(manager.tethering_operational_state),
        "ssid": str(cfg.ssid),
        "client_count": int(manager.client_count),
        "max_clients": int(manager.max_client_count),
    }


def clients() -> List[Dict]:
    manager = _manager()
    out = []
    for client in manager.get_tethering_clients():
        out.append({
            "mac": str(client.mac_address),
            "hosts": [str(h.display_name) for h in client.host_names],
        })
    return out
