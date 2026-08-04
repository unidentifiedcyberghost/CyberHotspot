import re, os
from typing import List
from .models import Client, InterfaceInfo
from .runner import CommandError, run, which

def require_nmcli():
    if os.name=="nt": raise CommandError("Linux NetworkManager backend requested on Windows.")
    if not which("nmcli"): raise CommandError("nmcli was not found. Install NetworkManager.")

def interfaces() -> List[InterfaceInfo]:
    if os.name=="nt":
        from .windows_backend import wifi_interfaces
        return wifi_interfaces()
    require_nmcli(); result=run(["nmcli","-t","-f","DEVICE,TYPE,STATE,CONNECTION","device"]); items=[]
    for line in result.stdout.splitlines():
        parts=line.split(":",3)
        if len(parts)==4: items.append(InterfaceInfo(*parts))
    return items

def wireless_interfaces():
    return [x for x in interfaces() if x.kind in ("wifi","802-11-wireless")]

def ap_capable(iface=""):
    if os.name=="nt":
        from .windows_backend import hosted_network_supported
        return hosted_network_supported()
    if not which("iw"): return False
    return bool(re.search(r"(?m)^\s*\*?\s*AP\s*$",run(["iw","list"],check=False).stdout))

def clients() -> List[Client]:
    if os.name=="nt":
        from .windows_backend import clients as win_clients
        return win_clients()
    out=[]
    for line in run(["ip","neigh","show"],check=False).stdout.splitlines():
        fields=line.split()
        if not fields: continue
        ip=fields[0]; mac=""; state=""
        for i,v in enumerate(fields):
            if v.upper()=="LLADDR" and i+1<len(fields): mac=fields[i+1]
            if v.upper() in {"REACHABLE","STALE","DELAY","PROBE","FAILED","INCOMPLETE"}: state=v.upper()
        if mac: out.append(Client(ip,mac,state))
    return out

def scan(iface=""):
    if os.name=="nt":
        from .windows_backend import driver_report
        return driver_report()
    require_nmcli(); command=["nmcli","-f","IN-USE,SSID,CHAN,RATE,SIGNAL,SECURITY","device","wifi","list"]
    if iface: command += ["ifname",iface]
    return run(command,check=False).stdout
