"""Simple safe calculator without eval()."""
class Parser:
    def __init__(self, text):
        if not isinstance(text, str):
            raise ValueError("Enter a mathematical expression.")
        if len(text) > 256:
            raise ValueError("Expression is too long (maximum 256 characters).")
        self.text = "".join(text.split())
        if not self.text:
            raise ValueError("Enter a mathematical expression.")
        self.pos = 0
        self.depth = 0

    def parse(self):
        value = self.expression()
        if self.pos != len(self.text):
            raise ValueError("Unexpected character: " + self.text[self.pos])
        return value

    def expression(self):
        value = self.term()
        while self.peek() in ("+", "-"):
            op = self.take()
            right = self.term()
            value = value + right if op == "+" else value - right
        return value

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

    def factor(self):
        sign = 1
        while self.peek() in ("+", "-"):
            if self.take() == "-":
                sign = -sign
        if self.peek() == "(":
            self.take()
            if self.depth >= 24:
                raise ValueError("Parentheses are nested too deeply (maximum 24 levels).")
            self.depth += 1
            try:
                value = self.expression()
            finally:
                self.depth -= 1
            if self.take() != ")":
                raise ValueError("Missing closing parenthesis.")
            return sign * value
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
        try:
            return sign * float(self.text[start:self.pos])
        except ValueError:
            raise ValueError("Enter a valid number.")

    def peek(self):
        return self.text[self.pos] if self.pos < len(self.text) else ""

    def take(self):
        char = self.peek()
        if not char:
            raise ValueError("Expression is incomplete.")
        self.pos += 1
        return char

def calculate(text):
    return Parser(text).parse()
