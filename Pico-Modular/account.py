"""Simple single-user registration and login for the Pico flash filesystem."""
import hashlib
import os
import random

ACCOUNT_FILE = "calculanator_user.txt"

def _password_prompt(label):
    try:
        import getpass
        return getpass.getpass(label)
    except Exception:
        # Most MicroPython USB REPLs echo input, so the password may be visible.
        return input(label)

def _hash_password(password, salt):
    value = (salt + password).encode()
    for _ in range(1024):
        value = hashlib.sha256(value).digest()
    return "".join("%02x" % byte for byte in value)

def _make_salt():
    try:
        raw = os.urandom(16)
        return "".join("%02x" % byte for byte in raw)
    except Exception:
        return "%08x%08x%08x%08x" % tuple(random.getrandbits(32) for _ in range(4))

def _read_account():
    try:
        with open(ACCOUNT_FILE, "r") as file:
            parts = file.read().strip().split("|", 2)
        if len(parts) != 3:
            raise ValueError("Invalid account file format.")
        return parts
    except OSError:
        return None

def register_or_login():
    try:
        account = _read_account()
    except ValueError as error:
        print("Account file is invalid:", error)
        return False
    if account is None:
        print("FIRST START — REGISTRATION")
        while True:
            username = input("Username: ").strip()
            allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-"
            if not username or any(char not in allowed for char in username):
                print("Username may contain letters, numbers, periods, hyphens, and underscores.")
                continue
            password = _password_prompt("Password: ")
            confirmation = _password_prompt("Confirm password: ")
            if len(password) < 4:
                print("Password must have at least 4 characters.")
                continue
            if password != confirmation:
                print("Passwords do not match. Try again.")
                continue
            salt = _make_salt()
            digest = _hash_password(password, salt)
            with open(ACCOUNT_FILE, "w") as file:
                file.write(username + "|" + salt + "|" + digest)
            print("Registration complete. Welcome,", username + "!")
            return True

    username_saved, salt, digest = account
    print("SIGN IN")
    for _ in range(3):
        username = input("Username: ").strip()
        password = _password_prompt("Password: ")
        candidate = _hash_password(password, salt)
        if username == username_saved and candidate == digest:
            print("Sign-in successful. Welcome,", username + "!")
            return True
        print("Incorrect username or password.")
    print("Too many failed attempts.")
    return False
