# Use case: your first filter rules

This tutorial configures a typical setup: a firewall protecting an internal
LAN with Internet access, and admin SSH restricted to a single address. MurOS
is an OPNsense fork, so rules attach to interfaces, not to zones.

## Topology

```
   [Internet]
       |
     WAN (eth0, 203.0.113.10/24)
       |
   +--- MurOS firewall ---+
       |
     LAN (eth1, 192.168.1.1/24)
       |
   [LAN hosts]
```

## Step 1: Interfaces

Under Interfaces > Assignments, map the devices, then configure each:

* WAN (eth0): static IPv4 `203.0.113.10/24`, gateway set, MTU 1500.
* LAN (eth1): static IPv4 `192.168.1.1/24`, MTU 1500.

Save and Apply.

## Step 2: Outbound NAT for Internet access

Under Firewall > NAT > Outbound, leave the mode on automatic. The LAN network
is then masqueraded behind the WAN address. Use manual mode only if you need
custom source NAT.

## Step 3: Let the LAN reach the Internet

Under Firewall > Rules, on the LAN tab, the default install ships a pass rule
from the LAN network to any destination. Keep it. This is the rule that lets
LAN hosts get out.

## Step 4: The WAN stays closed

The WAN tab has no pass rule toward the firewall or the LAN, so inbound
traffic from the Internet is blocked by default. There is nothing to add to
stay closed.

## Step 5: Restrict admin SSH to one address

First create an alias for the admin host. Under Firewall > Aliases, add a host
alias `admin_host` containing `203.0.113.99`.

Then, under Firewall > Rules on the WAN tab (or Floating if you prefer), add a
rule above the defaults:

* Action pass, protocol TCP, source `admin_host`, destination This Firewall,
  destination port 22.

Because the first matching rule wins and nothing else opens port 22 from the
WAN, only the admin host can reach SSH.

## Step 6: Let the LAN ping the firewall

Under Firewall > Rules on the LAN tab, add a pass rule, protocol ICMP, source
LAN net, destination This Firewall. Apply.

## Step 7: Keep the UI on the LAN only

The web UI listens on every interface; you decide who reaches it with rules.
Keep a pass rule on the LAN tab allowing the LAN to This Firewall on TCP 443
(present by default), and add no such rule on the WAN tab. The UI is then
reachable from the LAN and denied from the Internet.

Click Apply, then check the UI is still reachable. Every generated ruleset
keeps a mandatory anti-lockout rule for SSH and the web UI, so a too-strict
rule does not lock you out of management. If you ever do lose access, recover
from the console (see the Quickstart).

## Step 8: Back up before going to production

The whole configuration is one file. Under System > Configuration > Backups,
download a copy of config.xml so you can restore it on this node or another.

## Next steps

* Add an opt1 interface for a DMZ of exposed servers.
* Configure a WireGuard VPN for roaming users.
* Enable a DHCP server and the DNS resolver for the LAN.
* Pair a second node for high availability.
