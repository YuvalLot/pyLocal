
import Lexer
import Interpreter
import unittest
from main import imports
import logging

logging.basicConfig(filename="Logging.log", level=logging.DEBUG)

def toLCL(_list):
    if type(_list) is str:
        return _list
    _list = map(toLCL, _list)
    return "[" + ",".join(_list) + "]"


class Testing(unittest.TestCase):

    @classmethod
    def upload(cls, data, _imports=None):
        lexer = Lexer.build()
        lexer.input(data)
        tokens = []
        while True:
            tok = lexer.token()
            if not tok:
                break  # No more input
            tokens.append(tok)
        compiler = Interpreter.Interpreter(20, imports, path="D:\Yuval Lotenberg\Documents\LCL")
        compiler.read(tokens)

        if len(compiler.errorLoad) != 0:

            logging.debug(f"{compiler.errorLoad}")

            assert compiler.errorLoad == []

        return compiler


    def generic(self, query=None, expected=None, notExpected=None):
        if query is None or expected is None:
            return

        sols = list(self.compiler.mixed_query(query, 0, 10000, unP=True))
        for e in expected:
            self.assertIn(e, sols, msg=f"Expected {e} in {query}")
            if e in sols:
                sols.remove(e)

        self.assertEqual(len(sols), 0, f"Extra solutions to {query}: {sols}")

        if notExpected:
            for e in notExpected:
                self.assertNotIn(e, sols)

    def isTrue(self, query=None):
        if query is None:
            return

        sols = list(self.compiler.mixed_query(query, 0, 300, unP=True))

        self.assertEqual(len(sols), 1, msg=f"Expected True for {query}")
        self.assertEqual(sols[0], {}, msg=f"Expected no variables for {query}, in {sols[0]}")

    def noSolution(self, query=None):
        if query is None:
            return

        sols = list(self.compiler.mixed_query(query, 0, 300, unP=True))

        self.assertEqual(len(sols), 0, msg=f"Query {query} has solutions: {sols}")

    def solved(self, query=None):
        if query is None:
            return

        sols = list(self.compiler.mixed_query(query, 0, 300, unP=True))
        self.assertNotEqual(len(sols), 0, msg=f"Query {query} has no solutions")

    def resulted(self, query=None, var=None, result=None):
        if query is None or result is None or var is None:
            return

        self.generic(query, [{var:str(result)}])

    def singleSolved(self, query=None, **kwargs):
        if query is None:
            return

        sols = list(self.compiler.mixed_query(query, 0, 10000, unP=True))
        self.assertEqual(len(sols), 1, msg=f"Expected Single solution for {query}")

        sol_dict = {}
        for key, value in kwargs.items():
            sol_dict["?" + str(key)] = str(value)

        self.assertEqual(sols[0], sol_dict, msg=f"solution unexpected in query {query}")

    def multipleSolved(self, query=None, **kwargs):
        if query is None:
            return

        if "not_care" in kwargs.keys():
            d_vars = kwargs["not_care"]
            del kwargs["not_care"]
            dicts = []
            n = len(kwargs[list(kwargs.keys())[0]])
            for i in range(n):
                d = {}
                for key, value in kwargs.items():
                    d["?" + key] = kwargs[key][i]
                dicts.append(d)
            sols = list(self.compiler.mixed_query(query, 0, 10000, unP=True))
            self.assertEqual(len(sols), n, msg=f"Expected {n} solutions to {query}")
            for sol in sols:
                d = sol.copy()
                for var in d_vars:
                    if var in sol.keys():
                        del d[var]
                self.assertIn(d, dicts, msg=f"Received {d}, in query {query}")


        else:
            dicts = []
            n = len(kwargs[list(kwargs.keys())[0]])
            for i in range(n):
                d = {}
                for key, value in kwargs.items():
                    d["?"+key] = kwargs[key][i]
                dicts.append(d)

            self.generic(query, dicts)


