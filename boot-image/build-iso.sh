#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
    echo "Run this builder with sudo: sudo bash ./boot-image/build-iso.sh" >&2
    exit 1
fi

PACKAGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${PACKAGE_DIR}/.build-live-image"
CONFIG_DIR="${BUILD_DIR}/config"

command -v lb >/dev/null || {
    echo "Missing live-build. On Debian/Ubuntu install: live-build debootstrap debian-archive-keyring xorriso squashfs-tools" >&2
    exit 1
}

APP_SOURCE="${PACKAGE_DIR}/desktop/CalculanatorOS.py"
if [[ ! -f "${APP_SOURCE}" ]]; then
    APP_SOURCE="${PACKAGE_DIR}/CalculanatorOS.py"
fi
if [[ ! -f "${APP_SOURCE}" ]]; then
    echo "Could not find desktop/CalculanatorOS.py or CalculanatorOS.py in the repository root." >&2
    exit 1
fi

rm -rf "${BUILD_DIR}"
mkdir -p \
    "${CONFIG_DIR}/package-lists" \
    "${CONFIG_DIR}/includes.chroot/etc/skel" \
    "${CONFIG_DIR}/includes.chroot/etc/systemd/system/getty@tty1.service.d"

cp "${APP_SOURCE}" \
    "${CONFIG_DIR}/includes.chroot/etc/skel/CalculanatorOS.py"
cp "${PACKAGE_DIR}/boot-image/.bash_profile" \
    "${CONFIG_DIR}/includes.chroot/etc/skel/.bash_profile"
cp "${PACKAGE_DIR}/boot-image/autologin.conf" \
    "${CONFIG_DIR}/includes.chroot/etc/systemd/system/getty@tty1.service.d/autologin.conf"
cp "${PACKAGE_DIR}/boot-image/calculanatoros.list.chroot" \
    "${CONFIG_DIR}/package-lists/calculanatoros.list.chroot"

cd "${BUILD_DIR}"
lb config \
    --mode debian \
    --distribution trixie \
    --architectures amd64 \
    --binary-images iso-hybrid \
    --archive-areas "main contrib non-free-firmware" \
    --mirror-bootstrap "http://deb.debian.org/debian/" \
    --mirror-chroot-security "http://security.debian.org/debian-security/" \
    --mirror-binary "http://deb.debian.org/debian/" \
    --mirror-binary-security "http://security.debian.org/debian-security/" \
    --iso-application "CalculanatorOS Live" \
    --iso-volume "CALCULANATOROS" \
    --bootappend-live "boot=live components username=calculanator hostname=calculanatoros locales=en_US.UTF-8 keyboard-layouts=us"

lb build

OUTPUT_DIR="${PACKAGE_DIR}/dist"
mkdir -p "${OUTPUT_DIR}"
cp live-image-amd64.hybrid.iso "${OUTPUT_DIR}/CalculanatorOS-live-amd64.iso"
sha256sum "${OUTPUT_DIR}/CalculanatorOS-live-amd64.iso" \
    > "${OUTPUT_DIR}/CalculanatorOS-live-amd64.iso.sha256"

echo "Created ${OUTPUT_DIR}/CalculanatorOS-live-amd64.iso"
