# High availability

MurOS HA is a classic active/passive pair. OPNsense uses CARP and pfsync on
FreeBSD; the MurOS port rebuilds the same model on Linux with keepalived (VRRP
for the virtual IPs) and conntrackd (connection-state replication). On top of
that, the configuration in config.xml is synchronised to the backup so it
always holds the full configuration of the master.

> Beta status: the high-availability backend is wired on Debian. Applying the
> configuration renders the keepalived and conntrackd configuration, the
> virtual IPs come up as VRRP instances and the master synchronises its
> configuration to the backup. Long-run soak testing of the state
> synchronisation is still in progress.

## Topology

```
            VIP 203.0.113.1                   VIP 10.10.0.1
                |                                  |
         (WAN) eth0 -------- internet -------- eth0 (WAN)
                                                   |
  master ---- eth1 (LAN) ---- switch ---- eth1 (LAN) ---- backup
                |              VRRP +              |
                |              conntrack           |
                |              sync                |
         (sync) eth2 ------ direct cable ------ eth2 (sync)
```

The sync link can be a dedicated NIC or a VLAN on the LAN switch. A direct
cable keeps VRRP advertisements out of the broadcast domain and survives a LAN
switch reboot.

## What you configure

Under System > High Availability:

* Role: master or backup. The VRRP priority follows the role.
* Authentication: the VRRP shared secret.
* Sync interface: the link conntrackd uses for state replication.
* Peer address: used to synchronise the configuration to the backup.
* Virtual IPs: one per interface that should fail over, each with its own
  VRID.

Applying this page regenerates the keepalived and conntrackd configuration and
restarts both services, and pushes the configuration to the backup.

## What survives a failover

* TCP and UDP connections tracked in conntrack (web sessions, SSH from the LAN
  to a DMZ host, replicated IPsec security associations).
* The active WireGuard interface: peers reconnect within their persistent
  keepalive interval.
* DHCP leases, as part of the synchronised configuration state.

## What does not survive a failover

* Live diagnostic streams (packet capture, traceroute) in the UI. Restart them
  after takeover.
* Your current SSH session to the master IP: reconnect to the virtual IP to
  land on the new master.

## Asymmetric pairs

Identical hardware is recommended but not required. As long as the interface
assignments match on both sides, keepalived owns the virtual IPs and
conntrackd replays sessions. A smaller backup must still have enough CPU and
RAM to terminate the same encrypted tunnels at the real traffic rate, or it
becomes the bottleneck during a takeover.

## Verifying the pair

From either node:

```bash
ip -br addr
journalctl -u keepalived -n 50 --no-pager
conntrackd -s
```

## Common pitfalls

* VRID collision with another VRRP cluster on the same L2. Change the VRIDs if
  you already run keepalived elsewhere.
* Editing the generated ruleset by hand on the backup. The configuration sync
  keeps both nodes identical; hand edits will surprise you on the next
  failover. Drive everything from the UI.
* Upstream anti-spoofing that drops packets sourced from the virtual IP when
  they arrive from the backup right after a takeover. Use sticky source NAT
  upstream if you observe it.
