# Hardware

MurOS runs on anything that runs Debian 13. Because it is built on stock
Debian, you get the full Linux driver set: mini-PCs, rack servers, VMs and
recent or inexpensive NICs that the BSD-based original often will not drive.
Below are realistic sizing brackets, for both bare metal and VMs.

## Minimum

* CPU: 1 vCPU, x86_64 (amd64). No special instructions required.
* RAM: 1 GB. The base stack (web UI, php-fpm, nftables) is light at idle.
* Disk: 8 GB. Mostly Debian and the MurOS package.
* NIC: 1 interface for management, 2 or more for WAN / LAN segmentation.

A small fanless thin client is enough for a home lab or a small office under
50 Mbps.

## Sizing by throughput

These brackets assume stateful filtering plus NAT and a couple of WireGuard or
IPsec tunnels.

| Target | CPU | RAM | Notes |
| --- | --- | --- | --- |
| Home / 100 Mbps | 1 vCPU | 1 GB | thin client, small VM |
| SMB / 500 Mbps | 2 vCPU | 2 GB | Intel N5105 / N100 mini-PC |
| Office / 1 Gbps | 4 vCPU | 4 GB | i3 / Ryzen 3 with Intel i225 / i226 NICs |
| Datacenter / 10 Gbps | 8+ vCPU | 8 GB+ | Xeon / EPYC, Intel X710 / Mellanox ConnectX-4, AES-NI for VPN |

## Recommended boxes

* Fanless Intel N100 / N305 mini-PC with 4x Intel i226-V: the sweet spot for
  home and small office, gigabit-class.
* Protectli and similar turnkey Intel-NIC firewall boxes: well documented
  under Debian.
* Generic 1U rack server with 2 to 4x Intel X710: when you need 10 Gbps.
* VMware, Proxmox or KVM VM: virtio-net works out of the box.

## Network cards

* Intel i210 / i225 / i226 / X710: first choice. Mature kernel driver, robust
  under load.
* Mellanox ConnectX-4 / 5: 10 / 25 / 40 Gbps, good offloads.
* Realtek r8168 / r8125: works, but the proprietary driver can misbehave under
  heavy load. Avoid in production.

## High availability

Active/passive HA needs two MurOS nodes running the same package version, with
matching interface assignments and a dedicated link (or VLAN) between them for
VRRP advertisements and conntrack sync. Identical hardware is recommended but
not required: keepalived handles virtual-IP failover and conntrackd replays
sessions on the backup so existing connections survive a takeover. See the
High availability page for the full setup.

## Power and form factor

A typical N100 mini-PC pulls 7 to 12 W under load, fits a shelf or a DIN rail,
and runs silent. A 1U appliance with two Xeon and 25 GbE pulls 80 to 150 W.
Pick the form factor that matches your environment first, then size up if
needed.
