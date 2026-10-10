# CalculanatorOS for Raspberry Pi Pico 2 W

CalculanatorOS is an experimental firmware shell for the Raspberry Pi Pico 2 W. It is not desktop Linux or Windows. MicroPython provides the runtime and automatically starts `main.py` when the board boots.

## Editions

- `Pico-Modular`: learning edition split into separate modules. `devices.py` contains the board hardware interface.
- `Pico-SingleFile`: the same core features in one script. Rename it to `main.py` before uploading it to the board.

On first boot, the system asks you to register a username and password. On later boots, sign in with that account. The Pico stores account data in `calculanator_user.txt`; the password is stored as a hash, not as readable text. Some MicroPython USB consoles may display password input while you type. To reset registration, delete this file from the Pico flash using Thonny, then restart the board.

## Install on a Pico 2 W

1. Download the official [MicroPython UF2 for Pico 2 W](https://micropython.org/download/RPI_PICO2_W/).
2. Connect the board over USB while holding BOOTSEL, then copy the UF2 file to the drive that appears.
3. Open the board in Thonny or another MicroPython editor.
4. Copy all files from `Pico-Modular` to the root of the board storage. `main.py` must sit beside the other modules.
5. Restart the Pico. The shell runs through the USB serial console. Ctrl+C returns to the MicroPython REPL.

For the single-file edition, upload `Pico-SingleFile/calculanator_os.py` as `main.py`.

## Commands

`HELP`, `HELP_BOOK`, `APPS`, `APP <name>`, `HARDWARE`, `INFO`, `VER`, `DATE`, `UPTIME`, `LED ON/OFF`, `WIFI STATUS/SCAN/CONNECT/DISCONNECT`, `SCAN`, `CONNECT`, `DISCONNECT`, `NETINFO`, `IP`, `BT STATUS/SCAN`, `PKG HELP/LIST/INSTALL`, `NOTE`, `READ.NOTES`, `CALC`, `INSTRUMENTS`, `MATRIX`, `REBOOT`, `EXIT`.

Notes and installed packages are stored in internal flash. The Wi-Fi password is requested when connecting but is not saved. `BT SCAN` searches for Bluetooth Low Energy (BLE) devices; it does not pair with them. `PKG INSTALL name` uses MicroPython `mip`, asks for confirmation, requires Wi-Fi, and downloads third-party code to the board. Install only packages you trust. The Pico instrument panel reads the RP2350 internal chip sensor. It reports approximate chip temperature, not room temperature; connect an external sensor to measure ambient temperature. The PC build keeps hardware access in simulation mode.

## Limitations

CalculanatorOS is a firmware shell running on MicroPython, not a standalone kernel or a multi-user operating system. The Pico 2 W is a microcontroller and cannot run standard Linux or Windows. `EXIT` closes the shell but does not power off the board.
