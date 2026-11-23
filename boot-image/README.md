# Building the CalculanatorOS VirtualBox/PC image

This folder builds an **x86-64 bootable Debian Live ISO** that automatically
opens the existing CalculanatorOS Python shell on its first text console. It
is a complete bootable Linux environment with CalculanatorOS as its main shell
application; it does not turn the Python project into a new Linux kernel.

The ISO is for 64-bit PCs and VirtualBox. It is separate from the MicroPython
firmware for Raspberry Pi Pico 2 W. A Pico UF2 image cannot boot as a VirtualBox
PC image, and this x86-64 ISO cannot boot on the Pico.

## Build on Debian or Ubuntu

Install the build tools:

```sh
sudo apt update
sudo apt install live-build debootstrap xorriso squashfs-tools isolinux syslinux-common grub-pc-bin grub-efi-amd64-bin mtools dosfstools
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

The first build downloads Debian packages and needs an internet connection and
several gigabytes of free disk space. The live session is temporary: files
saved during a session are lost at shutdown unless a virtual hard disk or
persistence is configured. The app's own registration is a convenience for
the shell and is not an operating-system security boundary.

## Boot it in VirtualBox

Create a new Linux/Debian (64-bit) virtual machine, attach the ISO as its
optical disk, and start it. Give it at least 2 GB RAM and a 16 GB virtual disk
if you later want to install a writable system. To try the live image, no
installation to that disk is required. The image starts CalculanatorOS on
`tty1`; use `Ctrl+Alt+F2` to switch to another text console.

## Automated build in GitHub Actions

The repository workflow at `.github/workflows/build-calculanatoros-iso.yml`
can build the ISO when manually started from the Actions tab. It uploads the
ISO and checksum as a downloadable workflow artifact. Publish that artifact as
a GitHub Release asset when ready to distribute a version to the public.
