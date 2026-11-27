"""CalculanatorOS shell commands."""
import random
import time
import os
import config
import calculator
import devices
import storage
import preferences

HELP = (
    "HELP | HELP_BOOK | APPS | APP <name> | STATUS | SCREEN | SETTINGS [THEME|STARTUP] | "
    "HARDWARE | INFO | VER | DATE | UPTIME | LED ON/OFF | WIFI [STATUS|IP|SCAN|CONNECT|DISCONNECT] | "
    "BT [STATUS|SCAN] | PKG [HELP|LIST|INSTALL <name>] | NOTE [text] | READ.NOTES | CALC [expression] | "
    "FILES | STORAGE | INSTRUMENTS | MATRIX | SHUTDOWN | REBOOT | CLEAR | EXIT"
)
LED_STATE = False
PREFERENCES = preferences.load()
FRAME_CHARS = {"green": "#", "amber": "=", "ocean": "~", "plain": "-"}
HELP_BOOK = (
    "HELP — show the short command list.",
    "HELP_BOOK — show these numbered command descriptions.",
    "APPS — open the app launcher; add apps in APP_REGISTRY.",
    "APP <name> — launch calculator, notes, instruments, settings, files, network, or system status.",
    "STATUS or DASHBOARD — show temperature, LED, Wi-Fi, Bluetooth, uptime, and flash space.",
    "SCREEN — explain the USB serial display and where to change its size.",
    "SETTINGS — show saved theme and startup preferences.",
    "SETTINGS THEME <green|amber|ocean|plain> — save the ASCII frame style (the terminal app controls colors).",
    "SETTINGS STARTUP <dashboard|menu|shell> — choose the first view after login.",
    "SETTINGS RESET — restore default theme and startup preferences.",
    "HARDWARE — explain which commands use real Pico hardware.",
    "INFO, VER, VERSION — show system information and firmware version.",
    "DATE, UPTIME — show the Pico clock or time since the last restart.",
    "LED ON or LED OFF — control the onboard Pico LED.",
    "WIFI STATUS or WIFI IP — show connection state and IP address.",
    "WIFI SCAN — list nearby Wi-Fi networks and signal strength.",
    "WIFI CONNECT [SSID] — connect without saving the Wi-Fi password.",
    "WIFI DISCONNECT — disconnect the wireless interface.",
    "SCAN, CONNECT, DISCONNECT, NETINFO, IP — short Wi-Fi command aliases.",
    "BT STATUS or BLUETOOTH — show Bluetooth Low Energy status.",
    "BT SCAN — discover nearby BLE devices; it does not pair with them.",
    "PKG HELP, PKG LIST, PKG INSTALL <name> — manage MicroPython packages with mip.",
    "NOTE [text], READ.NOTES — save or read notes in Pico flash storage.",
    "CALC [expression] — calculate safe arithmetic; input is limited to 256 characters.",
    "FILES — list user-visible files on Pico flash; account and settings files are hidden.",
    "STORAGE — show available Pico flash capacity when MicroPython reports it.",
    "INSTRUMENTS or INSTRUMENT_PANEL — open the live chip sensor and device panel.",
    "MATRIX — print a short text animation.",
    "SHUTDOWN or POWER OFF — explain safe power-off; unplug the Pico's USB supply.",
    "REBOOT or RESTART — restart the board after typing REBOOT to confirm.",
    "CLEAR — clear the serial view with blank lines; terminal apps may also have a clear-screen shortcut.",
    "EXIT or QUIT — return from CalculanatorOS to the MicroPython prompt; power stays on.",
    "PING — ICMP ping is not implemented in this MicroPython shell.",
    "BLE note — Bluetooth scan discovers devices but does not pair with them.",
    "Network note — Wi-Fi passwords are requested for a connection and are not saved.",
)


def show_banner():
    theme = PREFERENCES["theme"]
    edge = FRAME_CHARS.get(theme, "=")
    line = edge * 52
    print("\n" + line)
    print("|                 CALCULANATOROS                  |")
    print("|              PICO 2 W / WH EDITION              |")
    print(line)
    print(config.VERSION, "| BUILD", config.BUILD, "| STYLE", theme.upper())


def show_dashboard():
    edge = FRAME_CHARS.get(PREFERENCES["theme"], "=")
    print("\n" + edge * 52)
    print("|             CALCULANATOROS SYSTEM STATUS        |")
    print(edge * 52)
    try:
        print("Uptime:", time.ticks_ms() // 1000, "seconds")
    except Exception:
        print("Uptime: unavailable")
    temperature, error = devices.chip_temperature_celsius()
    if error:
        print("Chip sensor:", error)
    else:
        print("RP2350 chip temperature:", round(temperature, 1), "C (approximate)")
    led, error = devices.led_state()
    print("On-board LED:", error if error else ("on" if led else "off"))
    print("Wi-Fi:", devices.wifi_status())
    print("Bluetooth LE:", devices.bluetooth_status())
    try:
        stats = os.statvfs(".")
        total = stats[0] * stats[2]
        free = stats[0] * stats[3]
        print("Flash storage:", round(free / 1024), "KiB free of", round(total / 1024), "KiB")
    except Exception:
        print("Flash storage: information unavailable")
    print("Type APPS to launch an app, HELP for commands, or SCREEN for display details.")
    print(edge * 52)


def save_preferences():
    try:
        preferences.save(PREFERENCES)
        print("Settings saved to", preferences.SETTINGS_FILE)
    except Exception as error:
        print("Could not save settings:", error)


def settings_command(argument=""):
    cleaned = " ".join(argument.strip().split())
    parts = cleaned.split(" ", 1) if cleaned else []
    if not parts:
        print("Theme:", PREFERENCES["theme"], "| Startup:", PREFERENCES["startup"])
        print("Use SETTINGS THEME <green|amber|ocean|plain> (ASCII frame style; terminal apps control colors).")
        print("Use SETTINGS STARTUP <dashboard|menu|shell> or SETTINGS RESET")
        print("Screen: USB serial console; change its size in Thonny or your terminal app.")
        return
    key = parts[0].lower()
    value = parts[1].strip().lower() if len(parts) > 1 else ""
    if key == "theme" and value in preferences.THEMES:
        PREFERENCES["theme"] = value
        save_preferences()
    elif key == "startup" and value in preferences.STARTUP_MODES:
        PREFERENCES["startup"] = value
        save_preferences()
    elif key == "reset" and not value:
        PREFERENCES.update(preferences.DEFAULTS)
        save_preferences()
    else:
        print("Invalid setting. Type SETTINGS to see valid options.")


def _hidden_input(label):
    try:
        import getpass
        return getpass.getpass(label)
    except Exception:
        print("This serial console may show the password while you type.")
        return input(label)


def app_files():
    hidden = ("calculanator_user.txt", preferences.SETTINGS_FILE)
    try:
        names = sorted(name for name in os.listdir() if name not in hidden)
        print("Pico flash files:")
        for name in names:
            print(" -", name)
        if not names:
            print(" - no user files yet")
    except Exception as error:
        print("Could not read the file list:", error)


def show_storage():
    try:
        stats = os.statvfs(".")
        total = stats[0] * stats[2]
        free = stats[0] * stats[3]
        print("Flash storage:", round(free / 1024), "KiB free of", round(total / 1024), "KiB")
    except Exception as error:
        print("Flash storage information is unavailable:", error)


def app_network():
    while True:
        print("\n=== NETWORK TOOLS ===")
        print("1 Wi-Fi status | 2 Scan Wi-Fi | 3 Connect Wi-Fi | 4 Disconnect Wi-Fi")
        print("5 Bluetooth status | 6 Scan BLE | 0 Back")
        choice = input("Network> ").strip()
        actions = {"1": "WIFI STATUS", "2": "WIFI SCAN", "3": "WIFI CONNECT",
                   "4": "WIFI DISCONNECT", "5": "BT STATUS", "6": "BT SCAN"}
        if choice in ("0", "BACK"):
            return
        if choice in actions:
            run(actions[choice])
        else:
            print("Choose 0 through 6.")

def app_calculator():
    run("CALC")

def app_notes():
    run("NOTE")

def app_instruments():
    instrument_panel()

def app_settings():
    while True:
        print("\n=== PERSONALIZE PICO ===")
        print("Theme:", PREFERENCES["theme"], "| Startup:", PREFERENCES["startup"])
        print("1 Change theme | 2 Startup view | 3 Reset settings | 0 Back")
        choice = input("Settings> ").strip()
        if choice in ("0", "BACK"):
            return
        if choice == "1":
            value = input("Theme (green/amber/ocean/plain): ").strip()
            settings_command("THEME " + value)
        elif choice == "2":
            value = input("Startup (dashboard/menu/shell): ").strip()
            settings_command("STARTUP " + value)
        elif choice == "3":
            if input("Type RESET to restore defaults: ").strip().upper() == "RESET":
                settings_command("RESET")
            else:
                print("Reset cancelled.")
        else:
            print("Choose 0, 1, 2, or 3.")

# Register another app by adding a name/description/callback pair here.
APP_REGISTRY = {
    "calculator": ("Run the safe arithmetic calculator.", app_calculator),
    "notes": ("Create a note in Pico flash storage.", app_notes),
    "instruments": ("Open the board hardware panel.", app_instruments),
    "settings": ("Change saved text theme and startup view.", app_settings),
    "files": ("List files saved on Pico flash.", app_files),
    "network": ("Open Wi-Fi and Bluetooth tools.", app_network),
    "system": ("Show the hardware status dashboard.", show_dashboard),
}

def apps_menu():
    names = list(APP_REGISTRY)
    while True:
        print("=== CALCULANATOROS APPS ===")
        for index, name in enumerate(names, 1):
            print(str(index) + ".", name.title(), "—", APP_REGISTRY[name][0])
        print("0. Back")
        choice = input("Apps> ").strip().lower()
        if choice == "0":
            return
        if choice.isdigit() and 1 <= int(choice) <= len(names):
            APP_REGISTRY[names[int(choice) - 1]][1]()
        elif choice in APP_REGISTRY:
            APP_REGISTRY[choice][1]()
        else:
            print("Choose an app number, name, or 0.")

def instrument_panel():
    global LED_STATE
    while True:
        print("=== INSTRUMENT PANEL ===")
        print("1 RP2350 chip temperature | 2 Uptime | 3 Wi-Fi | 4 LED | 5 BLE scan | 0 Back")
        choice = input("Instrument> ").strip()
        if choice == "1":
            temperature, error = devices.chip_temperature_celsius()
            if error:
                print(error)
            else:
                print("RP2350 chip temperature:", round(temperature, 1), "°C (approximate; not room temperature)")
        elif choice == "2":
            try:
                print("Running for", time.ticks_ms() // 1000, "seconds." )
            except Exception:
                print("The timer is unavailable.")
        elif choice == "3":
            print(devices.wifi_status())
        elif choice == "4":
            current, error = devices.led_state()
            if error:
                print(error)
            else:
                LED_STATE = not current
                print(devices.led_set(LED_STATE)[1])
        elif choice == "5":
            found, error = devices.bluetooth_scan()
            if error:
                print("Bluetooth scan failed:", error)
            elif not found:
                print("No BLE devices found.")
            else:
                for address, details in found.items():
                    print("-", details[0], address, "RSSI", details[1], "dBm")
        elif choice == "0":
            return
        else:
            print("Choose 0, 1, 2, 3, 4, or 5.")

def package_command(arg):
    parts = arg.strip().split(" ", 1)
    action = parts[0].upper() if parts else "HELP"
    package = parts[1].strip() if len(parts) > 1 else ""
    if action == "HELP":
        print("PKG LIST | PKG INSTALL <micropython-lib-package>")
        print("Installation requires Wi-Fi. A package runs third-party Python code.")
    elif action == "LIST":
        try:
            names = [name for name in os.listdir() if name.endswith((".py", ".mpy"))]
            print("Python files:", ", ".join(names) if names else "none")
        except Exception as error:
            print("Could not list files:", error)
    elif action == "INSTALL":
        if not package or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for char in package):
            print("Usage: PKG INSTALL package_name")
            return
        if input("Install package '" + package + "'? Type INSTALL to confirm: ").strip() != "INSTALL":
            print("Installation cancelled.")
            return
        try:
            import mip
            mip.install(package)
            print("Installation complete:", package)
        except Exception as error:
            print("Installation failed:", error)
    else:
        print("Unknown action. Use PKG HELP.")

def run(command):
    cleaned = " ".join(command.strip().split())
    parts = cleaned.split(" ", 1) if cleaned else []
    name = parts[0].upper() if parts else ""
    arg = parts[1].strip() if len(parts) > 1 else ""
    if not name:
        return True
    if name in ("EXIT", "QUIT"):
        print("The shell is closing. The Pico will remain powered on.")
        return False
    if name == "HELP":
        print("Commands:", HELP)
    elif name == "HELP_BOOK":
        print("=== CALCULANATOROS HELP BOOK ===")
        for number, description in enumerate(HELP_BOOK, 1):
            print("%02d | %s" % (number, description))
    elif name in ("STATUS", "DASHBOARD"):
        show_dashboard()
    elif name == "SCREEN":
        print("Pico 2 W / WH has no built-in display. CalculanatorOS uses the USB serial console.")
        print("Change the console window size in Thonny or your terminal app; the firmware cannot resize it.")
        print("Saved text style:", PREFERENCES["theme"])
    elif name == "SETTINGS":
        settings_command(arg)
    elif name in ("CLEAR", "CLS"):
        print("\n" * 24)
    elif name in ("FILES", "FILETREE", "TREE") or (name == "FILE" and arg.upper() == "TREE"):
        app_files()
    elif name == "STORAGE":
        show_storage()
    elif name in ("SHUTDOWN", "POWER"):
        if name == "POWER" and arg.upper() != "OFF":
            print("Usage: POWER OFF")
        else:
            print("Pico 2 W / WH has no software power-off command. Unplug its USB power to turn it off.")
            print("Use EXIT to return to MicroPython, or REBOOT to restart the board.")
    elif name == "INFO":
        print(config.NAME, "is an experimental firmware shell for the Pico 2 W / WH.")
        print("It runs on MicroPython; it is not desktop Linux or Windows.")
    elif name == "HARDWARE":
        print("Mode: PICO HARDWARE. The LED, Wi-Fi, Bluetooth LE, and RP2350 chip-temperature sensor use board hardware.")
        print("The internal temperature reading is approximate chip temperature, not room temperature.")
    elif name == "APPS":
        apps_menu()
    elif name == "APP":
        app = arg.lower()
        if app in APP_REGISTRY:
            APP_REGISTRY[app][1]()
        else:
            print("Usage: APP <" + "|".join(APP_REGISTRY) + ">")
    elif name in ("VER", "VERSION"):
        print(config.NAME, config.VERSION, "build", config.BUILD)
    elif name == "DATE":
        print(time.localtime())
    elif name == "UPTIME":
        try:
            print("Running for", time.ticks_ms() // 1000, "seconds." )
        except Exception:
            print("The timer is unavailable.")
    elif name == "LED":
        state = arg.lower()
        if state not in ("on", "off"):
            print("Usage: LED ON or LED OFF")
        else:
            print(devices.led_set(state == "on")[1])
    elif name == "WIFI" and arg.upper().split(" ", 1)[0] in ("SCAN", "CONNECT", "DISCONNECT", "STATUS", "IP"):
        wifi_parts = arg.split(" ", 1)
        action = wifi_parts[0].upper()
        wifi_name = wifi_parts[1].strip() if len(wifi_parts) > 1 else ""
        if action == "SCAN":
            rows, error = devices.wifi_scan()
            if error:
                print("Scan failed:", error)
            else:
                for row in rows:
                    try:
                        ssid = row[0].decode()
                    except Exception:
                        ssid = str(row[0])
                    print("-", ssid, "RSSI", row[3], "dBm")
        elif action == "CONNECT":
            ssid = wifi_name or input("Wi-Fi name (SSID): ").strip()
            if not ssid:
                print("A Wi-Fi name is required.")
            else:
                password = _hidden_input("Wi-Fi password (not saved): ")
                print(devices.wifi_connect(ssid, password)[1])
        elif action == "DISCONNECT":
            _, wlan = devices.wifi_interface()
            if wlan:
                wlan.disconnect()
                print("Wi-Fi disconnected.")
            else:
                print("Wi-Fi is unavailable.")
        else:
            print(devices.wifi_status())
    elif name in ("WIFI", "NETINFO", "IP"):
        print(devices.wifi_status())
    elif name == "SCAN":
        return run("WIFI SCAN")
    elif name in ("BT", "BLUETOOTH"):
        action = arg.upper() or "STATUS"
        if action in ("STATUS", "INFO"):
            print(devices.bluetooth_status())
        elif action == "SCAN":
            print("Scanning for Bluetooth LE devices for 5 seconds...")
            found, error = devices.bluetooth_scan()
            if error:
                print("Bluetooth scan failed:", error)
            elif not found:
                print("No BLE devices found.")
            else:
                for address, details in found.items():
                    print("-", details[0], address, "RSSI", details[1], "dBm")
        else:
            print("Usage: BT STATUS or BT SCAN (Bluetooth Low Energy)")
    elif name == "PKG":
        package_command(arg)
    elif name == "CONNECT":
        return run("WIFI CONNECT" + (" " + arg if arg else ""))
    elif name == "DISCONNECT":
        return run("WIFI DISCONNECT")
    elif name == "NOTE":
        note = arg or input("Note: ")
        if not note.strip():
            print("A note cannot be empty.")
        elif len(note) > 512:
            print("A note can be up to 512 characters to protect Pico flash space.")
        else:
            try:
                storage.add_note(note)
                print("Note saved to", config.NOTES_FILE)
            except OSError as error:
                print("Could not save note:", error)
    elif name == "READ.NOTES":
        notes = storage.read_notes()
        print(notes if notes else "There are no notes yet.")
    elif name == "CALC":
        expression = arg or input("Example 2*(3+4): ")
        try:
            print("=", calculator.calculate(expression))
        except Exception as error:
            print("Expression error:", error)
    elif name in ("INSTRUMENTS", "INSTRUMENT_PANEL"):
        instrument_panel()
    elif name == "MATRIX":
        alphabet = "01ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for _ in range(10):
            print("".join(random.choice(alphabet) for _ in range(32)))
            if hasattr(time, "sleep_ms"):
                time.sleep_ms(80)
            else:
                time.sleep(0.08)
    elif name in ("REBOOT", "RESTART"):
        if input("Type REBOOT to restart the Pico: ").strip().upper() != "REBOOT":
            print("Restart cancelled.")
            return True
        try:
            import machine
            print("Restarting...")
            machine.reset()
        except Exception:
            print("Restart is only available on a Pico.")
    elif name == "PING":
        print("ICMP ping is not implemented in this MicroPython shell.")
    else:
        print("Unknown command. Type HELP.")
    return True
