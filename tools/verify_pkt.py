"""Decodifica el .pkt de Packet Tracer y verifica la configuración esperada del laboratorio.

Uso: python tools/verify_pkt.py packet-tracer/Temperature_Control_System.pkt
Sale con código 1 si alguna verificación falla.
"""
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pkt_codec import decode  # noqa: E402


def devices(root):
    return {d.find("ENGINE").findtext("NAME"): d.find("ENGINE") for d in root.find("NETWORK/DEVICES")}


def lines(engine, tag):
    node = engine.find(tag)
    return [l.text or "" for l in node] if node is not None else []


def main(path):
    xml = decode(open(path, "rb").read())
    root = ET.fromstring(xml)
    dev = devices(root)
    checks = []

    def check(name, ok):
        checks.append((name, bool(ok)))

    isp = dev["ISP"]
    run = lines(isp, "RUNNINGCONFIG")
    start = lines(isp, "STARTUPCONFIG")
    check("ISP: interfaz Gi0/0 10.0.0.1/24", "ip address 10.0.0.1 255.255.255.0" in [l.strip() for l in run])
    check("ISP: interfaz Gi0/1 209.165.200.225/27", "ip address 209.165.200.225 255.255.255.224" in [l.strip() for l in run])
    check("ISP: interfaz Gi0/2 209.165.201.225/27", "ip address 209.165.201.225 255.255.255.224" in [l.strip() for l in run])
    check("ISP: pool WAN con default-router .225", " default-router 209.165.200.225" in run)
    check("ISP: pool CELL con default-router .225", " default-router 209.165.201.225" in run)
    check("ISP: ningún default-router apunta a broadcast", not any(re.search(r"default-router \S+\.255$", l) for l in run))
    check("ISP: excluded-address con rangos válidos", all(
        int(a.split(".")[-1]) <= int(b.split(".")[-1])
        for a, b in re.findall(r"ip dhcp excluded-address (\S+) (\S+)", "\n".join(run))))
    check("ISP: DNS 10.0.0.254 entregado por DHCP", run.count(" dns-server 10.0.0.254") == 2)
    check("ISP: startup-config guardada (= running)", start == run)

    dns = dev["DNS-SERVER"]
    recs = {r.findtext("NAME"): r.findtext("IPADDRESS") for r in dns.iter("RESOURCE-RECORD")}
    check("DNS-SERVER: servicio DNS activo", dns.findtext("DNS_SERVER/ENABLED") == "1")
    check("DNS-SERVER: iot.com -> 10.0.0.253", recs.get("iot.com") == "10.0.0.253")
    check("DNS-SERVER: www.iot.com -> 10.0.0.253", recs.get("www.iot.com") == "10.0.0.253")

    iot = dev["IOT-SERVER"]
    check("IOT-SERVER: IP 10.0.0.253", any(p.findtext("IP") == "10.0.0.253" for p in iot.iter("PORT")))
    check("IOT-SERVER: servicio IoT (registro) activo", iot.findtext("REGISTRATION_SEVER") == "true")
    users = {u.findtext("NAME"): u for u in iot.iter("USER")}
    check("IOT-SERVER: usuario admin", "admin" in users)
    registered = {d.findtext("TYPE") for d in users["admin"].iter("IOE_DEVICE")} if "admin" in users else set()
    check("IOT-SERVER: Thermostat y Temperature Monitor registrados", {"Thermostat", "Temperature Monitor"} <= registered)

    for name in ("Thermostat", "Temperature"):
        e = dev[name]
        check(f"{name}: cliente IoT remoto -> 10.0.0.253",
              e.findtext("IOE_CLIENT/CLIENT_MODE") == "REMOTE_SERVER" and e.findtext("IOE_CLIENT/SERVER_ADDRESS") == "10.0.0.253")

    g1, g2 = dev["Office - 1 Gateway"], dev["Office - 2 Gateway"]
    check("Gateway Oficina 1: gateway WAN .225", g1.findtext("DEFAULT_GATEWAY") == "209.165.200.225")
    check("Gateway Oficina 2: gateway WAN .225", g2.findtext("DEFAULT_GATEWAY") == "209.165.201.225")
    s1, s2 = g1.findtext("WIRELESS_SERVER/WIRELESS_COMMON/SSID"), g2.findtext("WIRELESS_SERVER/WIRELESS_COMMON/SSID")
    check("Oficinas con SSID distintos", s1 != s2)
    check("laptop - 2 usa el SSID de Oficina 2", dev["laptop - 2"].findtext("WIRELESS_CLIENT/WIRELESS_COMMON/SSID") == s2)

    width = max(len(n) for n, _ in checks)
    for name, ok in checks:
        print(f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}")
    failed = [n for n, ok in checks if not ok]
    print(f"\n{len(checks) - len(failed)}/{len(checks)} verificaciones OK")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "packet-tracer/Temperature_Control_System.pkt"))
