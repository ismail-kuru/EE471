"""The voice command table: which word belongs to which calculator key.

The same table is used in both directions: to read voice commands (word → key)
and to make the keys speak (key → word).
"""

import re

# Key → the word from the exercise's command table, in keypad order.
KEY_WORDS = {
    "7": "seven", "8": "eight", "9": "nine", "÷": "over",
    "4": "four", "5": "five", "6": "six", "×": "times",
    "1": "one", "2": "two", "3": "three", "−": "minus",
    "0": "zero", ".": "point", "=": "is", "+": "plus",
}

# Other ways Azure may write what was said: homophones ("to" for "two"),
# symbols ("+" for "plus") and common synonyms ("equals" for "is").
ALTERNATIVES = {
    "oh": "0", "won": "1", "to": "2", "too": "2", "for": "4", "ate": "8",
    "dot": ".",
    "divide": "÷", "divided": "÷", "/": "÷",
    "x": "×", "multiply": "×", "multiplied": "×", "*": "×",
    "subtract": "−", "-": "−",
    "add": "+",
    "equals": "=", "equal": "=",
}

WORD_TO_KEY = {word: key for key, word in KEY_WORDS.items()}
WORD_TO_KEY.update({key: key for key in KEY_WORDS})  # "+", "÷", "×", "−", "=" written as symbols
WORD_TO_KEY.update(ALTERNATIVES)

# A number such as 52 or 5.2, a word, or one operator symbol.
TOKEN = re.compile(r"\d+(?:\.\d+)?|[a-z]+|[+\-−×*/÷=]")


def parse(text):
    """Turn recognized speech into calculator keys.

    For example "Five plus two is." and "5 + 2 =" both give ["5", "+", "2", "="].
    Words that are not commands ("by", "the", ...) are ignored.
    """
    keys = []
    for token in TOKEN.findall(text.lower()):
        if token[0].isdigit():
            # Azure writes spoken numbers as digits, e.g. "52" or "5.2"; press each character.
            keys.extend(token)
        elif token in WORD_TO_KEY:
            keys.append(WORD_TO_KEY[token])
    return keys
