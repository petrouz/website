# Architecture

MurOS is a fork of OPNsense, ported from FreeBSD to Debian 13. The web UI, the
authentication stack and the configuration model are the proven OPNsense
codebase. The system layer underneath has been rebuilt for Linux. This page
maps the moving parts and how an action in the UI reaches the kernel.

## What is kept, what is rebuilt

| Layer | OPNsense (FreeBSD) | MurOS (Debian) |
| --- | --- | --- |
| Packet filter | pf / pfctl | nftables |
| Service supervision | rc.d + configd | systemd + configd bridge |
| Packages and updates | pkg / opnsense-update | apt |
| Interface configuration | ifconfig | iproute2 (ip) |
| Web UI and config model | PHP and Phalcon MVC, config.xml | unchanged |

The web UI, the data model and the operator workflow are therefore the same as
OPNsense. What changes is everything behind the Apply button.

## Configuration model

There is no database. The whole state of the firewall lives in a single XML
file, `/conf/config.xml`, read and written through the OPNsense configuration
classes. Rules, interfaces, users, VPN peers, services: all of it is one
versioned document. That is what makes a configuration portable between nodes
and simple to back up.

## Web stack

The GUI is served on Debian by lighttpd and php-fpm, with the Phalcon PHP
extension that the OPNsense MVC layer requires. Two GUI layers coexist, as
upstream: the classic PHP pages (login, dashboard) and the Phalcon MVC layer
that serves /ui and the API. HTTPS is mandatory and the session cookie is
secure-only, so the UI cannot be used over plain HTTP.

## System layer

| systemd unit | Role |
| --- | --- |
| muros-firewall.service | renders config.xml into an nftables ruleset (table inet muros, chains input / forward / output) and loads it at boot and on reload |
| muros-interface-assign.service | maps the logical interfaces (wan, lan, optN) to the real Linux devices at boot, then reloads the firewall |
| muros-interfaces.service | applies the assigned interfaces from config.xml via iproute2 (link, MTU, static v4/v6 addresses) |
| muros-configd.service | control-plane bridge: the UI asks it to apply a change, it runs the matching Linux action |
| lighttpd, php-fpm | serve the web UI over HTTPS |

The generated ruleset always carries an anti-lockout baseline (SSH and the web
UI from the management network), so an applied ruleset cannot strand the
operator.

## Apply pipeline

1. The UI validates the change and writes it to `/conf/config.xml`.
2. The configd bridge renders the affected configuration. For filtering, the
   ruleset is generated and loaded with `nft -f`, an atomic kernel swap.
3. The matching systemd unit is reloaded or restarted.
4. For a firewall apply the ruleset is first validated with `nft -c`; an
   invalid ruleset is rejected and the running one is left untouched. Every
   loaded ruleset carries a mandatory anti-lockout rule, so an apply cannot
   strand the operator.

## Porting status

MurOS is in beta. Running on Debian today: the web UI, login, the
configuration model, the stateful filter and NAT (config.xml to nftables),
address aliases as named nftables sets, the full interface layer via iproute2
(addressing, VLANs, bridges, LAGG as Linux bonding, GRE/GIF tunnels), static
routing, account management through the Debian shadow utilities, the package
inventory through dpkg/apt, and the WireGuard and OpenVPN runtime devices.
Also running: the infrastructure services (Kea DHCP, Unbound, chrony), high
availability on keepalived and conntrackd with configuration synchronisation to
the backup, traffic shaping on tc, intrusion detection and prevention on
Suricata, flow export on softflowd, the captive portal on nftables, host
discovery, gateway monitoring with dpinger, and per-rule policy routing with
automatic multi-WAN failover between the tiers of a gateway group. Still being
ported: SNMP and notifications, the full apt upgrade flow, and the sshd options. Each feature
page notes where it stands.
