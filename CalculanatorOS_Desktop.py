"""Responsive graphical desktop for the CalculanatorOS PC edition."""
import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLI_PATH = os.path.join(BASE_DIR, "CalculanatorOS.py")
SETTINGS_PATH = os.path.join(BASE_DIR, "CalculanatorOS_settings.json")
NOTES_PATH = os.path.join(BASE_DIR, "CalculanatorOS_Files", "notes.txt")
PALETTES = {
    "green": {"top": "#071713", "bottom": "#102b25", "accent": "#52e0a1", "panel": "#10241f"},
    "amber": {"top": "#191208", "bottom": "#392714", "accent": "#ffc36b", "panel": "#2b2115"},
    "plain": {"top": "#101622", "bottom": "#243044", "accent": "#dce7f5", "panel": "#1a2535"},
    "ocean": {"top": "#061525", "bottom": "#123d59", "accent": "#6ad5ff", "panel": "#10263a"},
    "violet": {"top": "#120c25", "bottom": "#342052", "accent": "#c7a0ff", "panel": "#211933"},
}


def load_settings():
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def save_settings(settings):
    os.makedirs(BASE_DIR, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=BASE_DIR,
                                         prefix=".calculanator-desktop-", suffix=".tmp",
                                         delete=False) as file:
            temporary = file.name
            json.dump(settings, file, indent=2)
            file.flush()
            os.fsync(file.fileno())
        if os.name != "nt":
            os.chmod(temporary, 0o600)
        os.replace(temporary, SETTINGS_PATH)
        temporary = None
    finally:
        if temporary and os.path.exists(temporary):
            os.remove(temporary)


class Desktop:
    def __init__(self, root):
        self.root = root
        self.settings = load_settings()
        self.theme = self.settings.get("theme", "green")
        if self.theme not in PALETTES:
            self.theme = "green"
        self.palette = PALETTES[self.theme]
        self.fullscreen = True
        self.background_photo = None
        self.resize_job = None
        self.font_family = "Segoe UI" if os.name == "nt" else "DejaVu Sans"

        root.title("CalculanatorOS Desktop")
        root.configure(bg=self.palette["top"])
        root.attributes("-fullscreen", True)
        root.bind("<Escape>", self.toggle_fullscreen)
        root.bind("<F11>", self.toggle_fullscreen)
        root.bind("<Configure>", self.schedule_draw)
        root.protocol("WM_DELETE_WINDOW", self.close_desktop)
        self.canvas = tk.Canvas(root, highlightthickness=0, bd=0, bg=self.palette["top"])
        self.canvas.pack(fill="both", expand=True)
        self.draw()

    def schedule_draw(self, _event=None):
        if self.resize_job is not None:
            self.root.after_cancel(self.resize_job)
        self.resize_job = self.root.after(80, self.draw)

    def _fit_font(self, width, height):
        return max(0.72, min(1.28, min(width / 1440, height / 900)))

    @staticmethod
    def _mix_color(start, end, amount):
        a = tuple(int(start[i:i + 2], 16) for i in (1, 3, 5))
        b = tuple(int(end[i:i + 2], 16) for i in (1, 3, 5))
        values = tuple(round(a[i] + (b[i] - a[i]) * amount) for i in range(3))
        return "#%02x%02x%02x" % values

    def _draw_default_background(self, width, height):
        steps = min(96, max(36, height // 9))
        top, bottom = self.palette["top"], self.palette["bottom"]
        for step in range(steps):
            color = self._mix_color(top, bottom, step / max(steps - 1, 1))
            y0 = int(height * step / steps)
            y1 = int(height * (step + 1) / steps) + 1
            self.canvas.create_rectangle(0, y0, width, y1, fill=color, outline="")
        glow = self.palette["accent"]
        self.canvas.create_oval(width * 0.60, -height * 0.70, width * 1.16, height * 0.28,
                                fill=self.palette["bottom"], outline="")
        self.canvas.create_oval(-width * 0.35, height * 0.62, width * 0.42, height * 1.45,
                                fill=self.palette["top"], outline="")
        self.canvas.create_oval(width * 0.75, height * 0.66, width * 0.77, height * 0.68,
                                fill=glow, outline="")

    def _draw_wallpaper(self, width, height):
        path = self.settings.get("wallpaper", "")
        if not path or not os.path.isfile(path):
            return False
        try:
            from PIL import Image, ImageOps, ImageTk
            with Image.open(path) as original:
                if original.width * original.height > 40_000_000:
                    return False
                image = ImageOps.fit(original.convert("RGB"), (width, height),
                                     method=Image.Resampling.LANCZOS)
            self.background_photo = ImageTk.PhotoImage(image)
            self.canvas.create_image(0, 0, image=self.background_photo, anchor="nw")
            self.canvas.create_rectangle(0, 0, width, height, fill="#07111d", stipple="gray50", outline="")
            return True
        except ImportError:
            try:
                self.background_photo = tk.PhotoImage(file=path)
                self.canvas.create_image(width // 2, height // 2, image=self.background_photo)
                self.canvas.create_rectangle(0, 0, width, height, fill="#07111d", stipple="gray50", outline="")
                return True
            except Exception:
                return False
        except Exception:
            return False

    def draw(self):
        self.resize_job = None
        self.palette = PALETTES.get(self.theme, PALETTES["green"])
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        if width < 100:
            width = self.root.winfo_width()
        if height < 100:
            height = self.root.winfo_height()
        if width < 100 or height < 100:
            width, height = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        scale = self._fit_font(width, height)
        self.canvas.delete("all")
        if not self._draw_wallpaper(width, height):
            self._draw_default_background(width, height)

        self.canvas.create_rectangle(0, 0, width, 74 * scale, fill="#07111d", stipple="gray25", outline="")
        self.canvas.create_text(36 * scale, 36 * scale, anchor="w", text="CALCULANATOROS",
                                fill="#f4f7fb", font=(self.font_family, int(16 * scale), "bold"))
        self.canvas.create_text(226 * scale, 38 * scale, anchor="w", text="DESKTOP  /  PC EDITION",
                                fill="#a7b5c7", font=(self.font_family, int(9 * scale), "bold"))
        display_size = f"{self.root.winfo_screenwidth()} × {self.root.winfo_screenheight()}"
        self.canvas.create_text(width - 78 * scale, 38 * scale, anchor="e",
                                text=display_size + "   •   " + datetime.datetime.now().strftime("%H:%M"),
                                fill="#d9e3ef", font=(self.font_family, int(10 * scale)))
        self.canvas.create_text(width - 28 * scale, 38 * scale, text="⏻", fill=self.palette["accent"],
                                font=(self.font_family, int(17 * scale), "bold"), tags=("power-menu",))
        self.canvas.tag_bind("power-menu", "<Button-1>", lambda _event: self.open_power_menu())
        self.canvas.tag_bind("power-menu", "<Enter>", lambda _event: self.canvas.itemconfigure("power-menu", fill="#ffffff"))
        self.canvas.tag_bind("power-menu", "<Leave>", lambda _event: self.canvas.itemconfigure("power-menu", fill=self.palette["accent"]))

        username = self.settings.get("username") or "Explorer"
        self.canvas.create_text(width / 2, height * 0.225, text="Good to see you, " + username,
                                fill="#f7f9fc", font=(self.font_family, int(30 * scale), "bold"))
        self.canvas.create_text(width / 2, height * 0.285,
                                text="A calm place to calculate, create, and explore.",
                                fill="#c4cfdd", font=(self.font_family, int(12 * scale)))

        columns = 4 if width >= 1500 else 3 if width >= 600 else 2
        gap = 18 * scale
        card_width = min(250 * scale, (width - 64 * scale - gap * (columns - 1)) / columns)
        entries = [
            ("terminal", "01", "Terminal", "Open the CalculanatorOS command shell."),
            ("calculator", "02", "Calculator", "Solve expressions with a clean keypad."),
            ("notes", "03", "Notes", "Keep notes in your local OS folder."),
            ("settings", "04", "Personalize", "Choose a theme, wallpaper, and screen mode."),
            ("files", "05", "Files", "Browse the CalculanatorOS files folder."),
        ]
        rows = (len(entries) + columns - 1) // columns
        card_height = min(154 * scale,
                          max(80 * scale, (height * 0.56 - gap * (rows - 1)) / rows))
        total_width = columns * card_width + (columns - 1) * gap
        x_start = (width - total_width) / 2
        grid_height = rows * card_height + (rows - 1) * gap
        y_start = max(height * 0.37, height * 0.5 - grid_height / 2)
        for index, (key, number, title, description) in enumerate(entries):
            row, column = divmod(index, columns)
            x = x_start + column * (card_width + gap)
            y = y_start + row * (card_height + gap)
            tag = "app-" + key
            panel = self.palette["panel"]
            self.canvas.create_rectangle(x, y, x + card_width, y + card_height,
                                         fill=panel, outline="#35506a", width=max(1, int(scale)),
                                         tags=(tag, tag + "-background"))
            self.canvas.create_text(x + 25 * scale, y + 25 * scale, anchor="nw", text=number,
                                    fill=self.palette["accent"], font=(self.font_family, int(10 * scale), "bold"), tags=(tag,))
            self.canvas.create_text(x + 25 * scale, y + 69 * scale, anchor="w", text=title,
                                    fill="#f7f9fc", font=(self.font_family, int(17 * scale), "bold"), tags=(tag,))
            self.canvas.create_text(x + 25 * scale, y + 106 * scale, anchor="nw", width=card_width - 48 * scale,
                                    text=description, fill="#b6c3d2", font=(self.font_family, int(9 * scale)), tags=(tag,))
            self.canvas.create_text(x + card_width - 25 * scale, y + card_height - 24 * scale, anchor="e",
                                    text="OPEN  →", fill=self.palette["accent"],
                                    font=(self.font_family, int(8 * scale), "bold"), tags=(tag,))
            self.canvas.tag_bind(tag, "<Button-1>", lambda _event, name=key: self.open_app(name))
            self.canvas.tag_bind(tag, "<Enter>", lambda _event, name=key: self.hover(name, True))
            self.canvas.tag_bind(tag, "<Leave>", lambda _event, name=key: self.hover(name, False))

        footer_y = height - 60 * scale
        self.canvas.create_text(34 * scale, footer_y, anchor="w", text="ESC / F11  ·  toggle full screen",
                                fill="#d2dbe6", font=(self.font_family, int(9 * scale)))
        self.canvas.create_text(width / 2, footer_y, text="VIRTUALBOX  ·  Right Ctrl releases the host key",
                                fill="#b2c0d0", font=(self.font_family, int(9 * scale)))
        self.canvas.create_text(width - 34 * scale, footer_y, anchor="e",
                                text="DISPLAY  " + display_size,
                                fill=self.palette["accent"], font=(self.font_family, int(9 * scale), "bold"))

        self.canvas.create_text(36 * scale, height - 25 * scale, anchor="w",
                                text="DEBIAN LIVE  ·  Hardware access is simulated in PC mode",
                                fill="#92a1b3", font=(self.font_family, int(8 * scale)))
        self.canvas.create_text(width - 36 * scale, height - 25 * scale, anchor="e",
                                text="ALT+F4  ·  return to command shell",
                                fill="#92a1b3", font=(self.font_family, int(8 * scale)))

    def hover(self, name, active):
        color = "#213b50" if active else self.palette["panel"]
        self.canvas.itemconfigure("app-" + name + "-background", fill=color)

    def open_app(self, name):
        actions = {
            "terminal": self.open_terminal,
            "calculator": self.open_calculator,
            "notes": self.open_notes,
            "settings": self.open_settings,
            "files": self.open_files,
        }
        actions[name]()

    def open_files(self):
        folder = os.path.join(BASE_DIR, "CalculanatorOS_Files")
        os.makedirs(folder, exist_ok=True)
        try:
            if os.name == "nt":
                os.startfile(folder)
                return
            manager = shutil.which("pcmanfm") or shutil.which("xdg-open")
            if not manager:
                messagebox.showinfo("Files", "No graphical file manager is installed. Use FILE TREE in Terminal.", parent=self.root)
                return
            subprocess.Popen([manager, folder], start_new_session=True)
        except OSError as error:
            messagebox.showerror("Files", "Could not open the files folder:\n" + str(error), parent=self.root)

    def open_terminal(self):
        if os.name == "nt":
            flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
            try:
                env = os.environ.copy()
                env["CALCULANATOROS_FROM_DESKTOP"] = "1"
                subprocess.Popen([sys.executable, CLI_PATH], cwd=BASE_DIR, creationflags=flags, env=env)
            except OSError as error:
                messagebox.showerror("Terminal", "Could not open the OS shell:\n" + str(error), parent=self.root)
            return
        terminal = shutil.which("xterm") or shutil.which("x-terminal-emulator")
        if not terminal:
            messagebox.showinfo("Terminal", "No terminal window app is installed. Use the current text console.", parent=self.root)
            return
        width, height = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        columns = max(40, min(170, (width - 48) // 9))
        rows = max(12, min(55, (height - 110) // 18))
        command = [terminal, "-geometry", f"{columns}x{rows}+24+70", "-fa", "DejaVu Sans Mono",
                   "-fs", "11", "-bg", "#07121d", "-fg", self.palette["accent"],
                   "-T", "CalculanatorOS Terminal", "-e", sys.executable, CLI_PATH]
        try:
            env = os.environ.copy()
            env["CALCULANATOROS_FROM_DESKTOP"] = "1"
            subprocess.Popen(command, cwd=BASE_DIR, start_new_session=True, env=env)
        except OSError as error:
            messagebox.showerror("Terminal", "Could not open a terminal window:\n" + str(error), parent=self.root)

    def _load_cli_calculator(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("calculanator_cli", CLI_PATH)
        if spec is None or spec.loader is None:
            raise RuntimeError("The CalculanatorOS command file could not be loaded.")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.calculate

    def open_calculator(self):
        window = self.make_window("Calculator", 440, 300)
        tk.Label(window, text="CALCULATOR", bg="#101a28", fg=self.palette["accent"],
                 font=(self.font_family, 11, "bold")).pack(anchor="w", padx=22, pady=(20, 8))
        expression = tk.StringVar()
        entry = tk.Entry(window, textvariable=expression, bg="#0a111b", fg="#f6f8fb",
                         insertbackground="#f6f8fb", relief="flat", font=(self.font_family, 18))
        entry.pack(fill="x", padx=22, ipady=12)
        result = tk.Label(window, text="Enter an expression such as 2*(3+4)", bg="#101a28",
                          fg="#c0ccda", font=(self.font_family, 11))
        result.pack(anchor="w", padx=22, pady=16)

        def calculate(_event=None):
            try:
                result.configure(text="= " + str(self._load_cli_calculator()(expression.get())))
            except Exception as error:
                result.configure(text="Check the expression: " + str(error))
            return "break"

        self.button(window, "CALCULATE", calculate, accent=True).pack(anchor="e", padx=22, pady=10)
        entry.bind("<Return>", calculate)
        entry.focus_set()

    def open_notes(self):
        window = self.make_window("Notes", 720, 520)
        tk.Label(window, text="YOUR NOTES", bg="#101a28", fg=self.palette["accent"],
                 font=(self.font_family, 11, "bold")).pack(anchor="w", padx=20, pady=(18, 8))
        text = tk.Text(window, bg="#0a111b", fg="#edf2f8", insertbackground="#edf2f8",
                       relief="flat", wrap="word", font=(self.font_family, 11), padx=12, pady=12)
        text.pack(fill="both", expand=True, padx=20, pady=8)
        try:
            with open(NOTES_PATH, "r", encoding="utf-8") as file:
                text.insert("1.0", file.read())
        except FileNotFoundError:
            pass
        except OSError as error:
            messagebox.showwarning("Notes", "Could not read notes:\n" + str(error), parent=window)

        def save_notes():
            os.makedirs(os.path.dirname(NOTES_PATH), exist_ok=True)
            try:
                with open(NOTES_PATH, "w", encoding="utf-8") as file:
                    file.write(text.get("1.0", "end-1c"))
                messagebox.showinfo("Notes", "Notes saved in CalculanatorOS_Files.", parent=window)
            except OSError as error:
                messagebox.showerror("Notes", "Could not save notes:\n" + str(error), parent=window)

        self.button(window, "SAVE NOTES", save_notes, accent=True).pack(anchor="e", padx=20, pady=(4, 16))

    def open_settings(self):
        window = self.make_window("Desktop settings", 560, 440)
        tk.Label(window, text="MAKE IT YOURS", bg="#101a28", fg=self.palette["accent"],
                 font=(self.font_family, 11, "bold")).pack(anchor="w", padx=22, pady=(20, 12))
        tk.Label(window, text=f"Detected screen: {self.root.winfo_screenwidth()} × {self.root.winfo_screenheight()}",
                 bg="#101a28", fg="#dce5ef", font=(self.font_family, 10)).pack(anchor="w", padx=22, pady=4)
        tk.Label(window, text="The desktop and terminal window size adapt to this display.",
                 bg="#101a28", fg="#9eacbd", font=(self.font_family, 9)).pack(anchor="w", padx=22, pady=(0, 18))

        theme_var = tk.StringVar(value=self.theme)
        tk.Label(window, text="COLOR THEME", bg="#101a28", fg="#dce5ef",
                 font=(self.font_family, 9, "bold")).pack(anchor="w", padx=22, pady=(2, 6))
        theme_row = tk.Frame(window, bg="#101a28")
        theme_row.pack(fill="x", padx=22)
        for theme in PALETTES:
            self.button(theme_row, theme.title(), lambda chosen=theme: self.set_theme(chosen, theme_var),
                        accent=(theme == self.theme)).pack(side="left", padx=(0, 8))

        tk.Label(window, text="WALLPAPER IMAGE", bg="#101a28", fg="#dce5ef",
                 font=(self.font_family, 9, "bold")).pack(anchor="w", padx=22, pady=(22, 6))
        wallpaper_label = tk.Label(window, text=self._wallpaper_label(), bg="#101a28", fg="#9eacbd",
                                   font=(self.font_family, 9), anchor="w")
        wallpaper_label.pack(fill="x", padx=22, pady=(0, 10))

        def choose_wallpaper():
            path = filedialog.askopenfilename(parent=window, title="Choose a desktop wallpaper",
                                              filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                                                         ("All files", "*.*")])
            if not path:
                return
            try:
                if os.path.getsize(path) > 32 * 1024 * 1024:
                    raise ValueError("Choose an image smaller than 32 MB.")
                try:
                    from PIL import Image
                    with Image.open(path) as image:
                        if image.width * image.height > 40_000_000:
                            raise ValueError("The image dimensions are too large for a wallpaper.")
                        image.verify()
                except ImportError:
                    if os.path.splitext(path)[1].lower() not in (".png", ".gif"):
                        raise ValueError("This Python install needs Pillow for JPG, BMP, or WEBP wallpapers. Use PNG or GIF here.")
                    preview = tk.PhotoImage(file=path)
                    del preview
                self.settings["wallpaper"] = os.path.abspath(path)
                save_settings(self.settings)
                wallpaper_label.configure(text=self._wallpaper_label())
                self.draw()
            except Exception as error:
                messagebox.showerror("Wallpaper", str(error), parent=window)

        def reset_wallpaper():
            self.settings["wallpaper"] = ""
            try:
                save_settings(self.settings)
                wallpaper_label.configure(text="CalculanatorOS default wallpaper")
                self.draw()
            except OSError as error:
                messagebox.showerror("Wallpaper", "Could not save settings:\n" + str(error), parent=window)

        row = tk.Frame(window, bg="#101a28")
        row.pack(fill="x", padx=22)
        self.button(row, "CHOOSE IMAGE", choose_wallpaper, accent=True).pack(side="left", padx=(0, 8))
        self.button(row, "RESET", reset_wallpaper).pack(side="left")
        tk.Label(window, text="Supported: PNG, JPG, GIF, BMP, WEBP. Press Esc or F11 to leave full screen.",
                 bg="#101a28", fg="#9eacbd", font=(self.font_family, 8)).pack(anchor="w", padx=22, pady=(20, 12))

    def open_power_menu(self):
        window = self.make_window("Power", 360, 255)
        tk.Label(window, text="POWER OPTIONS", bg="#101a28", fg=self.palette["accent"],
                 font=(self.font_family, 11, "bold")).pack(anchor="w", padx=22, pady=(20, 14))
        self.button(window, "SHUT DOWN", lambda: self.power_action("SHUTDOWN"), accent=True).pack(
            fill="x", padx=22, pady=5)
        self.button(window, "RESTART", lambda: self.power_action("REBOOT")).pack(fill="x", padx=22, pady=5)
        self.button(window, "RETURN TO SHELL", self.close_desktop).pack(fill="x", padx=22, pady=5)

    def power_action(self, action):
        label = "shut down" if action == "SHUTDOWN" else "restart"
        if not messagebox.askyesno("Confirm power action", f"Do you want to {label} this computer?", parent=self.root):
            return
        if os.name == "nt":
            command = [shutil.which("shutdown.exe") or "shutdown.exe",
                       "/s" if action == "SHUTDOWN" else "/r", "/t", "0"]
        else:
            sudo = shutil.which("sudo")
            if not sudo:
                messagebox.showerror("Power action", "sudo is not installed. Use the command shell.", parent=self.root)
                return
            command = [sudo, "-n", "systemctl", "poweroff" if action == "SHUTDOWN" else "reboot"]
        try:
            result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=20)
            if result.returncode:
                messagebox.showinfo("Power action", "The system needs administrator confirmation. Open Terminal and use CALC SUDO " + action + ".", parent=self.root)
        except (OSError, subprocess.TimeoutExpired) as error:
            messagebox.showerror("Power action", "Could not start the power action:\n" + str(error), parent=self.root)

    def _wallpaper_label(self):
        path = self.settings.get("wallpaper") or ""
        return os.path.basename(path) if path else "CalculanatorOS default wallpaper"

    def set_theme(self, theme, variable=None):
        self.theme = theme
        self.settings["theme"] = theme
        self.palette = PALETTES[theme]
        try:
            save_settings(self.settings)
        except OSError as error:
            messagebox.showerror("Settings", "Could not save the theme:\n" + str(error), parent=self.root)
            return
        if variable is not None:
            variable.set(theme)
        self.root.configure(bg=self.palette["top"])
        self.draw()

    def make_window(self, title, width, height):
        window = tk.Toplevel(self.root)
        window.title("CalculanatorOS — " + title)
        window.configure(bg="#101a28")
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width = max(320, min(width, int(screen_width * 0.90)))
        height = max(240, min(height, int(screen_height * 0.88)))
        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")
        window.transient(self.root)
        window.lift()
        return window

    def button(self, parent, text, command, accent=False):
        background = self.palette["accent"] if accent else "#1b293a"
        foreground = "#07111d" if accent else "#e8eef6"
        return tk.Button(parent, text=text, command=command, bg=background, fg=foreground,
                         activebackground="#31516a", activeforeground="#ffffff", relief="flat",
                         bd=0, padx=14, pady=9, cursor="hand2", font=(self.font_family, 9, "bold"))

    def toggle_fullscreen(self, _event=None):
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)
        if not self.fullscreen:
            width, height = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
            self.root.geometry(f"{int(width * 0.88)}x{int(height * 0.84)}+40+40")
        self.schedule_draw()
        return "break"

    def close_desktop(self):
        if messagebox.askyesno("Close desktop", "Close the desktop and return to the command shell?", parent=self.root):
            self.root.destroy()


def main():
    root = tk.Tk()
    Desktop(root)
    root.mainloop()


if __name__ == "__main__":
    main()
