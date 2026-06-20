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

## In progress

* Infrastructure services on their Debian daemons: DHCP (Kea), DNS (Unbound)
  and time (chrony).
* High availability (keepalived/conntrackd), traffic shaping, gateway
  monitoring and policy routing.
* The full apt upgrade flow and the sshd options from the UI.
