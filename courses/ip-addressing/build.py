#!/usr/bin/env python3
"""Generates ip-addressing-course.html (tables are computed, answers are checked)."""
import ipaddress as ia, re, pathlib
here = pathlib.Path(__file__).parent
css = re.search(r"<style>(.*?)</style>", (here.parent / "network-commands" / "network-commands-course.html").read_text(), re.S).group(1)
css += """
  .bits { font-family: "DejaVu Sans Mono", monospace; letter-spacing: 1px; }
  .n { color:#1f4e79; font-weight:bold; } .h { color:#c62828; font-weight:bold; } .s { color:#2e7d32; font-weight:bold; }
  pre .n { color:#6cb6ff; } pre .s { color:#8be28b; } pre .h { color:#ff8a80; }
  td.c, th.c { text-align:center; }
  .bt td { text-align:center; font-family:"DejaVu Sans Mono",monospace; }
  .small table { font-size: 8.4pt; } .small td { padding: 2px 5px; }
"""

def b8(x): return format(x, "08b")
def bip(ip): return ".".join(b8(int(o)) for o in str(ip).split("."))

# ---------- computed tables ----------
cidr_rows = ""
for p in range(8, 33):
    n = ia.ip_network(f"0.0.0.0/{p}")
    total = 2 ** (32 - p)
    usable = {31: "2 (point-to-point, RFC 3021)", 32: "1 (single host)"}.get(p, f"{total-2:,}")
    cidr_rows += f"<tr><td class=c>/{p}</td><td>{n.netmask}</td><td>{n.hostmask}</td><td>{total:,}</td><td>{usable}</td></tr>"

pow_rows = "".join(f"<tr><td class=c>2<sup>{k}</sup></td><td>{2**k:,}</td><td class=c>2<sup>{k+12}</sup></td><td>{2**(k+12):,}</td></tr>" for k in range(0, 12))
pow_rows += "<tr><td class=c>…</td><td></td><td class=c>2<sup>32</sup></td><td>4,294,967,296</td></tr>"

def subnet_table(net, newp, limit=None):
    rows = ""
    for i, s in enumerate(ia.ip_network(net).subnets(new_prefix=newp)):
        if limit and i >= limit: rows += "<tr><td colspan=6 class=c>…</td></tr>"; break
        h = list(s.hosts()) if s.prefixlen < 31 else []
        rows += f"<tr><td class=c>{i+1}</td><td>{s}</td><td>{h[0]}</td><td>{h[-1]}</td><td>{s.broadcast_address}</td><td>{s.num_addresses-2:,}</td></tr>"
    return "<table><tr><th class=c>#</th><th>Subnet</th><th>First host</th><th>Last host</th><th>Broadcast</th><th>Hosts</th></tr>" + rows + "</table>"

def info(addr):
    i = ia.ip_interface(addr); n = i.network; h = list(n.hosts())
    return dict(mask=n.netmask, net=n.network_address, bc=n.broadcast_address, first=h[0], last=h[-1], hosts=f"{n.num_addresses-2:,}")

def vlsm(base, needs):
    cur = ia.ip_network(base).network_address; rows = ""
    for name, hosts in needs:
        p = 32
        while 2 ** (32 - p) - 2 < hosts: p -= 1
        s = ia.ip_network(f"{cur}/{p}"); h = list(s.hosts())
        rows += f"<tr><td>{name}</td><td class=c>{hosts}</td><td class=c>/{p} ({s.num_addresses-2})</td><td>{s}</td><td>{s.netmask}</td><td>{h[0]} – {h[-1]}</td><td>{s.broadcast_address}</td></tr>"
        cur = s.broadcast_address + 1
    return ("<table><tr><th>Network</th><th>Hosts needed</th><th>Prefix (usable)</th><th>Subnet</th><th>Mask</th><th>Host range</th><th>Broadcast</th></tr>" + rows + "</table>", cur)

# ---------- checks of every worked example and answer ----------
def chk(a, **exp):
    got = info(a)
    for k, v in exp.items(): assert str(got[k]) == v, (a, k, got[k], v)
chk("192.168.10.77/26", net="192.168.10.64", bc="192.168.10.127", first="192.168.10.65", last="192.168.10.126", hosts="62")
chk("172.16.45.200/20", mask="255.255.240.0", net="172.16.32.0", bc="172.16.47.255", hosts="4,094")
chk("10.45.123.77/13", mask="255.248.0.0", net="10.40.0.0", bc="10.47.255.255", hosts="524,286")
chk("192.168.50.130/27", net="192.168.50.128", bc="192.168.50.159", hosts="30")
chk("172.20.99.14/19", net="172.20.96.0", bc="172.20.127.255", hosts="8,190")
chk("10.200.17.5/10", mask="255.192.0.0", net="10.192.0.0", bc="10.255.255.255", hosts="4,194,302")
chk("192.168.1.255/23", net="192.168.0.0", bc="192.168.1.255")
chk("200.15.7.99/29", net="200.15.7.96", bc="200.15.7.103", first="200.15.7.97", last="200.15.7.102", hosts="6")
assert list(ia.collapse_addresses([ia.ip_network(f"192.168.{i}.0/24") for i in range(4)])) == [ia.ip_network("192.168.0.0/22")]
assert list(ia.collapse_addresses([ia.ip_network(f"172.16.{i}.0/24") for i in range(12, 16)])) == [ia.ip_network("172.16.12.0/22")]
assert list(ia.collapse_addresses([ia.ip_network(f"10.1.{i}.0/24") for i in range(64, 128)])) == [ia.ip_network("10.1.64.0/18")]
assert [str(x) for x in ia.collapse_addresses([ia.ip_network(f"192.168.{i}.0/24") for i in range(1, 5)])] == ["192.168.1.0/24", "192.168.2.0/23", "192.168.4.0/24"]
assert list(ia.collapse_addresses([ia.ip_network(f"172.16.{i}.0/24") for i in range(32, 36)])) == [ia.ip_network("172.16.32.0/22")]
assert list(ia.collapse_addresses([ia.ip_network(f"10.0.{i}.0/24") for i in range(8, 16)])) == [ia.ip_network("10.0.8.0/21")]
assert list(ia.collapse_addresses([ia.ip_network("198.51.100.0/25"), ia.ip_network("198.51.100.128/25")])) == [ia.ip_network("198.51.100.0/24")]
assert str(ia.ip_address("2001:0db8:0000:0000:0001:0000:0000:0001")) == "2001:db8::1:0:0:1"
assert str(ia.ip_address("2001:0db8:0000:0000:0000:ff00:0042:8329")) == "2001:db8::ff00:42:8329"
assert ia.ip_address("fe80::1").exploded == "fe80:0000:0000:0000:0000:0000:0000:0001"
assert not ia.ip_address("172.32.1.1").is_private and ia.ip_address("172.31.255.1").is_private
for d, b in [(172, "10101100"), (200, "11001000"), (99, "01100011"), (7, "00000111"), (214, "11010110")]: assert b8(d) == b
assert [int(x, 2) for x in ("10110111", "01111111", "11100000")] == [183, 127, 224]
vl1, _ = vlsm("192.168.10.0/24", [("LAN A", 100), ("LAN B", 50), ("LAN C", 25), ("LAN D", 10), ("WAN 1", 2), ("WAN 2", 2), ("WAN 3", 2)])
vl2, _ = vlsm("10.10.0.0/24", [("Sales", 60), ("Tech", 28), ("Admin", 12), ("Link R1–R2", 2)])

i1 = info("172.16.45.200/20"); i2 = info("10.45.123.77/13")

html = (here / "ip-addressing-course.src.html").read_text()
for k, v in dict(CSS=css, CIDR=cidr_rows, POW=pow_rows, VLSM1=vl1, VLSM2=vl2,
                 FLSM1=subnet_table("192.168.1.0/24", 26), FLSM8=subnet_table("192.168.100.0/24", 27),
                 FLSMB=subnet_table("172.16.0.0/16", 23, limit=5), FLSMA=subnet_table("10.0.0.0/8", 12, limit=5),
                 B172=bip("172.16.45.200"), B10=bip("10.45.123.77")).items():
    html = html.replace("{{" + k + "}}", str(v))
assert "{{" not in html
(here / "ip-addressing-course.html").write_text(html)
print("ok")
