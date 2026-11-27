# Building the CalculanatorOS VirtualBox/PC image

This folder builds an **x86-64 Debian Live ISO**. After first registration,
the PC image opens the CalculanatorOS graphical desktop. The desktop detects
the display size, fits its layout and terminal window to that screen, and
offers a theme and custom wallpaper picker. The command shell remains
available from the Terminal card or by choosing `shell` as startup. A Debian
file manager opens the `CalculanatorOS_Files` folder from the Files card.

The ISO is for 64-bit PCs and VirtualBox. It is separate from the MicroPython
firmware for Raspberry Pi Pico 2 W. A Pico UF2 image cannot boot as a
VirtualBox PC image, and this x86-64 ISO cannot boot on the Pico.

## Build on Debian 13 (Trixie)

Install the build tools:

```sh
sudo apt update
sudo apt install live-build debootstrap debian-archive-keyring xorriso squashfs-tools isolinux syslinux-common grub-pc-bin grub-efi-amd64-bin mtools dosfstools
```

From the root of the downloaded CalculanatorOS source tree, build the image:

```sh
sudo bash ./boot-image/build-iso.sh
```

The resulting ISO and its SHA-256 file are written to `dist/`:

```text
dist/CalculanatorOS-live-amd64.iso
dist/CalculanatorOS-live-amd64.iso.sha256
```

Use Debian 13 (Trixie) for a local build so the host's `live-build` version
matches the target distribution. GitHub Actions builds inside a Debian Trixie
container. The first build downloads Debian packages and needs an internet
connection and several gigabytes of free disk space.

## Boot it in VirtualBox

Create a Linux/Debian (64-bit) VM, attach the ISO as its optical disk, and
start it with at least 2 GB RAM. The graphical desktop starts after registration.
Press **Esc** or **F11** to leave full screen. In VirtualBox, **Right Ctrl**
releases the host key; **Alt+F4** or the desktop's Return to Shell option closes
the desktop.

Type `DESKTOP` from the shell to reopen the UI. `SCREEN` shows the detected
display resolution and terminal dimensions. `WALLPAPER <path>` selects an
image and `WALLPAPER DEFAULT` resets it; the Personalize card opens visual
settings. PNG, JPG, GIF, BMP, and WEBP images are supported when Pillow is
installed. The desktop scales its cards and terminal window to the current
display size.

The shell has `SHUTDOWN` and `REBOOT` commands with a confirmation prompt.
`CALC SUDO` re-checks the CalculanatorOS password and requires an exact command
confirmation for SHUTDOWN, REBOOT, APT UPDATE, or APT INSTALL. It does not
provide an unrestricted root shell. Debian may separately request its system
account password. A Live session is temporary: saved files and settings are
lost at shutdown unless persistence or a writable system disk is configured.

## Automated build in GitHub Actions

The repository workflow at `.github/workflows/build-calculanatoros-iso.yml`
builds the ISO on pushes to `main` that change the PC app or image builder, and
can also be started manually. It uploads the ISO and checksum as a workflow
artifact. Publish that artifact as a GitHub Release asset when ready to
distribute a version publicly.
