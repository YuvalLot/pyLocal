from functools import reduce

import Interpreter
import Lexer
from main import imports

import numpy

lexer = Lexer.build()
interpreter = Interpreter.Interpreter(10, imports, path="D:\\Yuval Lotenberg\\Documents\\LCL\\")


def create_board():
    board = [[]]

    over = "over "

    for i in range(1, 9 * 9 + 1):
        s = f"?x{i}"
        over += s + ", "
        print(f"of {s} : Valid({s})")
        board[-1].append(s)
        if i % 9 == 0 and i != 81:
            board.append([])

    print(over)

    # rows
    for row in board:
        print(f"elim not_unique([{', '.join(row)}])")

    board = numpy.array(board)
    for i in range(len(board)):
        print(f"elim not_unique([{', '.join(board[:, i])}])")

    i = 0
    j = 0

    while True:
        if j == 9:
            j = 0
            i += 3
        if i == 9:
            break
        t = [list(x) for x in board[i:i + 3, j:j + 3]]
        t = reduce(lambda x, y: x + y, t)
        print(f"elim not_unique([{', '.join(t)}])")
        j += 3


def is_valid(_board):
    if len(_board) == 9:
        _board = reduce(lambda x, y: x + y, _board, [])
    nums = {1, 2, 3, 4, 5, 6, 7, 8, 9}
    board = []
    for i in range(0, len(_board), 9):
        if set(_board[i:i + 9]) != nums:
            print("WRONG")
            print(_board[i:i+9])
            return False
        board.append(_board[i:i + 9])

    board = numpy.array(board)
    for i in range(len(board)):
        if set(board[:, i]) != nums:
            print("WRONG")
            return False

    i = 0
    j = 0

    while True:
        if j == 9:
            j = 0
            i += 3
        if i == 9:
            break
        t = [list(x) for x in board[i:i + 3, j:j + 3]]
        t = reduce(lambda x, y: x + y, t)
        if set(t) != nums:
            print("WRONG")
            return False
        j += 3

    print("Solved")
    return True


def replace_zeros(board):
    k = 1
    for i in range(len(board)):
        for j in range(len(board[i])):
            board[i][j] = board[i][j] if board[i][j] != 0 else f"?x{k}"
            k += 1

    print("[")
    for i in range(len(board)):
        print("\t[", end="")
        t = []
        for j in range(len((board[i]))):
            t.append(str(board[i][j]))
        print(", ".join(t), end="")
        print("]")
    print("]")

def rep(string: str, d):
    for key in d:
        string = string.replace(key, d[key])
    return string

print(rep("""

const OneOf(Eugene, 40, names, ages)
   const OneOf(Sean, black, names, shirts)
   const E(?disc4, 80)
   const OneOf(Dustin, 60, names, discounts)
   const ExactlyLeft(grape, lemon, juices, juices)
   const OneOf(Keith, game_console, names, deals)
   const ExactlyLeft(80, blue, discounts, shirts)
   const OneOf(grape, beard_trimmer, juices, deals)
   const ToTheLeft(Keith, black, names, shirts)
   const NextTo(smartphone, black, deals, shirts)

""", {
    "shirts" : "[?shirt1, ?shirt2, ?shirt3, ?shirt4, ?shirt5]",
    "names" : "[?name1, ?name2, ?name3, ?name4, ?name5]",
    "deals" : "[?deal1, ?deal2, ?deal3, ?deal4, ?deal5]",
    "discounts" : "[?disc1, ?disc2, ?disc3, ?disc4, ?disc5]",
    "ages" : "[?age1, ?age2, ?age3, ?age4, ?age5]",
    "juices" : "[?juice1, ?juice2, ?juice3, ?juice4, ?juice5]"
}))