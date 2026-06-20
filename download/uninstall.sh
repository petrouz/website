#!/bin/bash
# MurOS uninstaller - safe defaults.
#
# Default flow :
#   1. Stop + disable MurOS services and optional services (keepalived,
#      strongswan, wireguard, snmpd) only used via the MurOS UI
#   2. Snapshot /var/lib/muros to /var/backups/muros/data-<timestamp>
#      so the DB and backups can be restored by the next install.sh
#      (unless MUROS_PURGE_DATA=1)
#   3. apt-get purge muros (postrm wipes /opt/muros, DB, configs)
#   4. Cleanup config drop-ins written by MurOS outside the package
#   5. Restore /etc/network/interfaces from the .muros-bak backup
#   6. Unmask native network services (networking, systemd-networkd, NM)
#
# Dependency packages (keepalived, strongswan, wireguard, nginx,
# fail2ban, snmpd...) stay installed but inactive. Purge them with
# MUROS_PURGE_DEPS=1, which is opt-in (may pull shared libs used
# elsewhere).
#
# Everything is logged to /var/log/muros-install.log.
#
# Usage (official, single method) :
#   curl -fsSL https://download.muros.org/uninstall.sh | sudo bash
#
# Optional vars :
#   MUROS_PURGE_DEPS=1   also purge keepalived/strongswan/wireguard/etc.
#                        (default : off, safer)
#   MUROS_PURGE_DATA=1   wipe /var/lib/muros AND /var/backups/muros
#                        so the next install starts from a clean slate
#                        (default : off, data is preserved for reinstall)

set -eu

LOG=/var/log/muros-install.log
PURGE_DEPS="${MUROS_PURGE_DEPS:-0}"

if [ "$(id -u)" -ne 0 ]; then
  echo "Must be run as root" >&2
  exit 1
fi

exec > >(tee -a "$LOG") 2>&1
echo
echo "=============================================================="
echo "MurOS uninstall - $(date -Is)"
echo "=============================================================="

echo "[1/4] Stopping MurOS services and optional services"
# Services MurOS
for s in muros-backend muros-watcher muros-boot; do
  systemctl stop "$s.service" 2>/dev/null || true
  systemctl disable "$s.service" 2>/dev/null || true
done
# Optional services that only make sense with MurOS (managed via the UI).
# We stop and disable them, but leave the package in place. The
# reset-failed avoids leaving a unit in a red "failed" state afterwards.
for s in keepalived conntrackd strongswan strongswan-starter \
         snmpd kea-dhcp4-server unbound muros-watcher; do
  systemctl stop "$s.service" 2>/dev/null || true
  systemctl disable "$s.service" 2>/dev/null || true
  systemctl reset-failed "$s.service" 2>/dev/null || true
done
systemctl stop "wg-quick@wg0.service" 2>/dev/null || true
systemctl disable "wg-quick@wg0.service" 2>/dev/null || true
systemctl reset-failed "wg-quick@wg0.service" 2>/dev/null || true

echo "[2/4] Purge du paquet muros (dpkg postrm s'occupe de /opt, /etc, DB)"
export DEBIAN_FRONTEND=noninteractive
# Optional snapshot of /var/lib/muros before any purge action. Lets us
# restore the DB if the user reinstalls and wants the previous config
# back. Off if MUROS_PURGE_DATA=1 (user explicitly asks for wipe).
if [ "${MUROS_PURGE_DATA:-0}" != "1" ] && [ -d /var/lib/muros ]; then
  BACKUP_DIR="/var/backups/muros"
  STAMP=$(date -u +%Y%m%dT%H%M%SZ)
  mkdir -p "$BACKUP_DIR"
  if cp -a /var/lib/muros "$BACKUP_DIR/data-$STAMP" 2>/dev/null; then
    echo "    Data snapshot kept at $BACKUP_DIR/data-$STAMP"
    echo "    (it will be auto-restored by install.sh on the next reinstall)"
  fi
fi

if dpkg -l muros >/dev/null 2>&1; then
  # Degraded case: if an upgrade was killed mid-way, dpkg keeps muros in
  # "reinstall required" state and apt refuses to move forward until we
  # reinstall it, but the archive is gone. Try apt-get purge first, then
  # dpkg --purge, then dpkg --remove --force-remove-reinstreq which
  # nukes a "ReinstReq" package without requiring the archive.
  if ! apt-get purge -y muros 2>/dev/null; then
    if ! dpkg --purge muros 2>/dev/null; then
      echo "    package in inconsistent state, force-remove..."
      dpkg --remove --force-remove-reinstreq muros 2>/dev/null || true
      dpkg --purge --force-all muros 2>/dev/null || true
    fi
  fi
else
  echo "    muros package not installed"
fi

# If user explicitly asked to wipe, also remove our stashed snapshots
# (otherwise the next install would restore them).
if [ "${MUROS_PURGE_DATA:-0}" = "1" ]; then
  rm -rf /var/backups/muros 2>/dev/null || true
fi

# Clean up the dpkg/apt entries that might survive (ghost package in
# /var/lib/dpkg/info/muros.* after force-remove)
rm -f /var/lib/dpkg/info/muros.* 2>/dev/null || true
# Force apt to re-evaluate the state
dpkg --configure -a 2>/dev/null || true

if [ "$PURGE_DEPS" = "1" ]; then
  echo "[3/4] MUROS_PURGE_DEPS=1: purging optional dependencies"
  # Strictly MurOS-specific list. No purge of nginx, ssl-cert, rsync,
  # nftables, iproute2 or the build packages: too much risk of side
  # effects on the rest of the system.
  DEPS="
    keepalived conntrackd
    strongswan strongswan-starter strongswan-swanctl
    libcharon-extra-plugins libstrongswan-extra-plugins
    wireguard-tools wireguard
    fail2ban snmpd snmp
    kea-dhcp4-server kea-common chrony unbound
  "
  for p in $DEPS; do
    if dpkg -l "$p" >/dev/null 2>&1; then
      echo "    -> purge $p"
      apt-get purge -y "$p" 2>/dev/null || true
    fi
  done
else
  echo "[3/4] Dependencies kept (use MUROS_PURGE_DEPS=1 to remove them)"
fi

echo "[4/4] Cleaning up the drop-ins written by MurOS outside the package"

# MurOS application directories (the DB, the backups, the caches)
rm -rf /opt/muros /var/lib/muros /etc/muros /var/cache/muros

# Signed apt repository registered by install.sh (download.muros.org)
rm -f /etc/apt/sources.list.d/muros.list
rm -f /usr/share/keyrings/muros-archive-keyring.gpg

# IPsec: swanctl drop-ins written by MurOS (the strongswan package
# configs stay intact)
rm -f /etc/swanctl/conf.d/muros.conf /etc/swanctl/conf.d/muros.secrets

# WireGuard: configs written by MurOS
rm -f /etc/wireguard/wg*.conf

# HA / SNMP: MurOS overwrites /etc/keepalived/keepalived.conf,
# /etc/conntrackd/conntrackd.conf and /etc/snmp/snmpd.conf with its
# own config. We remove them here. If the admin wants to reuse
# keepalived/snmpd standalone after uninstall, they must reinstall the
# package (apt-get install --reinstall keepalived) to get the original
# config back.
rm -f /etc/keepalived/keepalived.conf 2>/dev/null || true
rm -f /etc/conntrackd/conntrackd.conf 2>/dev/null || true

# SNMP: MurOS drop-in only (leaves the package's /etc/snmp/snmpd.conf)
rm -f /etc/snmp/snmpd.conf.d/muros.conf

# V1.2 network services: configs written by MurOS. Kea serves DHCP,
# unbound the recursive resolver. We remove the MurOS config from Kea, its
# leases, and the unbound drop-in. The package configs stay intact.
rm -f /etc/kea/kea-dhcp4.conf
rm -f /var/lib/kea/kea-leases4.csv 2>/dev/null || true
rm -f /etc/unbound/unbound.conf.d/muros.conf

# NTP: chrony drop-in written by MurOS. We remove it and re-enable
# systemd-timesyncd (masked at install) so the box keeps the time.
rm -f /etc/chrony/conf.d/muros.conf
systemctl unmask systemd-timesyncd.service 2>/dev/null || true

# DNS: MurOS writes /etc/resolv.conf directly and keeps a .muros-bak
# backup (saved by postinst on the 1st install). Two possible backups,
# we try them from the most specific to the most general:
#  - .muros-pre-unbound: laid down when the admin enabled "Unbound as
#    the system resolver" (resolv.conf = nameserver 127.0.0.1). This is
#    THE case that breaks apt after uninstall: Unbound is stopped/removed
#    but resolv.conf still points at the dead 127.0.0.1, so every DNS
#    query waits for a timeout before falling back, and `apt update`
#    crawls / hangs at 0%.
#  - .muros-bak: backup of the old pre-MurOS resolv.conf.
if [ -f /etc/resolv.conf.muros-pre-unbound ]; then
  mv /etc/resolv.conf.muros-pre-unbound /etc/resolv.conf
  rm -f /etc/resolv.conf.muros-bak 2>/dev/null || true
elif [ -f /etc/resolv.conf.muros-bak ]; then
  mv /etc/resolv.conf.muros-bak /etc/resolv.conf
fi
# Safety net: if resolv.conf still points ONLY at the local resolver
# 127.0.0.1 (Unbound, now stopped), apt and everything else have no DNS
# anymore. We replace it with public resolvers so the box stays usable
# right after the uninstall.
if [ -f /etc/resolv.conf ]; then
  RC_LOCAL=$(grep -E '^[[:space:]]*nameserver[[:space:]]+127\.' /etc/resolv.conf 2>/dev/null | wc -l)
  RC_PUBLIC=$(grep -E '^[[:space:]]*nameserver[[:space:]]+' /etc/resolv.conf 2>/dev/null \
              | grep -Ecv 'nameserver[[:space:]]+127\.')
  if [ "$RC_LOCAL" -gt 0 ] && [ "$RC_PUBLIC" -eq 0 ]; then
    printf 'nameserver 1.1.1.1\nnameserver 8.8.8.8\n' > /etc/resolv.conf
  fi
fi
# resolved drop-in if we laid one down (advanced case where the admin had
# installed systemd-resolved by hand)
rm -f /etc/systemd/resolved.conf.d/muros.conf 2>/dev/null || true

# Network: iface drop-in + backup of the original interfaces
rm -f /etc/network/interfaces.d/muros
# /etc/network/interfaces.muros-bak is restored by the postrm purge,
# but if this script runs without an apt purge having happened before
# (rare case), we restore it here as a last resort.
if [ -f /etc/network/interfaces.muros-bak ] && \
   [ ! -f /etc/network/interfaces.restored.muros ]; then
  mv /etc/network/interfaces.muros-bak /etc/network/interfaces
  touch /etc/network/interfaces.restored.muros
  rm -f /etc/network/interfaces.restored.muros
fi

# nginx : site + bak + symlinks SSL
rm -f /etc/nginx/sites-enabled/muros
rm -f /etc/nginx/sites-available/muros.muros-bak
rm -f /etc/nginx/ssl/muros.crt /etc/nginx/ssl/muros.key
rmdir /etc/nginx/ssl 2>/dev/null || true

# fail2ban / nftables
rm -f /etc/fail2ban/jail.d/muros.conf
rm -f /etc/nftables.conf.muros-bak 2>/dev/null || true

# Flush the live nftables ruleset. nftables is stateful in the kernel:
# removing the muros package does NOT clear the rules that muros-boot
# loaded, so without this the box stays firewalled by a ruleset nobody
# manages anymore (and can drop traffic in confusing ways). Uninstalling
# the firewall must leave an open box.
if command -v nft >/dev/null 2>&1; then
  nft flush ruleset 2>/dev/null || true
fi

# Kernel hardening drop-in shipped by MurOS (rp_filter strict, IP
# forwarding, no ICMP redirects, ...). It is NOT a package conffile, so
# apt purge leaves it behind and the box stays in a firewall-tuned state
# after removal. Drop it and reload sysctl so the kernel reverts to the
# Debian defaults (no forwarding, loose rp_filter, etc.).
rm -f /etc/sysctl.d/99-muros-hardening.conf
rm -f /etc/sysctl.d/99-muros.conf 2>/dev/null || true
if command -v sysctl >/dev/null 2>&1; then
  sysctl --system >/dev/null 2>&1 || true
fi

# SSH drop-in: shipped by the .deb so removed by apt purge muros.
# In case MurOS rewrote it after purge (race with the UI apply):
rm -f /etc/ssh/sshd_config.d/muros.conf
# The /var/log/muros-install.log log is kept on purpose so the uninstall
# sequence can be reviewed afterwards.
# muros user (if created)
if getent passwd muros >/dev/null 2>&1; then
  deluser --quiet --remove-home muros 2>/dev/null || true
fi

if dpkg -l nginx-common >/dev/null 2>&1; then
  if [ -f /etc/nginx/sites-available/default ] && [ ! -L /etc/nginx/sites-enabled/default ]; then
    ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default
  fi
  systemctl reload nginx 2>/dev/null || systemctl restart nginx 2>/dev/null || true
fi
systemctl daemon-reload || true

# Restore Debian-default network manager so the box still has working
# network management after MurOS is gone. ifupdown is the historical
# Debian default and works with the /etc/network/interfaces backup we
# restored above. We don't reinstall NetworkManager (desktop-only by
# default on Debian server installs).
if ! dpkg-query -W -f='${Status}' ifupdown 2>/dev/null | grep -q "install ok installed"; then
  echo "    -> reinstalling ifupdown (Debian default network manager)"
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends ifupdown isc-dhcp-client 2>/dev/null || \
    echo "       (failed, install ifupdown manually if you need it)"
fi
# Unmask systemd-networkd (the only unit MurOS masked - the others
# were uninstalled outright). Stays disabled until admin enables it.
for svc in systemd-networkd.service systemd-networkd-wait-online.service; do
  systemctl unmask "$svc" 2>/dev/null || true
done

echo
echo "=============================================================="
echo "MurOS purge OK. Log : ${LOG}"
echo "=============================================================="
echo "Reinstall :"
echo "  curl -fsSL https://download.muros.org/install.sh | sudo bash"
