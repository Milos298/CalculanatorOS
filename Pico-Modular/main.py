"""MicroPython automatically runs main.py when the board starts."""
import config
import commands
import account

def main():
    commands.show_banner()
    if not account.register_or_login():
        print("The terminal did not start.")
        return
    startup = commands.PREFERENCES["startup"]
    if startup == "dashboard":
        commands.show_dashboard()
    elif startup == "menu":
        commands.apps_menu()
    print("Type HELP to list commands.")
    while True:
        try:
            command = input("calc> ")
            if not commands.run(command):
                break
        except KeyboardInterrupt:
            print("\nInterrupted. Type HELP or EXIT.")
        except Exception as error:
            print("Command error:", error)

main()
