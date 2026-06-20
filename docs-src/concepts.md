# MurOS concepts

These are the core concepts you meet in the MurOS web UI. MurOS is an OPNsense
fork, so the model is OPNsense's, running on a Debian system.

## Configuration and Apply

Everything is stored in one file, `/conf/config.xml`. You edit settings in the
UI and save them; saved changes are staged, not necessarily live yet. Pages
that change the running system show an Apply action that pushes the staged
configuration to the kernel and the services. On a firewall apply the
generated nftables ruleset is validated with `nft -c` before it is loaded, and
every ruleset carries a mandatory anti-lockout rule (SSH and the web UI from
the management network) so an apply cannot strand the operator.

## Interfaces

An interface is a logical handle (wan, lan, opt1, opt2, and so on) mapped to a
network device on the box: for example eth0, eth1, a VLAN such as eth0.10, or a
VPN device. Each interface carries an IPv4 and/or IPv6 address, an optional
gateway and an optional MTU.

A firewall LAN is static; only the WAN should use DHCP. Interfaces are mapped
under Interfaces > Assignments and configured on their own page.

## Firewall rules

MurOS filters per interface, not by zone. Each interface (WAN, LAN, ...) has
its own rules tab under Firewall > Rules, plus a Floating tab for rules that
span interfaces. Rules are evaluated on the interface where a packet enters,
top to bottom, first match wins.

A rule action is one of:

* pass: let the packet through
* block: silently drop it
* reject: drop it and tell the sender (TCP reset or ICMP unreachable)

Out of the box, the LAN allows outbound traffic and the WAN blocks everything
inbound, so the box is closed from the Internet and open from the inside.

## Aliases

An alias is a named group of addresses, networks, ports or hosts that you
reference in rules instead of repeating literals. Edit one alias, every rule
that uses it follows. On Debian these map to named nftables sets. Manage them
under Firewall > Aliases.

## NAT

* Outbound NAT (source NAT or masquerade): lets LAN hosts reach the Internet
  behind the firewall address. Modes are automatic, hybrid or manual.
* Port forward (destination NAT): publishes an internal service on a WAN port.

Both live under Firewall > NAT.

## VPN

* WireGuard: modern, fast and simple. Best for roaming devices and simple
  site-to-site links.
* IPsec: standards-based, interoperable with third-party gear, PSK or X.509.
* OpenVPN: TLS VPN with the widest client support, a road-warrior server with
  downloadable client profiles.

Manage them under VPN.

## High availability

An active/passive pair. On Debian, keepalived owns the virtual IPs over VRRP
(replacing FreeBSD CARP), conntrackd replicates connection state (replacing
pfsync), and config.xml is synchronised to the backup so it always holds the
full configuration. See the High availability page.

## Logging and backups

Filter and system logs are visible in the UI and on the box through
journalctl. Because the whole configuration is a single file, a backup is just
an export of config.xml that you can restore on the same node or a different
one.
