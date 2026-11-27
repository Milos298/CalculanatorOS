"""Small persistent user preferences for the Pico flash filesystem."""

SETTINGS_FILE = "calculanator_settings.txt"
THEMES = ("green", "amber", "ocean", "plain")
STARTUP_MODES = ("dashboard", "menu", "shell")
DEFAULTS = {"theme": "ocean", "startup": "dashboard"}


def load():
    values = dict(DEFAULTS)
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


def save(values):
    theme = values.get("theme", DEFAULTS["theme"])
    startup = values.get("startup", DEFAULTS["startup"])
    if theme not in THEMES or startup not in STARTUP_MODES:
        raise ValueError("Unsupported theme or startup mode.")
    with open(SETTINGS_FILE, "w") as file:
        file.write("theme=" + theme + "\n")
        file.write("startup=" + startup + "\n")
