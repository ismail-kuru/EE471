import math


class Calculator:
    """A calculator that remembers the result of its last operation.

    Extended from Mini Project 1 with calculate(), which picks one of the four
    operations by name so the web layer never needs eval().
    """

    OPERATIONS = ("add", "subtract", "multiply", "divide")

    def __init__(self):
        self._current_val = 0

    def add(self, x, y):
        self._current_val = x + y
        return self._current_val

    def subtract(self, x, y):
        self._current_val = x - y
        return self._current_val

    def multiply(self, x, y):
        self._current_val = x * y
        return self._current_val

    def divide(self, x, y):
        if y == 0:
            raise ValueError("Cannot divide by zero.")
        self._current_val = x / y
        return self._current_val

    def calculate(self, x, y, operation):
        """Run the named operation on x and y and return the result.

        Raises:
            ValueError: If an operand is not a number, the operation is
                unknown, or y is 0 for divide.
        """
        for operand in (x, y):
            # bool is a subclass of int in Python, so True/False would slip through.
            if isinstance(operand, bool) or not isinstance(operand, (int, float)):
                raise ValueError("Operands must be numbers.")
            if not math.isfinite(operand):
                raise ValueError("Operands must be finite numbers.")
        if operation not in self.OPERATIONS:
            raise ValueError(f"Unknown operation '{operation}'. Use one of: {', '.join(self.OPERATIONS)}.")
        result = getattr(self, operation)(x, y)
        if not math.isfinite(result):
            raise ValueError("Result is too large.")
        return result
