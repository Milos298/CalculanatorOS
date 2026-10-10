"""CalculanatorOS desktop prototype and Pico command simulator.

Run with Python on a PC. Hardware features are simulated unless marked PC.
The Pico firmware version is in Documents/CalculanatorOS/Pico-Modular.
"""
import datetime
import ast
import getpass
import hashlib
import hmac
import json
import os
import platform
import random
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import urllib.parse
import urllib.error
import webbrowser

VERSION = "0.6.5 BETA"
BUILD = "2026.10.10"
UPDATE_SOURCE_DEFAULT = "https://github.com/Milos298/desktop-tutorial/releases/latest/download/calculanatoros-update.json"
LED_STATE = False
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILES_DIR = os.path.join(BASE_DIR, "CalculanatorOS_Files")
ACCOUNT_FILE = os.path.join(BASE_DIR, "CalculanatorOS_users.json")
SETTINGS_FILE = os.path.join(BASE_DIR, "CalculanatorOS_settings.json")
NOTES_FILE = os.path.join(FILES_DIR, "notes.txt")
DOWNLOAD_DIR = os.path.join(FILES_DIR, "Downloads")
PBKDF2_ITERATIONS = 600000
LEGACY_PBKDF2_ITERATIONS = 120000
SETTINGS = {"username": "", "theme": "green", "startup": "shell", "update_source": UPDATE_SOURCE_DEFAULT}
CURRENT_USER = ""
CURRENT_COLOR = "07"
DEFAULT_COLOR = "07"
COLOR_ENABLED = False

CMD_FOREGROUND = (30, 34, 32, 36, 31, 35, 33, 37, 90, 94, 92, 96, 91, 95, 93, 97)
CMD_BACKGROUND = (40, 44, 42, 46, 41, 45, 43, 47, 100, 104, 102, 106, 101, 105, 103, 107)


def enable_terminal_colors():
    """Enable ANSI colors in an attached terminal, including modern Windows consoles."""
    if not getattr(sys.stdout, "isatty", lambda: False)():
        return False
    if os.name == "nt":
        try:
            import ctypes
            handle = ctypes.windll.kernel32.GetStdHandle(-11)
            mode = ctypes.c_uint()
            if not ctypes.windll.kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                return False
            if not (mode.value & 0x0004):
                if not ctypes.windll.kernel32.SetConsoleMode(handle, mode.value | 0x0004):
                    return False
        except Exception:
            return False
    return True


def ansi_color_sequence(code):
    if not isinstance(code, str) or not re.fullmatch(r"[0-9A-Fa-f]{2}", code):
        raise ValueError("Use two hexadecimal digits, for example 0A or 1F.")
    background, foreground = (int(char, 16) for char in code.upper())
    if background == foreground:
        raise ValueError("Background and text colors must be different.")
    return "\033[" + str(CMD_BACKGROUND[background]) + ";" + str(CMD_FOREGROUND[foreground]) + "m"


def set_console_color(code):
    global CURRENT_COLOR
    sequence = ansi_color_sequence(code)
    CURRENT_COLOR = code.upper()
    if not COLOR_ENABLED:
        return False
    sys.stdout.write(sequence)
    sys.stdout.flush()
    return True


def color_command(argument=""):
    global CURRENT_COLOR
    value = argument.strip().upper()
    if value in ("HELP", "/?", "-?"):
        print("Usage: COLOR [background+text]")
        print("Examples: COLOR 0A = black background, green text; COLOR 1F = blue background, bright white text.")
        print("Codes: 0 black, 1 blue, 2 green, 3 aqua, 4 red, 5 purple, 6 yellow, 7 light gray,")
        print("       8 dark gray, 9 bright blue, A bright green, B bright aqua, C bright red,")
        print("       D bright purple, E bright yellow, F white.")
        print("Current color:", CURRENT_COLOR)
        return
    code = value or DEFAULT_COLOR
    try:
        set_console_color(code)
    except ValueError as error:
        print("Invalid color:", error)
        return
    if COLOR_ENABLED:
        print("Console color set to", CURRENT_COLOR + ".")
    else:
        print("Color code saved for this session, but this terminal does not support interactive colors.")


def reset_console_colors():
    if COLOR_ENABLED:
        sys.stdout.write("\033[0m")
        sys.stdout.flush()


def password_hash(password, salt, iterations=PBKDF2_ITERATIONS):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations).hex()


def save_account(account, account_file):
    """Replace the account file atomically so a partial write cannot corrupt it."""
    account_dir = os.path.dirname(os.path.abspath(account_file))
    os.makedirs(account_dir, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=account_dir,
                                         prefix=".calculanator-account-", suffix=".tmp",
                                         delete=False) as file:
            temp_path = file.name
            json.dump(account, file)
            file.flush()
            os.fsync(file.fileno())
        if os.name != "nt":
            os.chmod(temp_path, 0o600)
        os.replace(temp_path, account_file)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def authenticate(account_file=ACCOUNT_FILE):
    global CURRENT_USER
    try:
        with open(account_file, "r", encoding="utf-8") as file:
            account = json.load(file)
    except FileNotFoundError:
        account = None
    except Exception as error:
        print("Could not load the account file:", error)
        return False

    if account is None:
        print("FIRST LAUNCH — REGISTRATION")
        print("Create your own local account for CalculanatorOS.")
        while True:
            username = input("Username: ").strip()
            if not re.fullmatch(r"[A-Za-z0-9_.-]{1,32}", username):
                print("Use 1–32 letters, numbers, dots, hyphens or underscores.")
                continue
            password = getpass.getpass("Password: ")
            confirmation = getpass.getpass("Confirm password: ")
            if len(password) < 8 or len(password) > 1024:
                print("Password must be 8–1024 characters long.")
                continue
            if password != confirmation:
                print("Passwords do not match. Try again.")
                continue
            salt = secrets.token_bytes(16)
            account = {
                "username": username,
                "salt": salt.hex(),
                "password_hash": password_hash(password, salt, PBKDF2_ITERATIONS),
                "iterations": PBKDF2_ITERATIONS,
            }
            try:
                save_account(account, account_file)
            except OSError as error:
                print("Could not save the account:", error)
                return False
            CURRENT_USER = username
            print("Registration complete. Welcome,", username + "!")
            return True

    print("SIGN IN")
    for _ in range(3):
        username = input("Username: ").strip()
        password = getpass.getpass("Password: ")
        try:
            if not isinstance(account, dict):
                raise ValueError("account data must be an object")
            stored_username = account["username"]
            if not isinstance(stored_username, str):
                raise ValueError("username must be text")
            salt = bytes.fromhex(account["salt"])
            stored_hash = account["password_hash"]
            if len(salt) != 16 or not isinstance(stored_hash, str) or len(stored_hash) != 64:
                raise ValueError("invalid password record")
            # Old accounts omit this field and were created with 120,000 rounds.
            iterations = account.get("iterations", LEGACY_PBKDF2_ITERATIONS)
            if iterations not in (LEGACY_PBKDF2_ITERATIONS, PBKDF2_ITERATIONS):
                raise ValueError("unsupported password hash version")
            expected = password_hash(password, salt, iterations)
            username_ok = hmac.compare_digest(username.casefold(), stored_username.casefold())
            password_ok = hmac.compare_digest(expected, stored_hash)
        except (KeyError, TypeError, ValueError) as error:
            print("The account file is invalid:", error)
            return False
        if username_ok and password_ok:
            # Upgrade old hashes after successful verification; never change the password.
            if iterations != PBKDF2_ITERATIONS:
                new_salt = secrets.token_bytes(16)
                upgraded = dict(account)
                upgraded.update({
                    "salt": new_salt.hex(),
                    "password_hash": password_hash(password, new_salt, PBKDF2_ITERATIONS),
                    "iterations": PBKDF2_ITERATIONS,
                })
                try:
                    save_account(upgraded, account_file)
                except OSError:
                    pass  # Keep the successful sign-in even if the upgrade cannot be saved.
            CURRENT_USER = stored_username
            print("Sign-in successful. Welcome,", stored_username + "!")
            return True
        print("Incorrect username or password.")
    print("Too many failed attempts.")
    return False


def change_password(account_file=ACCOUNT_FILE):
    """Change the local app password only after verifying the current password."""
    try:
        with open(account_file, "r", encoding="utf-8") as file:
            account = json.load(file)
        if not isinstance(account, dict):
            raise ValueError("invalid account record")
        salt = bytes.fromhex(account["salt"])
        stored_hash = account["password_hash"]
        iterations = account.get("iterations", LEGACY_PBKDF2_ITERATIONS)
        username = account["username"]
        if (len(salt) != 16 or not isinstance(stored_hash, str) or len(stored_hash) != 64
                or iterations not in (LEGACY_PBKDF2_ITERATIONS, PBKDF2_ITERATIONS)
                or not isinstance(username, str)):
            raise ValueError("invalid account record")
    except (OSError, ValueError, TypeError, KeyError):
        print("Could not read a valid account record.")
        return False
    if not hmac.compare_digest(CURRENT_USER.casefold(), username.casefold()):
        print("The signed-in username does not match the saved account.")
        return False
    current = getpass.getpass("Current password: ")
    expected = password_hash(current, salt, iterations)
    if not hmac.compare_digest(expected, stored_hash):
        print("Current password is incorrect.")
        return False
    new_password = getpass.getpass("New password (8–1024 characters): ")
    confirmation = getpass.getpass("Confirm new password: ")
    if len(new_password) < 8 or len(new_password) > 1024:
        print("Password must be 8–1024 characters long.")
        return False
    if new_password != confirmation:
        print("Passwords do not match.")
        return False
    new_salt = secrets.token_bytes(16)
    account.update({
        "salt": new_salt.hex(),
        "password_hash": password_hash(new_password, new_salt, PBKDF2_ITERATIONS),
        "iterations": PBKDF2_ITERATIONS,
    })
    try:
        save_account(account, account_file)
    except OSError as error:
        print("Could not save the new password:", error)
        return False
    print("Password updated.")
    return True


class CalculatorParser:
    """Evaluate + - * / and parentheses without executing Python code."""
    def __init__(self, expression):
        self.text = expression.replace(" ", "")
        self.pos = 0

    def peek(self):
        return self.text[self.pos] if self.pos < len(self.text) else ""

    def take(self):
        char = self.peek()
        if not char:
            raise ValueError("Expression is incomplete.")
        self.pos += 1
        return char

    def factor(self):
        if self.peek() == "+":
            self.take()
            return self.factor()
        if self.peek() == "-":
            self.take()
            return -self.factor()
        if self.peek() == "(":
            self.take()
            value = self.expression()
            if self.take() != ")":
                raise ValueError("Missing closing parenthesis.")
            return value
        start = self.pos
        dot_seen = False
        while self.pos < len(self.text):
            char = self.text[self.pos]
            if char.isdigit():
                self.pos += 1
            elif char == "." and not dot_seen:
                dot_seen = True
                self.pos += 1
            else:
                break
        if start == self.pos:
            raise ValueError("Expected a number.")
        return float(self.text[start:self.pos])

    def term(self):
        value = self.factor()
        while self.peek() in ("*", "/"):
            op = self.take()
            right = self.factor()
            if op == "/":
                if right == 0:
                    raise ValueError("Division by zero is not allowed.")
                value /= right
            else:
                value *= right
        return value

    def expression(self):
        value = self.term()
        while self.peek() in ("+", "-"):
            op = self.take()
            right = self.term()
            value = value + right if op == "+" else value - right
        return value

    def parse(self):
        result = self.expression()
        if self.pos != len(self.text):
            raise ValueError("Unexpected character: " + self.text[self.pos])
        return result


def calculate(expression):
    if not isinstance(expression, str) or not expression.strip():
        raise ValueError("Enter a mathematical expression.")
    if len(expression) > 256:
        raise ValueError("Expression is too long (maximum 256 characters).")
    return CalculatorParser(expression).parse()


def load_settings():
    """Load known preference fields only; ignore malformed or unknown data."""
    global SETTINGS
    settings = dict(SETTINGS)
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
            stored = json.load(file)
        if isinstance(stored, dict):
            if isinstance(stored.get("username"), str):
                settings["username"] = stored["username"][:32]
            if stored.get("theme") in ("green", "amber", "plain"):
                settings["theme"] = stored["theme"]
            if stored.get("startup") in ("shell", "menu"):
                settings["startup"] = stored["startup"]
            if isinstance(stored.get("update_source"), str):
                try:
                    settings["update_source"] = normalize_update_source(stored["update_source"])
                except ValueError:
                    print("Saved update source is invalid; updates are not configured.")
    except FileNotFoundError:
        pass
    except (OSError, ValueError, TypeError):
        print("Settings could not be read; using defaults.")
    SETTINGS = settings
    return SETTINGS


def save_settings():
    os.makedirs(BASE_DIR, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=BASE_DIR,
                                         prefix=".calculanator-settings-", suffix=".tmp",
                                         delete=False) as file:
            temp_path = file.name
            json.dump(SETTINGS, file, indent=2)
            file.flush()
            os.fsync(file.fileno())
        if os.name != "nt":
            os.chmod(temp_path, 0o600)
        os.replace(temp_path, SETTINGS_FILE)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def settings_command(argument=""):
    parts = argument.strip().split()
    if not parts:
        print("User:", SETTINGS.get("username") or "(not set)")
        print("Theme:", SETTINGS["theme"])
        print("Startup:", SETTINGS["startup"])
        print("Update source:", SETTINGS.get("update_source") or "(not configured)")
        print("Usage: SETTINGS | SETTINGS THEME <green|amber|plain> | SETTINGS STARTUP <shell|menu>")
        return
    if len(parts) != 2:
        print("Usage: SETTINGS THEME <green|amber|plain> or SETTINGS STARTUP <shell|menu>")
        return
    key, value = parts[0].lower(), parts[1].lower()
    if key == "theme" and value in ("green", "amber", "plain"):
        SETTINGS["theme"] = value
    elif key == "startup" and value in ("shell", "menu"):
        SETTINGS["startup"] = value
    else:
        print("Invalid setting. Use theme green/amber/plain or startup shell/menu.")
        return
    try:
        save_settings()
        suffix = " (applies after restart)" if key == "theme" else ""
        print(key.title(), "saved as", value + suffix + ".")
    except OSError as error:
        print("Could not save settings:", error)


def append_note(text):
    os.makedirs(FILES_DIR, exist_ok=True)
    with open(NOTES_FILE, "a", encoding="utf-8") as file:
        file.write(text + "\n")


def file_tree(directory=None, max_depth=8, max_entries=250):
    """Print a bounded tree of the OS sandbox without following links or reading files."""
    root = os.path.abspath(directory or FILES_DIR)
    allowed_root = os.path.abspath(FILES_DIR)
    if os.path.normcase(root) != os.path.normcase(allowed_root):
        raise ValueError("The file tree is limited to the CalculanatorOS_Files folder.")
    os.makedirs(root, exist_ok=True)
    print("CalculanatorOS_Files/")
    shown = 0

    def walk(current, prefix, depth):
        nonlocal shown
        if depth >= max_depth:
            return
        try:
            entries = sorted(os.scandir(current), key=lambda entry: entry.name.casefold())
        except OSError as error:
            print(prefix + "└── [cannot list folder: " + type(error).__name__ + "]")
            return
        for index, entry in enumerate(entries):
            if shown >= max_entries:
                print(prefix + "└── ... (tree limit reached)")
                return
            shown += 1
            last = index == len(entries) - 1
            branch = "└── " if last else "├── "
            try:
                if entry.is_symlink():
                    print(prefix + branch + entry.name + " [link not followed]")
                elif entry.is_dir(follow_symlinks=False):
                    print(prefix + branch + entry.name + "/")
                    walk(entry.path, prefix + ("    " if last else "│   "), depth + 1)
                else:
                    print(prefix + branch + entry.name)
            except OSError:
                print(prefix + branch + entry.name + " [unavailable]")

    walk(root, "", 0)


def files_app():
    file_tree()


def save_source_file(filename, source):
    """Validate and atomically save one top-level Python file beside the desktop OS."""
    if not re.fullmatch(r"[A-Za-z0-9_.-]+\.py", filename) or filename in (".py", "..py"):
        raise ValueError("Choose a simple .py file name from the CalculanatorOS folder.")
    root = os.path.realpath(BASE_DIR)
    target = os.path.abspath(os.path.join(root, filename))
    if os.path.islink(target) or os.path.normcase(os.path.dirname(target)) != os.path.normcase(root):
        raise ValueError("The editor can only write regular .py files in the CalculanatorOS folder.")
    if not os.path.isfile(target):
        raise FileNotFoundError("The selected Python source file no longer exists.")
    compile(source, target, "exec")
    backup_dir = os.path.join(FILES_DIR, "Backups")
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup_path = os.path.join(backup_dir, filename + "." + timestamp + ".bak")
    shutil.copy2(target, backup_path)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n",
                                         dir=root, prefix=".calculanator-edit-",
                                         suffix=".tmp", delete=False) as file:
            temp_path = file.name
            file.write(source)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_path, target)
        temp_path = None
        return backup_path
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def edit_os_app():
    print("CalculanatorOS Python Editor")
    print("Edits apply after restarting CalculanatorOS. The editor makes a backup before saving.")
    try:
        files = sorted(
            name for name in os.listdir(BASE_DIR)
            if name.lower().endswith(".py")
            and os.path.isfile(os.path.join(BASE_DIR, name))
            and not os.path.islink(os.path.join(BASE_DIR, name))
        )
    except OSError as error:
        print("Could not list Python source files:", error)
        return
    if not files:
        print("No editable Python files were found beside CalculanatorOS.")
        return
    print("Python files:", " | ".join(str(index) + ": " + name for index, name in enumerate(files, 1)))
    selection = input("File number or name [CalculanatorOS.py]: ").strip() or "CalculanatorOS.py"
    if selection.isdigit() and 1 <= int(selection) <= len(files):
        filename = files[int(selection) - 1]
    elif selection in files:
        filename = selection
    else:
        print("Choose one of the listed Python files.")
        return
    path = os.path.join(BASE_DIR, filename)
    try:
        with open(path, "r", encoding="utf-8") as file:
            lines = file.read().splitlines()
    except (OSError, UnicodeError) as error:
        print("Could not open source file:", error)
        return
    dirty = False
    print("Type EDITOR HELP for editor commands.")
    while True:
        try:
            raw = input("EDITOS> ")
        except (EOFError, KeyboardInterrupt):
            print("Editor closed.")
            return
        parts = raw.strip().split(maxsplit=1)
        action = parts[0].upper() if parts else ""
        argument = parts[1] if len(parts) > 1 else ""
        if action == "EDITOR" and argument.upper() == "HELP":
            print("SHOW [line] | EDIT <line> | INSERT <line> | DELETE <line> | SAVE | QUIT")
            print("SHOW displays up to 20 lines. INSERT adds a new line before the given line number.")
        elif action in ("SHOW", "LIST"):
            try:
                start = int(argument) if argument else 1
                if start < 1:
                    raise ValueError
            except ValueError:
                print("Usage: SHOW [line_number]")
                continue
            if not lines:
                print("(empty file)")
            for index in range(start - 1, min(start + 19, len(lines))):
                print(f"{index + 1:04d} | {lines[index]}")
            if start + 19 < len(lines):
                print("More lines remain. Use SHOW", start + 20)
        elif action in ("EDIT", "INSERT", "DELETE"):
            try:
                number = int(argument)
                if action == "INSERT":
                    if number < 1 or number > len(lines) + 1:
                        raise ValueError
                elif number < 1 or number > len(lines):
                    raise ValueError
            except ValueError:
                maximum = len(lines) + 1 if action == "INSERT" else len(lines)
                print(action, "line number must be from 1 to", maximum)
                continue
            if action == "DELETE":
                removed = lines.pop(number - 1)
                print("Deleted line", str(number) + ":", removed)
            else:
                new_line = input("New line text: ")
                if action == "EDIT":
                    lines[number - 1] = new_line
                else:
                    lines.insert(number - 1, new_line)
                print(action.title(), "line", number, "in the editor buffer.")
            dirty = True
        elif action == "SAVE":
            if input("Type WRITE to validate, back up, and save " + filename + ": ").strip() != "WRITE":
                print("Save cancelled.")
                continue
            source = "\n".join(lines) + ("\n" if lines else "")
            try:
                backup = save_source_file(filename, source)
                dirty = False
                print("Saved successfully. Backup:", backup)
                print("Restart CalculanatorOS to run the updated code.")
            except (OSError, ValueError, SyntaxError) as error:
                print("Save failed. The original source was kept.")
                if isinstance(error, SyntaxError):
                    print("Python syntax error on line", error.lineno, ":", error.msg)
                else:
                    print(type(error).__name__ + ":", error)
        elif action == "QUIT":
            if dirty and input("Unsaved edits will be lost. Type DISCARD to quit: ").strip() != "DISCARD":
                print("Still in the editor.")
                continue
            return
        elif not action:
            continue
        else:
            print("Unknown editor command. Type EDITOR HELP.")


def notes_app():
    print("Notes app — type /back to return to the shell.")
    while True:
        text = input("Note> ").strip()
        if text.lower() == "/back":
            return
        if text:
            append_note(text)
            print("Saved to", NOTES_FILE)


def settings_app():
    print("Settings app")
    print("Current theme:", SETTINGS["theme"], "| Startup:", SETTINGS["startup"])
    print("Use SETTINGS THEME <green|amber|plain> or SETTINGS STARTUP <shell|menu>.")


UNIT_GROUPS = {
    "length": {"mm": 0.001, "cm": 0.01, "m": 1.0, "km": 1000.0,
               "in": 0.0254, "ft": 0.3048, "mi": 1609.344},
    "mass": {"mg": 0.000001, "g": 0.001, "kg": 1.0,
             "oz": 0.028349523125, "lb": 0.45359237},
    "storage": {"b": 1, "kib": 1024, "mib": 1024**2, "gib": 1024**3},
}
TEMPERATURE_UNITS = {"c", "f", "k"}
PASSWORD_CHARSETS = (
    "abcdefghijklmnopqrstuvwxyz",
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "0123456789",
    "!@#$%^&*()-_=+[]{}?",
)


def convert_units(value, source_unit, target_unit):
    """Convert supported length, mass, storage, and temperature units."""
    amount = float(value)
    source = source_unit.strip().lower()
    target = target_unit.strip().lower()
    if source in TEMPERATURE_UNITS and target in TEMPERATURE_UNITS:
        celsius = amount if source == "c" else (amount - 32) * 5 / 9 if source == "f" else amount - 273.15
        if celsius < -273.15:
            raise ValueError("Temperature is below absolute zero.")
        if target == "c":
            return celsius
        if target == "f":
            return celsius * 9 / 5 + 32
        return celsius + 273.15
    for units in UNIT_GROUPS.values():
        if source in units and target in units:
            return amount * units[source] / units[target]
    raise ValueError("Choose units from the same supported category.")


def unit_converter_app():
    print("Unit Converter — length, mass, storage, or temperature.")
    print("Units: mm cm m km in ft mi | mg g kg oz lb | B KiB MiB GiB | C F K")
    while True:
        try:
            amount = float(input("Value> ").strip())
            source = input("From unit> ").strip()
            target = input("To unit> ").strip()
            result = convert_units(amount, source, target)
            print("=", format(result, ".10g"), target)
        except ValueError as error:
            print("Conversion error:", error)
        if input("Convert another value? [y/N] ").strip().lower() != "y":
            return


def generate_password(length=20):
    """Generate a password with a cryptographically secure random source."""
    if not isinstance(length, int) or not 12 <= length <= 64:
        raise ValueError("Password length must be between 12 and 64 characters.")
    chars = [secrets.choice(charset) for charset in PASSWORD_CHARSETS]
    alphabet = "".join(PASSWORD_CHARSETS)
    chars.extend(secrets.choice(alphabet) for _ in range(length - len(chars)))
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)


def password_generator_app():
    raw_length = input("Password length [20, range 12–64]: ").strip()
    try:
        length = int(raw_length) if raw_length else 20
        password = generate_password(length)
    except ValueError as error:
        print("Password generator error:", error)
        return
    print("Generated password (not saved):")
    print(password)
    print("Copy it to a password manager, then clear the terminal if needed.")


def system_dashboard_app():
    print("=== SYSTEM DASHBOARD (READ ONLY) ===")
    print("Operating system:", platform.platform())
    print("Python:", platform.python_version())
    print("Architecture:", platform.machine() or "unknown")
    print("Logical CPU cores:", os.cpu_count() or "unknown")
    print("CalculanatorOS session:", round(time.monotonic() - BOOT_TIME, 1), "seconds")
    print("Signed-in user:", SETTINGS.get("username") or "unknown")
    print("Theme / startup:", SETTINGS["theme"], "/", SETTINGS["startup"])
    try:
        disk = shutil.disk_usage(BASE_DIR)
        print("Disk free:", round(disk.free / (1024 ** 3), 2), "GiB of",
              round(disk.total / (1024 ** 3), 2), "GiB")
    except OSError as error:
        print("Disk information unavailable:", error)
    print("Hardware mode: PC simulation")


BOOT_TIME = time.monotonic()


APP_REGISTRY = {}


def register_app(name, description, callback):
    """Register a shell app; add a new entry here to extend the app menu."""
    key = name.strip().lower()
    if not re.fullmatch(r"[a-z][a-z0-9_-]{0,23}", key) or not callable(callback):
        raise ValueError("App names must be simple identifiers and callbacks must be callable.")
    APP_REGISTRY[key] = (description, callback)


def apps_menu():
    while True:
        print("\n=== CALCULANATOROS APPS ===")
        for number, (name, (description, _)) in enumerate(APP_REGISTRY.items(), 1):
            print(str(number) + ".", name.title(), "—", description)
        print("0. Back")
        choice = input("Apps> ").strip()
        if choice == "0":
            return
        if choice.isdigit() and 1 <= int(choice) <= len(APP_REGISTRY):
            name = list(APP_REGISTRY)[int(choice) - 1]
            APP_REGISTRY[name][1]()
        elif choice.lower() in APP_REGISTRY:
            APP_REGISTRY[choice.lower()][1]()
        else:
            print("Choose an app number, app name, or 0.")


def launch_app(name):
    app = APP_REGISTRY.get(name.strip().lower())
    if app is None:
        print("Unknown app. Type APPS to see installed apps.")
        return
    app[1]()


def download_file():
    url = input("HTTPS URL: ").strip()
    try:
        parsed = urllib.parse.urlparse(url)
    except ValueError:
        print("Invalid URL.")
        return
    if parsed.scheme.lower() != "https" or not parsed.hostname or parsed.username or parsed.password:
        print("Downloads require a valid HTTPS URL without embedded credentials.")
        return
    suggested = os.path.basename(urllib.parse.unquote(parsed.path)) or "downloaded_file"
    filename = input("Save as [" + suggested + "]: ").strip() or suggested
    filename = os.path.basename(filename.replace("\\", "/").strip())
    if filename in ("", ".", "..") or any(ord(char) < 32 for char in filename):
        print("Invalid file name.")
        return
    destination = os.path.join(DOWNLOAD_DIR, filename)
    print("Download destination:", destination)
    if os.path.exists(destination) and input("File exists. Type OVERWRITE to replace it: ").strip() != "OVERWRITE":
        print("Download cancelled.")
        return
    if input("Type DOWNLOAD to confirm: ").strip() != "DOWNLOAD":
        print("Download cancelled.")
        return
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    temp_path = None
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "CalculanatorOS/0.6"})
        with urllib.request.urlopen(request, timeout=15) as response:
            final_url = urllib.parse.urlparse(response.geturl())
            if final_url.scheme.lower() != "https":
                raise ValueError("redirected download did not use HTTPS")
            length = response.headers.get("Content-Length")
            if length and int(length) > 10 * 1024 * 1024:
                print("Download rejected: the file is larger than 10 MB.")
                return
            with tempfile.NamedTemporaryFile("wb", dir=DOWNLOAD_DIR,
                                             prefix=".download-", suffix=".part", delete=False) as out:
                temp_path = out.name
                total = 0
                while True:
                    chunk = response.read(65536)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > 10 * 1024 * 1024:
                        raise ValueError("file is larger than 10 MB")
                    out.write(chunk)
                out.flush()
                os.fsync(out.fileno())
        os.replace(temp_path, destination)
        temp_path = None
        print("Download complete:", destination)
        print("The file was saved but was not opened or executed.")
        try:
            append_note("Downloaded URL: " + url)
            print("The URL was added to", NOTES_FILE)
        except OSError:
            print("The file downloaded, but the URL could not be added to notes.")
    except (OSError, ValueError, urllib.error.URLError) as error:
        reason = getattr(error, "code", None) or type(error).__name__
        print("Download failed:", reason)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


MAX_UPDATE_MANIFEST_BYTES = 64 * 1024
MAX_UPDATE_SCRIPT_BYTES = 2 * 1024 * 1024
UPDATE_MANIFEST_NAME = "calculanatoros-update.json"


def normalize_update_source(value):
    """Validate an HTTPS release manifest URL or convert a GitHub repo URL to one."""
    value = value.strip() if isinstance(value, str) else ""
    if not value:
        return ""
    try:
        parsed = urllib.parse.urlsplit(value)
    except ValueError as error:
        raise ValueError("Enter a valid HTTPS URL.") from error
    if (parsed.scheme.lower() != "https" or not parsed.hostname
            or parsed.username or parsed.password or parsed.query or parsed.fragment):
        raise ValueError("Update sources must be HTTPS URLs without credentials, query, or fragment.")
    path = parsed.path.rstrip("/")
    if parsed.hostname.lower() == "github.com":
        pieces = [part for part in path.split("/") if part]
        if len(pieces) == 2:
            owner, repository = pieces
            if not re.fullmatch(r"[A-Za-z0-9_.-]+", owner) or not re.fullmatch(r"[A-Za-z0-9_.-]+", repository):
                raise ValueError("GitHub owner and repository names contain unsupported characters.")
            if repository.endswith(".git"):
                repository = repository[:-4]
            return "https://github.com/{}/{}/releases/latest/download/{}".format(
                owner, repository, UPDATE_MANIFEST_NAME
            )
        if len(pieces) == 4 and pieces[2:4] == ["releases", "latest"]:
            return "https://github.com/{}/{}/releases/latest/download/{}".format(
                pieces[0], pieces[1], UPDATE_MANIFEST_NAME
            )
    return value


def _read_https_url(url, limit, description):
    try:
        parsed = urllib.parse.urlsplit(url)
    except ValueError as error:
        raise ValueError(description + " URL is invalid.") from error
    if parsed.scheme.lower() != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError(description + " must use HTTPS and must not contain embedded credentials.")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "CalculanatorOS-Updater/" + VERSION, "Accept": "application/json, text/plain, */*"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        final_url = urllib.parse.urlsplit(response.geturl())
        if final_url.scheme.lower() != "https" or not final_url.hostname:
            raise ValueError(description + " redirected to a non-HTTPS address.")
        content_length = response.headers.get("Content-Length")
        if content_length:
            try:
                if int(content_length) > limit:
                    raise ValueError(description + " is larger than the allowed size limit.")
            except ValueError as error:
                if "larger than" in str(error):
                    raise
        payload = response.read(limit + 1)
    if len(payload) > limit:
        raise ValueError(description + " is larger than the allowed size limit.")
    return payload


def fetch_update_manifest(source=None):
    source = source or SETTINGS.get("update_source", "")
    if not source:
        raise ValueError("Updates are not configured. Use UPDATE SOURCE <GitHub repository URL> first.")
    payload = _read_https_url(source, MAX_UPDATE_MANIFEST_BYTES, "Update manifest")
    try:
        release = json.loads(payload.decode("utf-8"))
    except (UnicodeError, ValueError) as error:
        raise ValueError("The update manifest is not valid UTF-8 JSON.") from error
    if not isinstance(release, dict):
        raise ValueError("The update manifest must contain a JSON object.")
    if release.get("platform", "desktop") != "desktop":
        raise ValueError("This release is not for the desktop edition.")
    version = release.get("version")
    build = release.get("build")
    url = release.get("url")
    checksum = release.get("sha256")
    if not isinstance(version, str) or not isinstance(build, str):
        raise ValueError("The update manifest must include text fields 'version' and 'build'.")
    _version_key(version)
    if not build or len(build) > 40 or not re.fullmatch(r"[A-Za-z0-9._-]+", build):
        raise ValueError("The update manifest has an invalid build identifier.")
    if not isinstance(url, str):
        raise ValueError("The update manifest must include the script URL in 'url'.")
    try:
        parsed_url = urllib.parse.urlsplit(url)
    except ValueError as error:
        raise ValueError("The update script URL is invalid.") from error
    if parsed_url.scheme.lower() != "https" or not parsed_url.hostname or parsed_url.username or parsed_url.password:
        raise ValueError("The update script URL must use HTTPS and contain no embedded credentials.")
    if not isinstance(checksum, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", checksum):
        raise ValueError("The update manifest must include a 64-digit SHA-256 checksum.")
    size = release.get("size")
    if size is not None and (not isinstance(size, int) or isinstance(size, bool)
                             or size < 1 or size > MAX_UPDATE_SCRIPT_BYTES):
        raise ValueError("The update manifest has an invalid script size.")
    return {
        "version": version,
        "build": build,
        "url": url,
        "sha256": checksum.lower(),
        "size": size,
    }


def _version_key(value):
    match = re.fullmatch(r"(\d+(?:\.\d+){1,3})(?:[- ]?([A-Za-z][A-Za-z0-9.-]*))?", value.strip())
    if not match:
        raise ValueError("Version must look like 1.2.3 or 1.2.3 BETA.")
    numbers = tuple(int(part) for part in match.group(1).split("."))
    numbers += (0,) * (4 - len(numbers))
    suffix = match.group(2)
    return numbers, (1, "") if not suffix else (0, suffix.casefold())


def _build_key(value):
    parts = re.findall(r"\d+", value)
    return tuple(int(part) for part in parts)


def update_is_newer(release):
    candidate = _version_key(release["version"])
    current = _version_key(VERSION)
    if candidate != current:
        return candidate > current
    candidate_build = _build_key(release["build"])
    current_build = _build_key(BUILD)
    return bool(candidate_build and current_build and candidate_build > current_build)


def source_version_and_build(source):
    """Read only literal VERSION and BUILD values from a candidate Python file."""
    tree = ast.parse(source, filename="CalculanatorOS.py", mode="exec")
    values = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names = [node.target.id]
        else:
            continue
        for name in names:
            if name in ("VERSION", "BUILD"):
                try:
                    values[name] = ast.literal_eval(node.value)
                except (ValueError, TypeError):
                    raise ValueError("The candidate script must define literal VERSION and BUILD values.")
    if not isinstance(values.get("VERSION"), str) or not isinstance(values.get("BUILD"), str):
        raise ValueError("The candidate script is missing its VERSION or BUILD value.")
    return values["VERSION"], values["BUILD"]


def download_verified_update(release):
    payload = _read_https_url(release["url"], MAX_UPDATE_SCRIPT_BYTES, "Update script")
    if release["size"] is not None and len(payload) != release["size"]:
        raise ValueError("The downloaded script size does not match the release manifest.")
    if not hmac.compare_digest(hashlib.sha256(payload).hexdigest(), release["sha256"]):
        raise ValueError("The downloaded script failed its SHA-256 check; it was not installed.")
    try:
        source = payload.decode("utf-8-sig")
        compile(source, "CalculanatorOS.py", "exec")
    except (UnicodeError, SyntaxError) as error:
        raise ValueError("The downloaded file is not valid Python source.") from error
    candidate_version, candidate_build = source_version_and_build(source)
    if candidate_version != release["version"] or candidate_build != release["build"]:
        raise ValueError("The script's VERSION or BUILD does not match the release manifest.")
    return payload


def install_verified_update(release, payload, target_path=None):
    target = os.path.abspath(target_path or __file__)
    root = os.path.realpath(os.path.dirname(target))
    if (os.path.islink(target) or not os.path.isfile(target)
            or os.path.normcase(os.path.realpath(os.path.dirname(target))) != os.path.normcase(root)):
        raise ValueError("The current OS script must be a regular file before it can be updated.")
    backup_dir = os.path.join(FILES_DIR, "Backups")
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup_path = os.path.join(backup_dir, os.path.basename(target) + "." + timestamp + ".bak")
    shutil.copy2(target, backup_path)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile("wb", dir=root, prefix=".calculanator-update-",
                                         suffix=".tmp", delete=False) as file:
            temp_path = file.name
            file.write(payload)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_path, target)
        temp_path = None
        return backup_path
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def update_command(argument=""):
    parts = argument.strip().split(maxsplit=1)
    action = parts[0].upper() if parts else "INSTALL"
    if action == "SOURCE":
        if len(parts) != 2:
            print("Usage: UPDATE SOURCE <GitHub repository URL or HTTPS manifest URL>")
            print("Current source:", SETTINGS.get("update_source") or "(not configured)")
            return
        try:
            source = normalize_update_source(parts[1])
            previous = SETTINGS.get("update_source", "")
            SETTINGS["update_source"] = source
            save_settings()
            print("Update source saved:", source)
            print("This preference can sync through a shared settings folder such as OneDrive.")
        except (OSError, ValueError) as error:
            SETTINGS["update_source"] = locals().get("previous", SETTINGS.get("update_source", ""))
            print("Could not save update source:", error)
        return
    if action not in ("INSTALL", "CHECK"):
        print("Usage: UPDATE [CHECK|INSTALL] or UPDATE SOURCE <URL>")
        return
    try:
        release = fetch_update_manifest()
        if not update_is_newer(release):
            print("CalculanatorOS is up to date ({} / {}).".format(VERSION, BUILD))
            return
        print("Update available: {} / {} (current: {} / {}).".format(
            release["version"], release["build"], VERSION, BUILD
        ))
        if action == "CHECK":
            print("Run UPDATE or UPDATE INSTALL to install it.")
            return
        if input("Type INSTALL to download, verify, and install this update: ").strip() != "INSTALL":
            print("Update cancelled.")
            return
        payload = download_verified_update(release)
        backup = install_verified_update(release, payload)
        print("Update installed. Backup:", backup)
        print("Restart CalculanatorOS to run version", release["version"] + ".")
    except urllib.error.HTTPError as error:
        if error.code == 404:
            print("Update source returned 404. Make sure the GitHub repository is public and its latest release includes the update manifest.")
        else:
            print("Update failed: HTTP", error.code)
    except (OSError, ValueError, SyntaxError, urllib.error.URLError, json.JSONDecodeError) as error:
        reason = getattr(error, "code", None) or str(error) or type(error).__name__
        print("Update failed:", reason)


def start_url(value):
    value = value.strip()
    if not value:
        value = input("Website or URL: ").strip()
    if not value:
        print("No website was entered.")
        return
    if "://" not in value:
        value = "https://" + value
    try:
        parsed = urllib.parse.urlparse(value)
    except ValueError:
        print("Invalid website URL.")
        return
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        print("Only valid HTTP or HTTPS website URLs can be opened.")
        return
    try:
        if webbrowser.open(value):
            print("Opened in the default browser:", value)
        else:
            print("Could not open a browser. URL:", value)
    except Exception as error:
        print("Could not open the website:", type(error).__name__)


def calculator_mode(expression=""):
    single_use = bool(expression)
    while True:
        if not expression:
            expression = input("Expression (for example 2*(3+4), q = quit): ").strip()
        if expression.lower() in ("q", "quit", "exit"):
            return
        try:
            print("=", calculate(expression))
        except Exception as error:
            print("Expression error:", error)
        if single_use:
            return
        expression = ""


def simulated_thermometer():
    value = round(18 + random.random() * 10, 1)
    print("SIMULATED temperature:", value, "°C (random demo value on PC)")


def simulated_wifi_signal():
    value = random.randint(25, 100)
    print("SIMULATED Wi-Fi signal:", value, "% (random demo value on PC)")


def stopwatch():
    input("Press Enter to start the stopwatch.")
    start = time.monotonic()
    try:
        input("Timing... press Enter to stop.")
    except KeyboardInterrupt:
        print("Stopwatch interrupted.")
        return
    print("Elapsed:", round(time.monotonic() - start, 2), "seconds")


def instruments():
    while True:
        print("\n=== INSTRUMENT PANEL — PC SIMULATION ===")
        print("1 Temperature (simulated) | 2 Wi-Fi signal (simulated) | 3 Stopwatch | 4 LED | 5 Bluetooth | 0 Back")
        choice = input("Instrument> ").strip()
        if choice == "1":
            simulated_thermometer()
        elif choice == "2":
            simulated_wifi_signal()
        elif choice == "3":
            stopwatch()
        elif choice == "4":
            instrument_command("LED ON" if not LED_STATE else "LED OFF")
        elif choice == "5":
            bluetooth_command("BT STATUS")
        elif choice == "0":
            return
        else:
            print("Choose 0, 1, 2, 3, 4, or 5.")


def wifi_command(command):
    """PC adapter: use Windows netsh; Pico firmware has its own Wi-Fi driver."""
    if os.name != "nt":
        print("This Wi-Fi test command uses Windows. Pico firmware has its own Wi-Fi driver.")
        return
    original_command = command.strip()
    command = original_command.upper()
    if command == "WIFI" or command == "WIFI PROFILES":
        subprocess.run(["netsh", "wlan", "show", "profiles"], check=False)
    elif command in ("WIFI STATUS", "NETINFO WIFI"):
        subprocess.run(["netsh", "wlan", "show", "interfaces"], check=False)
    elif command in ("SCAN", "WIFI SCAN"):
        subprocess.run(["netsh", "wlan", "show", "networks"], check=False)
    elif command in ("CONNECT", "WIFI CONNECT") or command.startswith("WIFI CONNECT "):
        wifi = original_command[len("WIFI CONNECT "):].strip() if command.startswith("WIFI CONNECT ") else ""
        wifi = wifi or input("Saved Wi-Fi profile name (SSID): ").strip()
        if wifi:
            subprocess.run(["netsh", "wlan", "connect", f'name="{wifi}"'], check=False)
    elif command in ("DISCONNECT", "WIFI DISCONNECT"):
        subprocess.run(["netsh", "wlan", "disconnect"], check=False)


def bluetooth_command(command):
    command = command.upper()
    if command in ("BLUETOOTH", "BT", "BT STATUS"):
        if os.name != "nt":
            print("Check the Bluetooth adapter status in your system settings.")
            return
        subprocess.run([
            "powershell", "-NoProfile", "-Command",
            "Get-PnpDevice -Class Bluetooth | Select-Object Status,FriendlyName | Format-Table -AutoSize"
        ], check=False)
    elif command in ("BT SCAN", "BLUETOOTH SCAN"):
        try:
            import asyncio
            from bleak import BleakScanner
            devices = asyncio.run(BleakScanner.discover(timeout=5))
            if not devices:
                print("No BLE devices found.")
            for device in devices:
                print("-", device.name or "(unnamed)", device.address,
                      "RSSI", getattr(device, "rssi", "?"), "dBm")
        except ImportError:
            print("BLE scan on PC requires Bleak. Install it with: py -m pip install bleak")
        except Exception as error:
            print("Bluetooth scan failed:", error)


def package_command(command):
    parts = command.strip().split(" ", 2)
    action = parts[1].upper() if len(parts) > 1 else "HELP"
    package = parts[2].strip() if len(parts) > 2 else ""
    if action == "HELP":
        print("PKG LIST | PKG INSTALL <package_name>")
        print("Installation uses mpremote and a connected Pico with Wi-Fi.")
    elif action == "LIST":
        if not shutil.which("mpremote"):
            print("To list Pico files, install mpremote: py -m pip install mpremote")
        else:
            try:
                result = subprocess.run(["mpremote", "fs", "ls", ":"], check=False, timeout=30)
                if result.returncode == 0:
                    print("Pico file list completed.")
                else:
                    print("Could not list Pico files. mpremote exit code:", result.returncode)
            except (OSError, subprocess.TimeoutExpired) as error:
                print("Could not list Pico files:", type(error).__name__)
    elif action == "INSTALL":
        if not re.fullmatch(r"[A-Za-z0-9._-]+", package):
            print("Usage: PKG INSTALL package_name")
            return
        if input("Install third-party package '" + package + "'? Type INSTALL to confirm: ").strip() != "INSTALL":
            print("Installation cancelled.")
            return
        if not shutil.which("mpremote"):
            print("Install mpremote on the PC: py -m pip install mpremote")
            return
        print("Pico must be connected over USB and to Wi-Fi.")
        try:
            result = subprocess.run(["mpremote", "mip", "install", package], check=False, timeout=120)
            if result.returncode == 0:
                print("Package installation completed:", package)
            else:
                print("Package installation failed with exit code", result.returncode,
                      "Check the Pico connection, Wi-Fi, and package name.")
        except subprocess.TimeoutExpired:
            print("Package installation timed out after 120 seconds.")
        except OSError as error:
            print("Could not start mpremote:", error)
    else:
        print("Unknown action. Use PKG HELP.")


def instrument_command(command):
    global LED_STATE
    if command in ("INSTRUMENTS", "INSTRUMENT_PANEL"):
        instruments()
    elif command == "LED ON":
        LED_STATE = True
        print("SIMULATED LED is on (PC mode).")
    elif command == "LED OFF":
        LED_STATE = False
        print("SIMULATED LED is off (PC mode).")
    elif command == "LED":
        print("SIMULATED LED is", "on." if LED_STATE else "off.")


register_app("calculator", "Evaluate arithmetic expressions.", calculator_mode)
register_app("notes", "Create and view local notes.", notes_app)
register_app("settings", "View and change system preferences.", settings_app)
register_app("instruments", "Open the PC hardware simulation panel.", instruments)
register_app("converter", "Convert length, mass, storage, and temperature units.", unit_converter_app)
register_app("dashboard", "View read-only PC and CalculanatorOS status.", system_dashboard_app)
register_app("password-generator", "Create a random password; it is not saved.", password_generator_app)
register_app("stopwatch", "Measure elapsed time.", stopwatch)
register_app("files", "View the safe file tree for the OS sandbox.", files_app)
register_app("editor", "Edit Python source with syntax checks and automatic backups.", edit_os_app)


HELP_COMMANDS = (
    "HELP | HELP_BOOK | APPS | APP <name> | MENU | EDITOS | SETTINGS [THEME|STARTUP] | COLOR [code] | HARDWARE | "
    "INFO | MORE INFO | ABOUT | CREATOR | VER | VERSION | DATE | UPTIME | CLEAR | "
    "CALC [expression] | INSTRUMENTS | INSTRUMENT_PANEL | LED [ON|OFF] | WIFI | WIFI PROFILES | "
    "WIFI STATUS | WIFI SCAN | WIFI CONNECT [SSID] | WIFI DISCONNECT | BLUETOOTH | BT STATUS | BT SCAN | "
    "PKG HELP | PKG LIST | PKG INSTALL <name> | UPDATE [CHECK|INSTALL] | UPDATE SOURCE <URL> | "
    "PING | NETINFO | IP | NOTE [text] | READ.NOTES | "
    "MATRIX | FILE TREE | TREE | DOWNLOAD | CAL.APT INSTALL | START <website> | PASSWD | SECURITY | EXIT | QUIT"
)
HELP_BOOK = (
    "HELP — show the short list of available commands.",
    "HELP_BOOK — show this detailed command guide.",
    "APPS or MENU — open the app launcher. Add apps with register_app(name, description, callback).",
    "APP <name> — launch an app by name, for example APP calculator.",
    "EDITOS — open the built-in Python editor for files beside the desktop OS; syntax checks and backups are automatic.",
    "SETTINGS — show the saved username, theme, and startup preference.",
    "SETTINGS THEME <green|amber|plain> — save the terminal accent preference.",
    "SETTINGS STARTUP <shell|menu> — choose the first screen at startup.",
    "COLOR [code] — change terminal colors like Windows CMD, for example COLOR 0A; COLOR alone restores startup colors.",
    "HARDWARE — explain whether this PC build is simulating or accessing hardware.",
    "INFO, MORE INFO, ABOUT, CREATOR — show project and build information.",
    "VER or VERSION — show the CalculanatorOS version.",
    "DATE — show the computer's date and time.",
    "UPTIME — show how long this desktop test session has been running.",
    "CLEAR — clear the terminal window.",
    "CALC [expression] — safely calculate +, -, *, / and parentheses (maximum 256 characters).",
    "INSTRUMENTS or INSTRUMENT_PANEL — open the PC simulation panel.",
    "LED [ON|OFF] — view or change the simulated PC LED state.",
    "WIFI or WIFI PROFILES — list saved Windows Wi-Fi profile names.",
    "WIFI STATUS — show the Windows Wi-Fi adapter status.",
    "WIFI SCAN — list nearby Wi-Fi networks.",
    "WIFI CONNECT [SSID] — connect Windows to a saved profile.",
    "WIFI DISCONNECT — disconnect the Windows Wi-Fi adapter.",
    "BLUETOOTH or BT STATUS — show Bluetooth adapters on Windows.",
    "BT SCAN — scan for Bluetooth Low Energy devices; PC requires Bleak.",
    "PKG HELP — show package command help.",
    "PKG LIST — list files on a connected Pico using mpremote.",
    "PKG INSTALL <name> — after confirmation, install a third-party MicroPython package on Pico.",
    "UPDATE or UPDATE INSTALL — check the configured GitHub release manifest and, after confirmation, verify and install the desktop update.",
    "UPDATE CHECK — check for a newer desktop version without installing it.",
    "UPDATE SOURCE <GitHub repository URL> — save the HTTPS release source; releases must include calculanatoros-update.json and CalculanatorOS.py assets.",
    "PING — send one ping to a host entered by the user.",
    "NETINFO or IP — show Windows network configuration.",
    "NOTE [text] — append a note to CalculanatorOS_Files/notes.txt.",
    "READ.NOTES — read notes from CalculanatorOS_Files/notes.txt.",
    "MATRIX — show a short text animation.",
    "FILE TREE or TREE — show folder and file names inside CalculanatorOS_Files; links are not followed.",
    "DOWNLOAD or CAL.APT INSTALL — confirm and download one HTTPS file (maximum 10 MB) into the Downloads folder.",
    "START <website> — open an HTTP or HTTPS website in the default browser.",
    "SECURITY — show a summary of local account and download safeguards.",
    "PASSWD — change the app password after verifying the current password.",
    "EXIT or QUIT — close CalculanatorOS.",
    "PC hardware note — LED, temperature, and Wi-Fi signal in this menu are simulated; Pico firmware controls real hardware.",
)


def main():
    global CURRENT_USER, COLOR_ENABLED, DEFAULT_COLOR
    session_started = time.monotonic()
    load_settings()
    DEFAULT_COLOR = {"green": "0A", "amber": "0E", "plain": "07"}.get(SETTINGS["theme"], "07")
    COLOR_ENABLED = enable_terminal_colors()
    set_console_color(DEFAULT_COLOR)
    print("+==================================================+")
    print("|                 CALCULANATOROS                  |")
    print("|          PICO 2 W / DESKTOP EDITION             |")
    print("+==================================================+")
    print("VERSION =", VERSION, "| BUILD =", BUILD)
    if not authenticate():
        print("The terminal did not start.")
        reset_console_colors()
        return
    SETTINGS["username"] = CURRENT_USER
    try:
        save_settings()
    except OSError:
        print("Could not save the username preference; sign-in still succeeded.")
    print("PC MODE: hardware features are simulated. Type HARDWARE or HELP.")
    if SETTINGS["startup"] == "menu":
        apps_menu()

    while True:
        try:
            raw = input("calc> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        if not raw:
            continue
        cmd = raw.upper()
        if cmd in ("EXIT", "QUIT"):
            print("Goodbye!")
            break
        elif cmd == "HELP":
            print(HELP_COMMANDS)
        elif cmd == "HELP_BOOK":
            print("=== CALCULANATOROS HELP BOOK ===")
            for number, entry in enumerate(HELP_BOOK, 1):
                print(f"{number:02d} | {entry}")
        elif cmd in ("APPS", "MENU"):
            apps_menu()
        elif cmd.startswith("APP "):
            launch_app(raw[4:])
        elif cmd == "APP":
            print("Usage: APP <name>")
        elif cmd == "EDITOS":
            edit_os_app()
        elif cmd == "SETTINGS":
            settings_command()
        elif cmd.startswith("SETTINGS "):
            settings_command(raw[9:])
        elif cmd == "UPDATE" or cmd.startswith("UPDATE "):
            update_command(raw[7:] if len(raw) > 6 else "")
        elif cmd == "COLOR":
            color_command()
        elif cmd.startswith("COLOR "):
            color_command(raw[6:])
        elif cmd == "HARDWARE":
            print("Mode: PC SIMULATION. No GPIO or sensor hardware is accessed by this desktop build.")
            print("On Pico 2 W, the separate MicroPython firmware uses its real onboard LED and RP2350 chip-temperature sensor.")
        elif cmd == "INFO":
            print("CalculanatorOS is an experimental desktop test shell and Pico 2 W MicroPython firmware project.")
        elif cmd == "MORE INFO":
            print("Desktop testing and Pico firmware are separate builds.")
            print("Build:", BUILD)
        elif cmd == "ABOUT":
            print("Created in Calculanator Labs")
        elif cmd == "CREATOR":
            print("Created by a young developer from Czechia.")
        elif cmd in ("VER", "VERSION"):
            print("CalculanatorOS", VERSION)
        elif cmd == "DATE":
            print(datetime.datetime.now())
        elif cmd == "UPTIME":
            print("Desktop test uptime:", round(time.monotonic() - session_started, 1), "seconds")
        elif cmd == "CLEAR":
            os.system("cls" if os.name == "nt" else "clear")
        elif cmd == "CALC":
            calculator_mode()
        elif cmd.startswith("CALC "):
            calculator_mode(raw[5:].strip())
        elif cmd in ("INSTRUMENTS", "INSTRUMENT_PANEL"):
            instruments()
        elif cmd.startswith("LED"):
            instrument_command(cmd)
        elif cmd in ("WIFI", "SCAN", "CONNECT", "DISCONNECT") or cmd.startswith("WIFI "):
            wifi_command(raw)
        elif cmd in ("BLUETOOTH", "BT", "BT STATUS", "BT SCAN", "BLUETOOTH SCAN"):
            bluetooth_command(cmd)
        elif cmd == "PKG" or cmd.startswith("PKG "):
            package_command(raw)
        elif cmd == "PING":
            host = input("Host or IP address: ").strip()
            if host and re.fullmatch(r"[A-Za-z0-9_.:-]{1,253}", host):
                try:
                    result = subprocess.run(["ping", "-n", "1", host], check=False, timeout=10)
                    print("Ping exit code:", result.returncode)
                except (OSError, subprocess.TimeoutExpired) as error:
                    print("Ping failed:", type(error).__name__)
            else:
                print("Enter a valid host name or IP address.")
        elif cmd == "IP" or cmd == "NETINFO":
            if os.name == "nt":
                result = subprocess.run(["ipconfig"], check=False, timeout=15)
                if result.returncode:
                    print("Network information command failed with exit code", result.returncode)
            else:
                print("Network information is available through the host operating system.")
        elif cmd == "NOTE" or cmd.startswith("NOTE "):
            note = raw[4:].strip() if len(raw) > 4 else input("Note: ")
            if note:
                try:
                    append_note(note)
                    print("Saved to", NOTES_FILE)
                except OSError as error:
                    print("Could not save note:", error)
        elif cmd == "READ.NOTES":
            try:
                with open(NOTES_FILE, "r", encoding="utf-8") as file:
                    notes = file.read()
                print(notes or "There are no notes yet.")
            except FileNotFoundError:
                print("There are no notes yet.")
            except OSError as error:
                print("Could not read notes:", error)
        elif cmd == "MATRIX":
            print("Entering Matrix Mode...")
            for _ in range(20):
                print("".join(random.choice("01ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(80)))
                time.sleep(0.05)
        elif cmd in ("FILE TREE", "TREE"):
            file_tree()
        elif cmd == "FILE":
            print("Usage: FILE TREE")
        elif cmd in ("DOWNLOAD", "CAL.APT INSTALL"):
            download_file()
        elif cmd == "START" or cmd.startswith("START "):
            start_url(raw[5:] if len(raw) > 5 else "")
        elif cmd == "SECURITY":
            print("Local sign-in uses salted PBKDF2-HMAC-SHA256 password hashes.")
            print("Downloads require HTTPS, are limited to 10 MB, and are never executed automatically.")
            print("Notes and downloads are stored in the CalculanatorOS_Files folder. Do not store secrets in notes.")
            print("This app password does not protect your Windows account or files.")
        elif cmd == "PASSWD":
            change_password()
        else:
            print("Unknown command. Type HELP.")
    reset_console_colors()


if __name__ == "__main__":
    main()
