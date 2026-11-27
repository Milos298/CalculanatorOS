# CalculanatorOS

CalculanatorOS is an experimental Python project with two separate editions: MicroPython firmware for Raspberry Pi Pico 2 W/WH and a Debian-based PC edition. The Pico edition is a USB-serial shell, while the PC edition has a graphical desktop. Neither edition is a new operating-system kernel.

## Raspberry Pi Pico 2 W / WH

- [`Pico-Modular/`](Pico-Modular/): learning version split into modules. Copy all `.py` files to the Pico and keep `main.py` beside the other modules.
- [`Pico-SingleFile/calculanator_os.py`](Pico-SingleFile/calculanator_os.py): standalone version; upload it to the Pico as `main.py`.
- [`PICO-README.md`](PICO-README.md): Pico setup steps, commands, storage, hardware notes, and limitations.

The Pico edition has a system dashboard, app launcher, settings saved in flash, calculator, notes, files and network tools. Its LED, Wi-Fi, Bluetooth LE, and RP2350 chip-temperature sensor use the board hardware. The Pico board has no built-in screen, so its text appears in Thonny or another USB serial terminal; the PC terminal controls its window size and colors.

`SHUTDOWN` explains how to turn off the board by unplugging its USB power. `REBOOT` restarts after a confirmation. `EXIT` returns to the MicroPython prompt while leaving the board powered.

## PC edition

The root [`CalculanatorOS.py`](CalculanatorOS.py) file provides the command shell. [`CalculanatorOS_Desktop.py`](CalculanatorOS_Desktop.py) adds a responsive desktop with calculator, notes, files, themes, and a custom wallpaper picker. Use **Esc** or **F11** to leave full screen.

The shell has `SHUTDOWN` and `REBOOT` with confirmation, `DESKTOP` to reopen the UI, and `SCREEN` to show the detected resolution. `CALC SUDO` requires the app password and an exact confirmation for limited APT and power actions; it does not open an unrestricted root shell.

The [`boot-image/`](boot-image/) folder builds an x86-64 Debian Live ISO for a PC or VirtualBox. It is separate from the Pico firmware. A live session is temporary unless persistence or a writable system disk is configured. See [`boot-image/README.md`](boot-image/README.md) for build and boot instructions.

The GitHub Actions workflow builds the ISO when the PC app or image builder changes. It uploads the ISO and checksum as workflow artifacts; it does not automatically create a public release.
