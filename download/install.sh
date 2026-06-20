#!/bin/bash
# MurOS installer - registers the signed apt repository (download.muros.org)
# and installs the muros package on a fresh Debian 13 (trixie). Logs
# everything to /var/log/muros-install.log for later debugging.
#
# Usage:
#   curl -fsSL https://download.muros.org/install.sh | sudo bash
#
# Optional variable:
#   MUROS_VERSION=0.9.8   install a specific version (it must still be
#                         available in the repo; the repo keeps only the
#                         latest version).

set -eu

LOG=/var/log/muros-install.log
APT_KEYRING=/usr/share/keyrings/muros-archive-keyring.gpg
APT_LIST=/etc/apt/sources.list.d/muros.list

if [ "$(id -u)" -ne 0 ]; then
  echo "This script must run as root (sudo bash install.sh)" >&2
  exit 1
fi

# Redirect stdout+stderr to the log file while keeping the live output
# on screen.
exec > >(tee -a "$LOG") 2>&1
echo
echo "=============================================================="
echo "MurOS install - $(date -Is)"
echo "=============================================================="

echo "[1/3] Prerequisites"

# DNS preflight. If /etc/resolv.conf only points at a loopback resolver
# (the systemd-resolved stub 127.0.0.53 is the Debian default, and a box
# whose local resolver was removed ends up the same way), lookups can
# stall and apt hangs at 0%. Fall back to public resolvers so this
# installer and apt can reach the repository.
if [ -f /etc/resolv.conf ]; then
  RC_LOCAL=$(grep -E '^[[:space:]]*nameserver[[:space:]]+127\.' /etc/resolv.conf 2>/dev/null | wc -l)
  RC_PUBLIC=$(grep -E '^[[:space:]]*nameserver[[:space:]]+' /etc/resolv.conf 2>/dev/null \
              | grep -Ecv 'nameserver[[:space:]]+127\.' || true)
  if [ "$RC_LOCAL" -gt 0 ] && [ "$RC_PUBLIC" -eq 0 ]; then
    echo "    -> /etc/resolv.conf only points at a local resolver; using public DNS for install"
    printf 'nameserver 1.1.1.1\nnameserver 8.8.8.8\n' > /etc/resolv.conf
  fi
fi

# Detect a broken dpkg state inherited from a failed upgrade: if muros is
# marked "ReinstReq" / "half-configured" / "half-installed", apt-get
# refuses to proceed until it is reinstalled. Clean up first so the rest
# can proceed.
MUROS_STATUS=$(dpkg-query -W -f='${Status}' muros 2>/dev/null || true)
case "${MUROS_STATUS}" in
  *reinstreq*|*half-configured*|*half-installed*|*unpacked*|*triggers-pending*|*failed-config*)
    echo "    -> muros package in inconsistent state (${MUROS_STATUS}), force-remove before install..."
    dpkg --remove --force-remove-reinstreq muros 2>/dev/null || true
    dpkg --purge --force-all muros 2>/dev/null || true
    rm -f /var/lib/dpkg/info/muros.* 2>/dev/null || true
    dpkg --configure -a 2>/dev/null || true
    ;;
esac

# Neutralize any "deb cdrom:" apt source. A Debian install can leave a
# CD-ROM entry in the sources; on a running system the disc is not
# mounted, so apt-get update fails with exit code 100. Comment those
# lines out before touching apt.
for src in /etc/apt/sources.list /etc/apt/sources.list.d/*.list; do
  [ -f "$src" ] || continue
  if grep -qE '^[[:space:]]*deb[[:space:]]+cdrom:' "$src"; then
    echo "    -> disabling CD-ROM apt source in $src"
    sed -i -E 's/^([[:space:]]*deb[[:space:]]+cdrom:)/# \1/' "$src"
  fi
done

apt-get update -qq
apt-get install -y -qq curl ca-certificates gnupg

# Register the signed apt repository (download.muros.org). The whole
# install, and every later upgrade through apt, flows from here. A leading
# "v" in MUROS_VERSION is tolerated (tags are vX, the apt version is X).
echo "[2/3] Registering download.muros.org"
install -d -m 0755 /usr/share/keyrings
if ! curl -fsSL https://download.muros.org/muros.asc | gpg --dearmor --batch --yes -o "${APT_KEYRING}"; then
  echo "Cannot fetch the repository signing key from https://download.muros.org" >&2
  echo "Check DNS / network and retry." >&2
  exit 1
fi
echo "deb [signed-by=${APT_KEYRING}] https://download.muros.org stable main" > "${APT_LIST}"
apt-get update -qq
echo "    -> download.muros.org registered"

echo "[3/3] Installing MurOS"
# Block auto-start of config-required feature daemons during apt install.
# The muros package pulls some feature daemons (unbound as a Recommends,
# others as Suggests). Daemons that need a per-site configuration must
# stay dormant until the admin enables the matching feature from the UI;
# Debian otherwise starts them right after configure with their stock
# config. The core services (lighttpd, php-fpm, muros-configd) start
# normally so the UI is reachable right after install. The policy file is
# removed at the end (a trap covers unexpected exits).
POLICY=/usr/sbin/policy-rc.d
POLICY_BAK="${POLICY}.muros-bak.$$"
if [ -e "$POLICY" ]; then
  mv "$POLICY" "$POLICY_BAK"
fi
cat > "$POLICY" <<'EOF'
#!/bin/sh
# Installed by MurOS install.sh to block auto-start of feature daemons
# during apt install. Removed at the end of install.sh.
case "$1" in
  kea-dhcp4-server|unbound|snmpd|fail2ban|keepalived|conntrackd|\
  strongswan|strongswan-starter|strongswan-swanctl|\
  openvpn|wg-quick@*)
    exit 101
    ;;
esac
exit 0
EOF
chmod +x "$POLICY"
trap 'rm -f "$POLICY"; if [ -e "$POLICY_BAK" ]; then mv "$POLICY_BAK" "$POLICY"; fi' EXIT INT TERM

if [ -n "${MUROS_VERSION:-}" ]; then
  # Tolerate a leading "v" (release tag form) in the requested version.
  WANT="${MUROS_VERSION#v}"
  echo "    -> installing muros=${WANT}"
  apt-get install -y "muros=${WANT}"
else
  apt-get install -y muros
fi

# Clean up the policy file; trap covers the case where apt-get fails.
rm -f "$POLICY"
if [ -e "$POLICY_BAK" ]; then mv "$POLICY_BAK" "$POLICY"; fi
trap - EXIT INT TERM

# Defensive sweep: make sure no config-required feature daemon is left
# running or in a "failed" state after install. The admin re-enables each
# from the UI once it is configured.
for svc in keepalived conntrackd \
           strongswan strongswan-starter wg-quick@wg0 \
           openvpn; do
  if systemctl list-unit-files "${svc}.service" >/dev/null 2>&1; then
    systemctl disable --now "${svc}.service" 2>/dev/null || true
    systemctl reset-failed "${svc}.service" 2>/dev/null || true
  fi
done

VER=$(dpkg-query -W -f='${Version}' muros 2>/dev/null || echo "?")
IP=$(hostname -I 2>/dev/null | awk '{print $1}')
cat <<EOF

MurOS ${VER} installed.

  UI     : https://${IP:-<ip-vm>}/  (self-signed snakeoil cert, accept the browser warning)
  Login  : root / muros  (default credentials, change them after first login)
  Log    : ${LOG}

Checks:
  systemctl status lighttpd php8.4-fpm muros-configd
  journalctl -u muros-configd -n 50 -f

Later upgrades:
  apt-get update && apt-get install --only-upgrade muros

Full uninstall (official, single method):
  curl -fsSL https://download.muros.org/uninstall.sh | sudo bash

EOF
