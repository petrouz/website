# MurOS, first deployment

MurOS is a fork of OPNsense ported to Debian 13. There are two ways to install
it, and both give the same system:

* Option A (recommended): the installer ISO. It boots and installs itself
  offline, no Linux to assemble and no command line.
* Option B: on an existing Debian 13. Install the package on top of a server
  you already provisioned.

MurOS targets Debian 13 (Trixie), amd64. Other distributions (Ubuntu, Rocky,
RHEL) are not supported: MurOS relies on Debian-specific drop-in paths.
Whatever the install path, later upgrades flow through apt.

## Hardware

An x86_64 machine (VM or bare metal) with at least 1 vCPU, 2 GB RAM, 8 GB disk
and two network interfaces (one WAN, one LAN). 2 vCPU and 4 GB are comfortable.
See the Hardware page for sizing by throughput.

---

## Option A: the installer ISO (recommended)

1. Download the ISO from the Install page and write it to a USB key (`dd`,
   Rufus, balenaEtcher), or attach it to a VM.
2. Boot the machine and pick Install MurOS. Choose your keyboard layout, then
   the LAN interface and its static IP. The rest of the install runs offline.
3. After reboot, open `https://<the-LAN-IP>/` in any browser and accept the
   self-signed certificate. Log in as `root` with the default password
   `muros`. Change it right away under System > Access > Users.

The LAN address you set during install is what MurOS uses. A firewall LAN is
static, never DHCP: it is set once at install and not changed from the UI.

---

## Option B: on an existing Debian 13 (advanced)

Prerequisites:

* A clean Debian 13 (Trixie) install, server profile (no desktop).
* Root access (the install script must run as root).
* At least one network interface reachable from the management subnet.
* Outbound HTTPS to `download.muros.org` for the repository and package.

Run as root on the target machine:

```bash
curl -fsSL https://download.muros.org/install.sh | sudo bash
```

The script imports the repository signing key, writes
`/etc/apt/sources.list.d/muros.list`, removes competing network managers that
conflict with the firewall control plane, and installs the `muros` package.
When it finishes, open `https://<firewall-ip>/` and log in as `root` /
`muros`, then change the password.

---

## Upgrades

Every install, ISO included, upgrades the same way:

```bash
apt update && apt install --only-upgrade muros
```

---

## Configure the firewall

MurOS stages every change in `/conf/config.xml` first; nothing touches the
kernel until you Apply. On a firewall apply the generated nftables ruleset is
checked with `nft -c` before it is loaded, and every ruleset carries a
mandatory anti-lockout rule (SSH and the web UI from the management network),
so an applied ruleset cannot strand you. Always verify you still have access
after an apply.

### 1. Interfaces (Interfaces > Assignments, then WAN / LAN)

WAN: open the WAN interface, set its addressing to static or DHCP depending on
your uplink. If static, set the IP with its CIDR mask, gateway and DNS. Save.

LAN (Option B only, the ISO already set it): open the LAN interface, static
addressing, for example `10.0.0.1/24`. Save, then Apply.

### 2. Firewall rules (Firewall > Rules)

Rules attach to the interface where traffic enters. The defaults already let
the LAN out and keep the WAN closed, so you mainly add what you want to open:

* On LAN: a pass rule, source LAN net, destination any, lets the LAN reach the
  Internet (present by default).
* On LAN: a pass rule to the firewall on TCP 22 and 443 for SSH and the UI.

The WAN keeps no rule toward the firewall, so the box stays closed from the
Internet. Click Apply, then check you still have access.

### 3. Outbound NAT (Firewall > NAT > Outbound)

Leave outbound NAT on automatic and the LAN reaches the Internet behind the
WAN address. Switch to manual only if you need custom source NAT.

---

## Test from a LAN host

Plug a PC into the LAN, static IP `10.0.0.50/24`, gateway `10.0.0.1`, DNS
`1.1.1.1`. From the PC:

```bash
ping 10.0.0.1              # firewall reachable
ping 1.1.1.1               # Internet OK
curl -k https://10.0.0.1/  # UI reachable from LAN
```

If everything responds, your firewall is running.

---

## Locked out?

The console always keeps root access. If a too-strict rule or a wrong address
change locks the UI, reload the ruleset from the console:

```bash
nft flush ruleset
systemctl restart muros-firewall
```

The anti-lockout baseline comes back and the UI is reachable again. See the
FAQ for the other classic traps.
