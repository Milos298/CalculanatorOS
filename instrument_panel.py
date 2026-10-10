"""Panel simulovaných přístrojů; hodnoty nejsou z reálných senzorů."""
import random
import time

def show_temperature():
    print("Simulovaná teplota:", round(18 + random.random() * 10, 1), "°C")

def show_signal():
    print("Simulovaná síla signálu:", random.randint(1, 100), "%")

def stopwatch():
    input("Enter spustí stopky.")
    start = time.time()
    input("Měřím... Enter zastaví.")
    print("Naměřeno:", round(time.time() - start, 2), "sekund")

def main():
    while True:
        print("\nPŘÍSTROJE")
        print("1 Teploměr (simulace) | 2 Wi-Fi síla (simulace) | 3 Stopky | 0 Konec")
        choice = input("> ").strip()
        if choice == "1":
            show_temperature()
        elif choice == "2":
            show_signal()
        elif choice == "3":
            stopwatch()
        elif choice == "0":
            break
        else:
            print("Vyber 0, 1, 2 nebo 3.")

if __name__ == "__main__":
    main()
