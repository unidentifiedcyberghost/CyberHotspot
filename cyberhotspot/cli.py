import argparse, sys, os
from . import __version__
from .diagnostics import doctor
from .backend_manager import BackendManager
from .capabilities import scan_capabilities
from .models import HotspotConfig
from .network import clients, interfaces, scan
from .qr import write_png
from .telemetry import TelemetryEngine

def build_parser():
    p=argparse.ArgumentParser(prog="cyberhotspot",description="Cross-platform Wi-Fi hotspot manager")
    p.add_argument("--version",action="version",version=__version__)
    sub=p.add_subparsers(dest="command",required=True)
    s=sub.add_parser("start"); s.add_argument("--ssid",required=True); s.add_argument("--password",required=True); s.add_argument("--interface","--ifname"); s.add_argument("--connection-name",default="CyberHotspot"); s.add_argument("--shared",action="store_true")
    st=sub.add_parser("stop"); st.add_argument("--connection-name",default="CyberHotspot")
    for x in ("status","interfaces","clients","doctor","hardware","capabilities"): sub.add_parser(x)
    tm = sub.add_parser("telemetry", help="Show local system telemetry")
    tm.add_argument("--watch", action="store_true", help="Continuously print local telemetry")
    tm.add_argument("--interval", type=float, default=1.0)
    sub.add_parser("metrics", help="Print the local Prometheus-compatible metrics payload")
    sc=sub.add_parser("scan"); sc.add_argument("--interface","--ifname",default="")
    q=sub.add_parser("qr"); q.add_argument("--ssid",required=True); q.add_argument("--password",required=True); q.add_argument("--out",required=True)
    return p

def main(argv=None):
    args=build_parser().parse_args(argv); manager=BackendManager()
    try:
        if args.command=="start":
            print("[+] Hotspot active:",manager.start(HotspotConfig(args.ssid,args.password,args.interface,args.connection_name,args.shared)))
        elif args.command=="stop": manager.stop(args.connection_name); print("[+] Hotspot stopped.")
        elif args.command=="status": print(manager.status())
        elif args.command=="interfaces":
            for x in interfaces(): print(f"{x.name:22} {x.kind:8} {x.state:12} {x.connection}")
        elif args.command=="clients":
            for c in manager.clients(): print(f"{c.ip:16} {c.mac:18} {c.state}")
        elif args.command=="scan": print(scan(args.interface))
        elif args.command in ("capabilities","hardware"):
            r=scan_capabilities()
            print("=== CYBERHOTSPOT NETWORK CAPABILITY ENGINE ===")
            print("Platform:",r.platform); print("Environment:",r.virtualization)
            print("Wi-Fi:",", ".join(r.wifi_interfaces) or "NONE"); print("AP-capable:",", ".join(r.ap_interfaces) or "NONE")
            print("Backends:",", ".join(r.backends) or "NONE"); print("Selected backend:",r.selected_backend); print("Hotspot ready:","YES" if r.ready else "NO")
            if os.name == "nt":
                print("Legacy Hosted Network:", "YES" if any("Legacy Hosted Network: Yes" in x for x in r.driver_hints) else "NO")
            for x in r.driver_hints: print("[DRIVER]",x)
            for x in r.reasons: print("[REASON]",x)
            for x in r.recommendations: print("[NEXT]",x)
            return 0 if r.ready else 2
        elif args.command=="doctor":
            rep=doctor()
            for x in rep.checks: print("[OK]",x)
            for x in rep.warnings: print("[WARN]",x)
            for x in rep.errors: print("[ERROR]",x)
            return 1 if rep.errors else 0
        elif args.command=="telemetry":
            engine = TelemetryEngine(interval=args.interval)
            engine.start()
            try:
                while True:
                    import time
                    deadline = time.time() + max(0.2, args.interval)
                    while engine.snapshot() is None and time.time() < deadline + 1.0:
                        time.sleep(0.1)
                    snap = engine.snapshot()
                    if snap:
                        print(
                            f"CPU={snap.cpu_percent:5.1f}% "
                            f"RAM={snap.memory_percent:5.1f}% "
                            f"SWAP={snap.swap_percent:5.1f}% "
                            f"RX={snap.net_rx_speed/1024/1024:6.2f}MB/s "
                            f"TX={snap.net_tx_speed/1024/1024:6.2f}MB/s "
                            f"DISK-R={snap.disk_read_speed/1024/1024:6.2f}MB/s "
                            f"DISK-W={snap.disk_write_speed/1024/1024:6.2f}MB/s "
                            f"PROC={snap.process_count} THREADS={snap.thread_count} "
                            f"CLIENTS={snap.client_count}"
                        )
                    if not args.watch:
                        break
            except KeyboardInterrupt:
                pass
            finally:
                engine.stop()
        elif args.command=="metrics":
            engine = TelemetryEngine(interval=0.5)
            engine.start()
            try:
                import time
                deadline = time.time() + 2.0
                while engine.snapshot() is None and time.time() < deadline:
                    time.sleep(0.1)
                print(engine.prometheus_text(), end="")
            finally:
                engine.stop()
        elif args.command=="qr": print("[+] QR written to",write_png(args.ssid,args.password,args.out))
        return 0
    except Exception as exc:
        print("[ERROR]",exc,file=sys.stderr); return 1
if __name__=="__main__": raise SystemExit(main())
