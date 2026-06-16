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
  systemd unit, with an anti-lockout baseline for SSH and the web UI.
* Started the system-layer port from FreeBSD to Debian across four axes: pf to
  nftables, rc and configd to systemd, pkg to apt, and ifconfig to iproute2.

## In progress

* NAT (outbound and port forward), address aliases as named nftables sets,
  schedules, and gateway and policy routing.
* Infrastructure services on their Debian daemons: DHCP (Kea), DNS (Unbound)
  and time (chrony).
* Wiring the remaining Apply actions through the systemd and nftables control
  plane.
