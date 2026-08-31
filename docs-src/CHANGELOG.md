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
* Made aliases that are not lists of addresses (GeoIP, downloaded lists, host
  names, MAC addresses, autonomous system numbers, nested aliases) survive a
  ruleset reload: their resolved content is written into the generated ruleset,
  which pf got for free and nftables does not.
* Sent the replicated connection states to the peer the operator named,
  instead of always looking for it on a multicast group.
* Split the packet mark between the intrusion detection and policy based
  routing, which were overwriting each other and silently disabling either
  inspection or multi-gateway routing depending on the gateway number.
* Narrowed the captive portal redirection to what it is meant to intercept:
  encrypted connections addressed to the firewall, and plain web traffic that
  is not aimed at another client of the zone.
* Carried the rules the plugins register for themselves into the ruleset, so a
  DHCP server, an IPsec tunnel or a captive portal zone works without the
  operator writing their rules by hand.
* Narrowed the firewall reload to the table it owns, so the captive portal
  keeps its authenticated clients and their accounting across a reload.
* Implemented NAT reflection on nftables, as a redirection on the inside
  interfaces paired with a hairpin source translation on the return path.
* Completed the NAT translation: the address family, the protocol, the source
  and destination ports, the translation pool and its options, static port and
  logging are all carried into the ruleset, for outbound rules, port forwards
  and 1:1 mappings alike.
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
* Recursive DNS on the Debian Unbound daemon: DNSSEC, forwarders, local records
  and blocklists are generated from the UI for the stock package, without the
  FreeBSD chroot layout.
* Captive portal rebuilt on nftables: sessions, vouchers and per-session
  accounting, with the portal runtime and its background process under systemd.
* High availability on keepalived and conntrackd in place of CARP and pfsync:
  virtual IPs are rendered as VRRP instances with sync groups and service
  demotion, and the master pushes the selected configuration sections to the
  backup over XML-RPC.
* Traffic shaping on tc: pipes and queues become HTB classes with fq_codel or
  netem, the classification is carried by the nftables ruleset as marks, and the
  status page reads the live class counters.
* One-to-one NAT and IPv6 prefix translation are rendered from the model tree
  the GUI writes to: a mapping between whole prefixes becomes an nftables
  netmap, a single address a plain translation.
* The source NAT rules of the current GUI page are rendered next to the legacy
  outbound ones: an interface target becomes a masquerade, a fixed address or a
  prefix an explicit translation to that address or pool.
* Ported wireless to nl80211: the channel list, the transmit power table and
  the card capabilities come from `iw`, the status page shows the networks in
  range and the associated peers, and hostapd or wpa_supplicant drives the
  cell, protected or open. WEP has no equivalent and is refused.
* Fixed three features still calling a FreeBSD path: the OpenVPN client export
  produced an empty archive, the cipher lists of the secure shell page were
  empty, and the flow collector attributed flows to the wrong interface.
* The traffic shaper can shape what arrives on an interface, on an intermediate
  device fed by the ingress of the real one, classified by a filter of the
  traffic control layer.
* The traffic shaper builds the queueing discipline a pipe was configured with,
  scheduler, controlled delay targets, congestion notification and flow counts
  included, and names what the kernel cannot express, including shaping what
  arrives on an interface.
* A per source limit can add the offender to a table another rule blocks, for
  an hour, and the per source counters can be flushed from the interface.
* A rule asking for no connection tracking is excluded from the tracker ahead
  of it, and the options that have no counterpart here are named by the rule
  check instead of being dropped in silence.
* The quick option is honoured: a floating rule without it sets a verdict a
  later interface rule can override. The list is ordered so that the first
  match found by nftables is the one pf would have chosen.
* Rule schedules are honoured: weekday sets, calendar days and hour ranges. A
  rule outside its window is not loaded, and the filter is rebuilt on a timer
  so the ruleset follows the clock.
* A check tells whether a configured rule reached the kernel: it walks the
  configuration and looks for each item in the loaded ruleset and in the one
  the configuration produces, separating applied, pending a reload, and never
  applied. Available as `configctl filter verify` and in the health audit.
* Every rule carries the identifier of the item it came from, so the per rule
  counters work on the rules of the older pages too.
* The firmware changelog is built from the package: the history up to the
  running version ships with it, the repository publishes the changelog of
  every package alongside it, and apt fetches the one of a version not
  installed yet.
* The per source limits of a firewall rule are enforced: how many connections a
  single source may hold and how fast it may open them become a dynamic set
  keyed by the source address, guarding the rule they belong to.
* Intrusion detection and prevention on the Debian Suricata: detection through
  af-packet, inline blocking through NFQUEUE from the nftables ruleset, with
  rule downloads and alerts in the UI. Flow export runs on softflowd with local
  collection and aggregation.
* Host discovery without the FreeBSD hostwatch binary: a daemon listens for ARP
  and IPv6 neighbour discovery on a packet socket and reads the kernel neighbour
  table, feeding the host list, the captive portal and the MAC address aliases.
* Service monitoring on the Debian monit and power savings mapped to the cpufreq
  governors, both driven from the UI.
* The netstat diagnostics rebuilt on the Linux counters: per CPU softirq receive
  statistics, the packet sockets with the process holding them, and the socket
  memory charged against the kernel pressure limits.
* Per-rule policy routing with automatic multi-WAN failover: a rule pinned to a
  gateway or to a gateway group is marked by the nftables ruleset and steered
  into the routing table of that gateway. A group holds the members of the
  highest tier that still passes its trigger, as a weighted multipath route
  when the tier has several uplinks, and the table is rebuilt as soon as the
  monitor reports a state change. The connections that were already open move
  too: the tracked connections carrying the mark of the gateway that changed
  state are dropped, so their next packet is routed through what is current.
* The version, the commit and the hash of a build are derived at packaging time,
  so the firmware page reports what the box actually runs.

## In progress

* SNMP and notifications, the full apt upgrade flow and the sshd options from
  the UI.
* Long-run soak testing of the high availability state sync.
