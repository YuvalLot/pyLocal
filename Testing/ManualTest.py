
import Interpreter
import Lexer
from main import imports

lexer = Lexer.build()
interpreter = Interpreter.Interpreter(10, imports, path="D:\\Yuval Lotenberg\\Documents\\LCL\\")

board = [['?a', '?b', '?c', '?d'], ['?e', '?f', '?g', '?h'], ['?i', '?j', '?k', '?l'], ['?m', '?n', '?o', '?p']]

for i in range(len(board)):
    print(f"elim not_unique([{board[i][0]}, {board[i][1]}, {board[i][2]}, {board[i][3]}])")
for i in range(len(board)):
    print(f"elim not_unique([{board[0][i]}, {board[1][i]}, {board[2][i]}, {board[3][i]}])")

# X( ?a, ?b, ?c, ?d, ?e, ?f, ?g, ?h, ?i, ?j, ?k, ?l, ?m, ?n, ?o, ?p )