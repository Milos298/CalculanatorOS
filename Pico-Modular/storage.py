"""Simple note storage in the Pico internal flash memory."""
from config import NOTES_FILE

def add_note(text):
    with open(NOTES_FILE, "a") as file:
        file.write(text + "\n")

def read_notes():
    try:
        with open(NOTES_FILE, "r") as file:
            return file.read()
    except OSError:
        return ""
