# Changelog

MurOS is an open source fork of OPNsense, ported from FreeBSD to Debian 13.
The project is in beta: the version line is `v0.9.x`, and breaking changes are
still possible between release candidates.

Detailed, per-release notes are published with each build on the GitHub
Releases page. This page summarises the broad strokes.

## Beta (v0.9.x)

* Forked the OPNsense core and brought the web UI, login, dashboard and the
  single-file configuration model (`/conf/config.xml`) up on Debian 13, served
  by lighttpd and php-fpm with the Phalcon PHP extension.
* Replaced the FreeBSD packet filter: the configuration is compiled to an
  nftables ruleset (table inet muros) and loaded at boot and on reload by a
  systemd unit, with an anti-lockout baseline for SSH and the web UI, after a
  `nft -c` validation.
* Ported NAT (outbound masquerade and port forward) and address aliases to
  named nftables sets, with live per-rule and per-table counters from
  netfilter and connection-state flush through conntrack.
* Rebuilt the interface layer on iproute2: addressing, VLANs, bridges, LAGG as
  Linux bonding, GRE and GIF tunnels, and static routing, with automatic
  interface assignment and persistent bring-up at boot through systemd units.
* Ported account management to the Debian shadow utilities, PAM-based login
  shared between the web UI and SSH, and the package inventory to dpkg/apt.
* Brought up the WireGuard and OpenVPN runtime devices through iproute2.
* DHCP client on WAN through an iproute2 lease hook (address, routes including
  the classless and static options), kept across renew, rebind and reboot.
* Diagnostics on Linux tooling: connection states and flush through conntrack,
  packet capture with tcpdump, ARP/NDP and routes from iproute2, open sockets
  from ss, and the loaded ruleset.
* The firewall log streamed live to the UI from the system journal (journald),
  with the matching rule resolved per entry, plus health graphs (CPU, memory,
  temperature) and the dashboard read from /proc.
* System tunables applied live through sysctl on top of a curated set of
  network hardening defaults, and a serial console managed through systemd.
* Per-gateway monitoring (latency, packet loss and availability) with the
  dpinger daemon, packaged for Debian and pulled from the MurOS apt repository.
* DHCP server on the Debian Kea daemons (DHCPv4 and DHCPv6): configuration is
  generated to /etc/kea, the daemons run as stock systemd units driven by a
  service wrapper, and active leases are read over the Kea control channel.
* Network Time (NTP) on chrony instead of the ntp.org daemon: the configuration
  is generated to /etc/chrony/chrony.conf from the UI, the daemon runs as the
  stock chrony systemd unit, and the status page reads sources, offsets, jitter
  and delay live from chrony.

## In progress

* Recursive validating DNS on the Debian Unbound daemon.
* Full VPN service lifecycle (WireGuard, OpenVPN, IPsec) through systemd.
* High availability (keepalived/conntrackd) and traffic shaping.
* Automatic multi-WAN failover and policy routing.
* SNMP and notifications, the full apt upgrade flow and the sshd options from
  the UI.
