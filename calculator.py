"""Interaktivní kalkulačka se základními operacemi."""
def main():
    print("Calculanator — kalkulačka")
    while True:
        first = input("První číslo (nebo q): ").strip()
        if first.lower() == "q":
            break
        operation = input("Operace (+ - * /): ").strip()
        second = input("Druhé číslo: ").strip()
        try:
            a = float(first)
            b = float(second)
            if operation == "+":
                result = a + b
            elif operation == "-":
                result = a - b
            elif operation == "*":
                result = a * b
            elif operation == "/":
                if b == 0:
                    print("Nulou dělit nejde.")
                    continue
                result = a / b
            else:
                print("Neznámá operace.")
                continue
            print("=", result)
        except ValueError:
            print("Zadej platná čísla.")
    print("Ahoj!")

if __name__ == "__main__":
    main()
