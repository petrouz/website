# FAQ and troubleshooting

## Is MurOS a fork of OPNsense?

Yes. MurOS is an open source fork of OPNsense, ported from FreeBSD to Debian
13. It keeps the OPNsense web UI, authentication and configuration model and
rebuilds the system layer for Linux: nftables instead of pf, systemd instead
of rc and configd, apt instead of pkg, and iproute2 instead of ifconfig. MurOS
is an independent project, not affiliated with or endorsed by Deciso B.V. or
the OPNsense project.

## What actually changes compared to OPNsense?

Everything behind the Apply button. The pages you click are the same, but the
filter is compiled to nftables, services run under systemd, updates come from
apt, and interfaces are configured with iproute2. The configuration still
lives in a single `/conf/config.xml`.

## I forgot the admin password

MurOS authenticates against its own user store inside `/conf/config.xml`, not
the Debian system accounts, so `passwd root` on the shell does not change the
UI login. Recover from the system console (serial, IPMI or hypervisor) by
setting a new bcrypt password on the `root` user entry in `/conf/config.xml`,
or by restoring a known-good configuration backup.

## The web UI is unreachable

The UI is served by lighttpd and php-fpm. From the console:

```bash
systemctl status lighttpd php8.4-fpm
journalctl -u lighttpd -n 100 --no-pager
```

Remember the UI is HTTPS only: a plain HTTP request will not keep the session.

## I lost SSH or HTTPS access after a firewall change

MurOS always includes an anti-lockout baseline (SSH and the UI from the
management network) in the generated ruleset, and a firewall apply opens a
rollback timer. If you did not confirm in time, the previous ruleset is
restored automatically. If you are still locked out, reload from the console:

```bash
nft flush ruleset
systemctl restart muros-firewall
```

If you changed the admin interface IP or the default gateway and lost access,
you need console or hypervisor access to revert that change.

## The firewall does not forward LAN to WAN traffic

Check in order:

1. IP forwarding: `sysctl net.ipv4.ip_forward` must return `1`.
2. Outbound NAT: Firewall > NAT > Outbound on automatic, or a manual
   masquerade rule for the LAN network egressing the WAN.
3. A pass rule on the LAN tab from the LAN network to any.
4. No pending Apply: an orange banner means changes are not pushed yet.

From a LAN host, run `traceroute 1.1.1.1` to see where it stops.

## How do I update MurOS?

Through apt, like any Debian package:

```bash
apt update && apt install --only-upgrade muros
```

While MurOS is in beta, breaking changes are still possible between release
candidates; export a configuration backup before upgrading.

## Can I import an existing OPNsense config.xml?

The configuration model is the same, so much of it carries over, but device
names do not: OPNsense names interfaces the FreeBSD way (em0, igb0, vtnet0)
while MurOS uses Linux names (eth0, ens3, enp1s0). Review interface
assignments and any setting that references a raw device after importing, and
test before relying on it.

## How do I reset to a clean ruleset?

From the console:

```bash
nft flush ruleset
systemctl restart muros-firewall
```

This reloads the ruleset generated from the current configuration, including
the anti-lockout baseline.
