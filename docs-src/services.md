# MurOS services

Besides filtering, NAT and VPN, MurOS runs the infrastructure services a
firewall is usually expected to provide. Each has its own page in the UI and
is only written to the system when you Apply. On Debian these map to the
standard Linux daemons.

During beta, the service pages and the configuration model are in place; the
backends that drive the Linux daemons are being ported from the FreeBSD
originals. Treat this page as the target behaviour.

## DHCP server (IPv4 and IPv6)

Hands out addresses to LAN hosts using Kea. Per interface you define a pool
(range), the lease time and the options pushed to clients (gateway, DNS,
domain). Static mappings bind a fixed address to a MAC so a host always gets
the same IP. Managed under Services > Kea DHCP.

## DNS resolver

A recursive resolver for the LAN, backed by Unbound. It resolves names for
internal clients and can serve local host overrides (name to IP). This is the
resolver MurOS offers to the LAN; the firewall keeps its own upstream resolver
for apt, curl and time sync unless you point it at the local Unbound. Managed
under Services > Unbound DNS.

## Network time

Time synchronisation through chrony. The firewall keeps its clock in sync with
upstream sources and can serve time to the LAN. A correct clock matters for
logs, certificates and VPN. Managed under Services > Network Time.

## Dynamic DNS

Keeps one or more hostnames pointed at the firewall's current public IP.
Useful when the WAN address is dynamic and you need a stable name to reach a
VPN endpoint or a published service. Managed under Services > Dynamic DNS.

## Traffic shaping

Egress bandwidth control per interface, using the kernel's queueing
disciplines. You cap an interface's egress rate, split it into classes with
guaranteed and ceiling rates, and assign traffic to a class with match rules.
This keeps interactive traffic responsive when the link is saturated. Managed
under Firewall > Shaper.

## Remote logging

Forwards the firewall's logs to a central syslog server or SIEM over UDP or
TCP. Use it to keep logs off the box and centralise them with the rest of your
fleet. Managed under System > Settings > Logging.

## SNMP

Exposes read-only metrics for monitoring tools, SNMP v2c (community string)
and v3 (with authentication and privacy). Managed under Services > SNMP.

## Notifications

Sends email alerts on important events. Configure the SMTP relay and the
recipients so the firewall can warn you when something needs attention.
Managed under System > Settings > Notifications.
