# CalculanatorOS for Raspberry Pi Pico 2 W / WH

CalculanatorOS is an experimental MicroPython system shell for the Raspberry Pi Pico 2 W and Pico 2 WH. It is not desktop Linux or Windows. MicroPython provides the runtime and automatically starts `main.py` when the board boots.

## Editions

- `Pico-Modular`: learning edition split into modules, including `preferences.py` for saved settings. `devices.py` contains the board hardware interface.
- `Pico-SingleFile`: the same core features in one script. Rename it to `main.py` before uploading it to the board.

On first boot, the system asks you to register a username and password. On later boots, sign in with that account. The Pico stores account data in `calculanator_user.txt`; the password is stored as a hash, not as readable text. Some MicroPython USB consoles may display password input while you type. To reset registration, delete this file from the Pico flash using Thonny, then restart the board.

## Install on a Pico 2 W / WH

1. Download the official [MicroPython UF2 for Pico 2 W](https://micropython.org/download/RPI_PICO2_W/).
2. Connect the board over USB while holding BOOTSEL, then copy the UF2 file to the drive that appears.
3. Open the board in Thonny or another MicroPython editor.
4. For the modular edition, copy all Python files from `Pico-Modular` to the root of the board storage. `main.py` must sit beside the other modules.
5. For the single-file edition, upload `Pico-SingleFile/calculanator_os.py` as `main.py` instead.
6. Restart the Pico. The shell runs through the USB serial console. Ctrl+C returns to the MicroPython REPL.

## Commands and apps

`HELP`, `HELP_BOOK`, `APPS`, `APP <name>`, `STATUS`, `SCREEN`, `SETTINGS`, `FILES`, `STORAGE`, `HARDWARE`, `INFO`, `VER`, `DATE`, `UPTIME`, `LED ON/OFF`, `WIFI STATUS/SCAN/CONNECT/DISCONNECT`, `BT STATUS/SCAN`, `PKG HELP/LIST/INSTALL`, `NOTE`, `READ.NOTES`, `CALC`, `INSTRUMENTS`, `SHUTDOWN`, `REBOOT`, `CLEAR`, `EXIT`.

The app menu includes Calculator, Notes, Instruments, Personalize, Files, Network, and System Status. Add an app by adding a name, description, and callback to `APP_REGISTRY`.

`STATUS` shows uptime, approximate RP2350 chip temperature, LED, Wi-Fi, Bluetooth LE, and flash storage. `SETTINGS THEME <green|amber|ocean|plain>` saves a text frame style; `SETTINGS STARTUP <dashboard|menu|shell>` chooses the first view after sign-in. These preferences are stored in `calculanator_settings.txt`.

The Pico 2 W/WH has no built-in screen. CalculanatorOS uses the USB serial console, so the board cannot set the Thonny/terminal window size or display a wallpaper. Use `SCREEN` for this note and adjust the window in your computer's serial-console app.

Notes and installed packages are stored in internal flash. A note is limited to 512 characters. The Wi-Fi password is requested when connecting but is not saved. `BT SCAN` searches for Bluetooth Low Energy (BLE) devices; it does not pair with them. `PKG INSTALL name` uses MicroPython `mip`, asks for confirmation, requires Wi-Fi, and downloads third-party code to the board. Install only packages you trust. The instrument panel reads the RP2350 internal chip sensor; it reports approximate chip temperature, not room temperature.

## Power and limitations

CalculanatorOS is a firmware shell running on MicroPython, not a standalone kernel or a multi-user operating system. The Pico cannot run standard Linux or Windows. `SHUTDOWN` explains that power-off means unplugging the USB supply. `REBOOT` restarts the board only after you type the confirmation word. `EXIT` returns to the MicroPython prompt but leaves the board powered on.
