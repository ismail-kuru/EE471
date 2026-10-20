from custom_classes import Calculator

calc = Calculator()
result = calc.add(10, 5)
result = calc.multiply(result, 2)
result = calc.divide(result, 3)
print(f"(10 + 5) * 2 / 3 = {result}")
