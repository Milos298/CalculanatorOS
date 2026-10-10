"""Matrix režim pro terminál."""
import random
import time

def main():
    chars = "01ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    try:
        for _ in range(30):
            print("".join(random.choice(chars) for _ in range(70)))
            time.sleep(0.08)
    except KeyboardInterrupt:
        print("\nMatrix režim ukončen.")

if __name__ == "__main__":
    main()
