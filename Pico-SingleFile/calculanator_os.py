"""CalculanatorOS standalone MicroPython version for the Pico 2 W / WH.
Upload this file as main.py to a board running MicroPython.
"""
import random
import time
import os
import hashlib

NAME = "CalculanatorOS"
VERSION = "0.6.0"
BUILD = "2026-11-26"
NOTES = "notes.txt"
SETTINGS_FILE = "calculanator_settings.txt"
THEMES = ("green", "amber", "ocean", "plain")
STARTUP_MODES = ("dashboard", "menu", "shell")
DEFAULT_PREFERENCES = {"theme": "ocean", "startup": "dashboard"}
PREFERENCES = dict(DEFAULT_PREFERENCES)
LED_STATE = [False]
HELP = (
    "HELP | HELP_BOOK | APPS | APP <name> | STATUS | SCREEN | SETTINGS [THEME|STARTUP] | "
    "HARDWARE | INFO | VER | DATE | UPTIME | LED ON/OFF | WIFI [STATUS|IP|SCAN|CONNECT|DISCONNECT] | "
    "BT [STATUS|SCAN] | PKG [HELP|LIST|INSTALL <name>] | NOTE [text] | READ.NOTES | CALC [expression] | "
    "FILES | STORAGE | INSTRUMENTS | MATRIX | SHUTDOWN | REBOOT | CLEAR | EXIT"
)
HELP_BOOK = (
    "HELP — show the short command list.",
    "HELP_BOOK — show these numbered command descriptions.",
    "APPS — open the app launcher; add apps in APP_REGISTRY.",
    "APP <name> — launch a built-in app by name.",
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
    "CLEAR — clear the serial view with blank lines.",
    "EXIT or QUIT — return from CalculanatorOS to the MicroPython prompt; power stays on.",
    "PING — ICMP ping is not implemented in this MicroPython shell.",
    "Network note — Wi-Fi passwords are requested for a connection and are not saved.",
)

def calculate(text):
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Enter a mathematical expression.")
    if len(text) > 256:
        raise ValueError("Expression is too long (maximum 256 characters).")
    text = "".join(text.split())
    pos = [0]
    depth = [0]
    def peek():
        return text[pos[0]] if pos[0] < len(text) else ""
    def take():
        char = peek()
        if not char:
            raise ValueError("Expression is incomplete.")
        pos[0] += 1
        return char
    def factor():
        sign = 1
        while peek() in ("+", "-"):
            if take() == "-":
                sign = -sign
        if peek() == "(":
            take()
            if depth[0] >= 24:
                raise ValueError("Parentheses are nested too deeply (maximum 24 levels).")
            depth[0] += 1
            try:
                value = expression()
            finally:
                depth[0] -= 1
            if take() != ")":
                raise ValueError("Missing closing parenthesis.")
            return sign * value
        start = pos[0]
        dot = False
        while peek().isdigit() or (peek() == "." and not dot):
            if peek() == ".":
                dot = True
            take()
        if start == pos[0]:
            raise ValueError("Expected a number.")
        try:
            return sign * float(text[start:pos[0]])
        except ValueError:
            raise ValueError("Enter a valid number.")
    def term():
        value = factor()
        while peek() in ("*", "/"):
            op = take()
            right = factor()
            if op == "/":
                if right == 0:
                    raise ValueError("Division by zero is not allowed.")
                value /= right
            else:
                value *= right
        return value
    def expression():
        value = term()
        while peek() in ("+", "-"):
            op = take()
            right = term()
            value = value + right if op == "+" else value - right
        return value
    result = expression()
    if pos[0] != len(text):
        raise ValueError("Unexpected character: " + text[pos[0]])
    return result

def get_wifi():
    try:
        import network
        mode = getattr(network, "STA_IF", None)
        if mode is None:
            mode = network.WLAN.IF_STA
        return network.WLAN(mode)
    except Exception:
        return None

def load_preferences():
    values = dict(DEFAULT_PREFERENCES)
    try:
        with open(SETTINGS_FILE, "r") as file:
            for line in file:
                parts = line.strip().split("=", 1)
                if len(parts) != 2:
                    continue
                key, value = parts
                if key == "theme" and value in THEMES:
                    values["theme"] = value
                elif key == "startup" and value in STARTUP_MODES:
                    values["startup"] = value
    except OSError:
        pass
    return values

def save_preferences():
    if PREFERENCES["theme"] not in THEMES or PREFERENCES["startup"] not in STARTUP_MODES:
        print("Invalid preferences; settings were not saved.")
        return
    try:
        with open(SETTINGS_FILE, "w") as file:
            file.write("theme=" + PREFERENCES["theme"] + "\n")
            file.write("startup=" + PREFERENCES["startup"] + "\n")
        print("Settings saved to", SETTINGS_FILE)
    except OSError as error:
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
    if key == "theme" and value in THEMES:
        PREFERENCES["theme"] = value
        save_preferences()
    elif key == "startup" and value in STARTUP_MODES:
        PREFERENCES["startup"] = value
        save_preferences()
    elif key == "reset" and not value:
        PREFERENCES.update(DEFAULT_PREFERENCES)
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

def wifi_status():
    wlan = get_wifi()
    if wlan is None:
        return "Wi-Fi is unavailable."
    try:
        if wlan.isconnected():
            return "Connected. IP: " + wlan.ifconfig()[0]
        return "Wi-Fi is not connected."
    except Exception as error:
        return "Wi-Fi error: " + str(error)

def show_banner():
    edge = {"green": "#", "amber": "=", "ocean": "~", "plain": "-"}.get(PREFERENCES["theme"], "=")
    line = edge * 52
    print("\n" + line)
    print("|                 CALCULANATOROS                  |")
    print("|              PICO 2 W / WH EDITION              |")
    print(line)
    print(VERSION, "| BUILD", BUILD, "| STYLE", PREFERENCES["theme"].upper())

def show_storage():
    try:
        stats = os.statvfs(".")
        print("Flash storage:", round(stats[0] * stats[3] / 1024), "KiB free of",
              round(stats[0] * stats[2] / 1024), "KiB")
    except Exception as error:
        print("Flash storage information is unavailable:", error)

def show_dashboard():
    edge = {"green": "#", "amber": "=", "ocean": "~", "plain": "-"}.get(PREFERENCES["theme"], "=")
    print("\n" + edge * 52)
    print("|             CALCULANATOROS SYSTEM STATUS        |")
    print(edge * 52)
    try:
        print("Uptime:", time.ticks_ms() // 1000, "seconds")
    except Exception:
        print("Uptime: unavailable")
    temperature, error = chip_temperature_celsius()
    print("RP2350 chip temperature:", error if error else str(round(temperature, 1)) + " C (approximate)")
    try:
        from machine import Pin
        led = bool(Pin("LED", Pin.OUT).value())
        print("On-board LED:", "on" if led else "off")
    except Exception as error:
        print("On-board LED:", error)
    print("Wi-Fi:", wifi_status())
    print("Bluetooth LE:", bluetooth_status())
    show_storage()
    print("Type APPS to launch an app, HELP for commands, or SCREEN for display details.")
    print(edge * 52)

def app_files():
    hidden = ("calculanator_user.txt", SETTINGS_FILE)
    try:
        names = sorted(name for name in os.listdir() if name not in hidden)
        print("Pico flash files:")
        for name in names:
            print(" -", name)
        if not names:
            print(" - no user files yet")
    except Exception as error:
        print("Could not read the file list:", error)

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

def chip_temperature_celsius():
    """Read approximate RP2350 chip temperature, not room temperature."""
    try:
        from machine import ADC
        voltage = ADC(4).read_u16() * (3.3 / 65535)
        return 27 - (voltage - 0.706) / 0.001721, None
    except Exception as error:
        return None, str(error)

def password_prompt(label):
    try:
        import getpass
        return getpass.getpass(label)
    except Exception:
        # Some MicroPython USB REPLs echo the typed password.
        return input(label)

def hash_password(password, salt):
    value = (salt + password).encode()
    for _ in range(1024):
        value = hashlib.sha256(value).digest()
    return "".join("%02x" % byte for byte in value)

def make_salt():
    try:
        raw = os.urandom(16)
        return "".join("%02x" % byte for byte in raw)
    except Exception:
        return "%08x%08x%08x%08x" % tuple(random.getrandbits(32) for _ in range(4))

def open_calculator_app():
    run("CALC")

def open_notes_app():
    run("NOTE")

def open_instruments_app():
    run("INSTRUMENTS")

def open_settings_app():
    while True:
        print("\n=== PERSONALIZE PICO ===")
        print("Theme:", PREFERENCES["theme"], "| Startup:", PREFERENCES["startup"])
        print("1 Change theme | 2 Startup view | 3 Reset settings | 0 Back")
        choice = input("Settings> ").strip()
        if choice in ("0", "BACK"):
            return
        if choice == "1":
            settings_command("THEME " + input("Theme (green/amber/ocean/plain): ").strip())
        elif choice == "2":
            settings_command("STARTUP " + input("Startup (dashboard/menu/shell): ").strip())
        elif choice == "3":
            if input("Type RESET to restore defaults: ").strip().upper() == "RESET":
                settings_command("RESET")
            else:
                print("Reset cancelled.")
        else:
            print("Choose 0, 1, 2, or 3.")

# Add another app by adding a name/description/callback entry here.
APP_REGISTRY = {
    "calculator": ("Run the arithmetic calculator.", open_calculator_app),
    "notes": ("Create and read notes.", open_notes_app),
    "instruments": ("Open the Pico hardware panel.", open_instruments_app),
    "settings": ("Change saved text theme and startup view.", open_settings_app),
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

def register_or_login():
    account_file = "calculanator_user.txt"
    try:
        with open(account_file, "r") as file:
            parts = file.read().strip().split("|", 2)
        if len(parts) != 3:
            raise ValueError("Invalid account file format.")
        saved_user, salt, digest = parts
    except OSError:
        saved_user = salt = digest = None
    except ValueError as error:
        print("Account file is invalid:", error)
        return False

    if saved_user is None:
        print("FIRST START — REGISTRATION")
        while True:
            username = input("Username: ").strip()
            allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-"
            if not username or any(char not in allowed for char in username):
                print("Username may contain letters, numbers, periods, hyphens, and underscores.")
                continue
            password = password_prompt("Password: ")
            confirmation = password_prompt("Confirm password: ")
            if len(password) < 4:
                print("Password must have at least 4 characters.")
                continue
            if password != confirmation:
                print("Passwords do not match. Try again.")
                continue
            salt = make_salt()
            digest = hash_password(password, salt)
            with open(account_file, "w") as file:
                file.write(username + "|" + salt + "|" + digest)
            print("Registration complete. Welcome,", username + "!")
            return True

    print("SIGN IN")
    for _ in range(3):
        username = input("Username: ").strip()
        password = password_prompt("Password: ")
        if username == saved_user and hash_password(password, salt) == digest:
            print("Sign-in successful. Welcome,", username + "!")
            return True
        print("Incorrect username or password.")
    print("Too many failed attempts.")
    return False

def bluetooth_status():
    try:
        import bluetooth
        return "Bluetooth LE is " + ("on." if bluetooth.BLE().active() else "off.")
    except Exception as error:
        return "Bluetooth LE is unavailable: " + str(error)

def bluetooth_scan(duration_ms=5000):
    try:
        import bluetooth
        ble = bluetooth.BLE()
        found = {}
        scan_result = getattr(bluetooth, "_IRQ_SCAN_RESULT", 5)
        def decode_name(payload):
            index = 0
            while index < len(payload):
                size = payload[index]
                if size == 0 or index + size >= len(payload):
                    break
                if payload[index + 1] in (0x08, 0x09):
                    try:
                        return payload[index + 2:index + size + 1].decode()
                    except Exception:
                        return "(name unavailable)"
                index += size + 1
            return "(unnamed)"
        def on_event(event, data):
            if event == scan_result:
                _, address, _, rssi, payload = data
                address_text = ":".join("%02X" % byte for byte in bytes(address))
                found[address_text] = (decode_name(bytes(payload)), rssi)
        ble.active(True)
        ble.irq(on_event)
        ble.gap_scan(duration_ms, active=True)
        started = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), started) < duration_ms + 500:
            time.sleep_ms(50)
        ble.gap_scan(None)
        ble.irq(None)
        return found, None
    except Exception as error:
        return None, str(error)

def package_command(arg):
    parts = arg.strip().split(" ", 1)
    action = parts[0].upper() if parts else "HELP"
    package = parts[1].strip() if len(parts) > 1 else ""
    if action == "HELP":
        print("PKG LIST | PKG INSTALL <package-name>")
        print("Installation requires Wi-Fi and confirmation, and downloads third-party Python code.")
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
        print(NAME, "is a firmware shell for the Pico 2 W / WH. It runs on MicroPython through USB serial.")
        print("The board has no built-in screen; Thonny or a terminal app provides the display.")
    elif name == "HARDWARE":
        print("Mode: PICO HARDWARE. LED, Wi-Fi, Bluetooth LE, and the RP2350 chip-temperature sensor use board hardware.")
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
        print(NAME, VERSION, "build", BUILD)
    elif name == "DATE":
        print(time.localtime())
    elif name == "UPTIME":
        try:
            print(time.ticks_ms() // 1000, "seconds")
        except Exception:
            print("The timer is unavailable.")
    elif name == "LED":
        if arg.lower() not in ("on", "off"):
            print("Usage: LED ON or LED OFF")
        else:
            try:
                from machine import Pin
                Pin("LED", Pin.OUT).value(1 if arg.lower() == "on" else 0)
                print("LED updated.")
            except Exception as error:
                print("LED is unavailable:", error)
    elif name == "WIFI" and arg.upper().split(" ", 1)[0] in ("SCAN", "CONNECT", "DISCONNECT", "STATUS", "IP"):
        wifi_parts = arg.split(" ", 1)
        action = wifi_parts[0].upper()
        wifi_name = wifi_parts[1].strip() if len(wifi_parts) > 1 else ""
        wlan = get_wifi()
        if action == "SCAN":
            if wlan is None:
                print("Wi-Fi library is unavailable.")
            else:
                try:
                    wlan.active(True)
                    for row in wlan.scan():
                        try:
                            ssid = row[0].decode()
                        except Exception:
                            ssid = str(row[0])
                        print("-", ssid, "RSSI", row[3], "dBm")
                except Exception as error:
                    print("Scan failed:", error)
        elif action == "CONNECT":
            ssid = wifi_name or input("Wi-Fi name (SSID): ").strip()
            if not ssid:
                print("A Wi-Fi name is required.")
            elif wlan is None:
                print("Wi-Fi is unavailable.")
            else:
                try:
                    password = password_prompt("Wi-Fi password (not saved): ")
                    wlan.active(True)
                    wlan.connect(ssid, password)
                    for _ in range(20):
                        if wlan.isconnected():
                            print("Connected. IP:", wlan.ifconfig()[0])
                            break
                        time.sleep(1)
                    else:
                        print("Connection failed.")
                except Exception as error:
                    print("Wi-Fi error:", error)
        elif action == "DISCONNECT":
            if wlan:
                wlan.disconnect()
                print("Wi-Fi disconnected.")
            else:
                print("Wi-Fi is unavailable.")
        elif wlan and wlan.isconnected():
            print("Connected. IP:", wlan.ifconfig()[0])
        else:
            print("Wi-Fi is not connected.")
    elif name in ("WIFI", "NETINFO", "IP"):
        print(wifi_status())
    elif name == "SCAN":
        return run("WIFI SCAN")
    elif name == "CONNECT":
        return run("WIFI CONNECT" + (" " + arg if arg else ""))
    elif name == "DISCONNECT":
        return run("WIFI DISCONNECT")
    elif name in ("BT", "BLUETOOTH"):
        action = arg.upper() or "STATUS"
        if action in ("STATUS", "INFO"):
            print(bluetooth_status())
        elif action == "SCAN":
            print("Scanning for Bluetooth LE devices for 5 seconds...")
            found, error = bluetooth_scan()
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
    elif name == "NOTE":
        note = arg or input("Note: ")
        if not note.strip():
            print("A note cannot be empty.")
        elif len(note) > 512:
            print("A note can be up to 512 characters to protect Pico flash space.")
        else:
            try:
                with open(NOTES, "a") as file:
                    file.write(note + "\n")
                print("Note saved.")
            except OSError as error:
                print("Could not save note:", error)
    elif name == "READ.NOTES":
        try:
            with open(NOTES, "r") as file:
                print(file.read())
        except OSError:
            print("There are no notes yet.")
    elif name == "CALC":
        try:
            print("=", calculate(arg or input("Example 2*(3+4): ")))
        except Exception as error:
            print("Expression error:", error)
    elif name in ("INSTRUMENTS", "INSTRUMENT_PANEL"):
        while True:
            print("=== INSTRUMENT PANEL ===")
            print("1 Chip temperature | 2 Uptime | 3 Wi-Fi | 4 LED | 5 BLE scan | 0 Back")
            choice = input("Instrument> ").strip()
            if choice == "1":
                temperature, error = chip_temperature_celsius()
                if error:
                    print("Chip temperature sensor is unavailable:", error)
                else:
                    print("RP2350 chip temperature:", round(temperature, 1), "°C (approximate; not room temperature)")
            elif choice == "2":
                print(time.ticks_ms() // 1000, "seconds")
            elif choice == "3":
                wlan = get_wifi()
                if wlan and wlan.isconnected():
                    print("Connected. IP:", wlan.ifconfig()[0])
                else:
                    print("Wi-Fi is not connected.")
            elif choice == "4":
                LED_STATE[0] = not LED_STATE[0]
                try:
                    from machine import Pin
                    Pin("LED", Pin.OUT).value(1 if LED_STATE[0] else 0)
                    print("LED is", "on." if LED_STATE[0] else "off.")
                except Exception as error:
                    print("LED is unavailable:", error)
            elif choice == "5":
                print("Scanning for BLE devices for 5 seconds...")
                found, error = bluetooth_scan()
                if error:
                    print("Bluetooth scan failed:", error)
                elif not found:
                    print("No BLE devices found.")
                else:
                    for address, details in found.items():
                        print("-", details[0], address, "RSSI", details[1], "dBm")
            elif choice == "0":
                break
            else:
                print("Choose 0, 1, 2, 3, 4, or 5.")
    elif name == "MATRIX":
        for _ in range(10):
            print("".join(random.choice("01ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(32)))
            time.sleep(0.08)
    elif name in ("REBOOT", "RESTART"):
        if input("Type REBOOT to restart the Pico: ").strip().upper() != "REBOOT":
            print("Restart cancelled.")
            return True
        try:
            import machine
            machine.reset()
        except Exception as error:
            print("Restart is unavailable:", error)
    elif name == "PING":
        print("ICMP ping is not implemented.")
    else:
        print("Unknown command. Type HELP.")
    return True

def main():
    global PREFERENCES
    PREFERENCES = load_preferences()
    show_banner()
    print("Mode: PICO HARDWARE | USB SERIAL CONSOLE")
    if not register_or_login():
        print("The terminal did not start.")
        return
    if PREFERENCES["startup"] == "dashboard":
        show_dashboard()
    elif PREFERENCES["startup"] == "menu":
        apps_menu()
    print("Type HELP to list commands.")
    while True:
        try:
            if not run(input("calc> ")):
                break
        except KeyboardInterrupt:
            print("\nInterrupted. Type HELP or EXIT.")
        except Exception as error:
            print("Command error:", error)

if __name__ == "__main__":
    main()
