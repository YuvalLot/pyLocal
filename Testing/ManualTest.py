
import Interpreter
import Lexer
from main import imports

lexer = Lexer.build()
interpreter = Interpreter.Interpreter(10, imports, path="D:\\Yuval Lotenberg\\Documents\\LCL\\")

nationalities = [
    "norwegian",
    "dane",
    "brit",
    "german",
    "swede",
]

colors = [
    "yellow",
    "blue",
    "red",
    "green",
    "white"
]

drinks = [
    "water",
    "tea",
    "milk",
    "beer",
    "coffee"
]

s = []
index = 1

for nation in nationalities:
    s.append(f"In(person({nation}, ?_{index}, ?_{index+1}, ?_{index+2}, ?_{index+3}), ?persons)")
    index += 4

for color in colors:
    s.append(f"In(person(?_{index}, {color}, ?_{index + 1}, ?_{index + 2}, ?_{index + 3}), ?persons)")
    index += 4

print(" &\n".join(s))
