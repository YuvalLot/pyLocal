"""

Main

Runs the design and includes the version, recursion limit, and time limit.

"""


import Design
import sys

version = '1.8'
time_limit = 3000
recursion_limit = 1000000
imports = [
    'List',
    'Random',
    'Math',
    'Types',
    'Predicates',
    'Save',
    'Sequences',
    'NumberList',
    'Strings',
    'BinaryTrees',
    'Propositions',
    'Inspect',
    'Dynamic',
    'Filestream',
    'Zebra',
    'Sets'
    ]

if __name__ == "__main__":
    sys.setrecursionlimit(200000)

    C = Design.Console(version, time_limit, recursion_limit, imports)

    arg = sys.argv

    if len(arg) == 2:
        C.UploadAction(arg=arg[1])

    C.run()
