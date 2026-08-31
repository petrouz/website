# MurOS services

Besides filtering, NAT and VPN, MurOS runs the infrastructure services a
firewall is usually expected to provide. Each has its own page in the UI and
is only written to the system when you Apply. On Debian these map to the
standard Linux daemons.

During beta, the service pages, the configuration model and the backends that
drive the Linux daemons are wired on Debian. SNMP and notifications are the
last ones still being ported; the changelog page tracks what is left.

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
This keeps interactive traffic responsive when the link is saturated. On Debian
a pipe becomes an HTB class whose leaf discipline follows what the pipe was
configured with: fq_codel with its limit, flows and quantum, the controlled
delay targets and congestion notification, a plain codel queue, fq_pie, or a
delay queue for a pipe that adds latency. The match rules are carried by the
nftables ruleset as marks and the status page reads the live class counters.
Managed under Firewall > Shaper.

Shaping what arrives on an interface works too, which a queueing discipline
cannot do on its own: the ingress of the interface is redirected onto an
intermediate device whose egress carries the same tree. That direction is
classified by a filter of the traffic control layer rather than by the
ruleset, because the redirection happens before the packet filter is
consulted, and such a filter only understands a protocol, an address or a
prefix and ports.

What this kernel cannot express is named rather than ignored: the schedulers
with no counterpart, the dynamic pipe per source or destination, the hash
bucket count, and the inbound rules whose match is beyond a traffic control
filter, an alias, a negation or a packet length. Ask for the list with
`configctl shaper notes`, or read it in the health audit of the firmware page.

## Wireless

A wifi card can serve an access point or join an existing network. The
interface form offers the channels the regulatory domain of the radio allows,
with the high throughput modes the card advertises, all read from `iw`. An
access point is served by hostapd, a station is joined by wpa_supplicant, with
or without encryption, and the hidden network, quality of service and station
isolation toggles are passed to hostapd. WEP has no equivalent on this
platform and is refused. Status > Wireless lists the networks in range and the
associated peers with their signal, negotiated rates and traffic counters.
Unlike FreeBSD, a card is assigned directly, there is no clone device.

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
