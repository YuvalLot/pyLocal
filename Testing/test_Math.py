
from Testing.TestingSuper import Testing
from math import log, cos, sin, tan, asin, acos, atan
from random import randint, shuffle


class MathTest(Testing):

    @classmethod
    def setUpClass(cls) -> None:
        data = """
        
        import Math;
        import NumberList;

        """
        cls.interpreter = cls.upload(data)

    def test_Math(self):

        # Add, Sub, Mul, Div, Mod, Power
        self.resulted("Add(3,4,?x)", "?x", "7")
        self.resulted("Sub(9.56,5,?x)", "?x", 9.56-5.0)
        self.resulted("Mul(6.77,-3.1,?x)", "?x", 6.77*-3.1)
        self.resulted("Div(12,3,?x)", "?x", 4)
        self.resulted("Mod(361,7,?x)", "?x", 361 % 7)
        self.resulted("Power(2,6,?x)", "?x", 2**6)
        self.resulted("Power(2,0.5,?x)", "?x", 2**0.5)
        self.noSolution("Div(8,0,?x)")
        self.noSolution("Mod(8,0,?x)")

        # Neg, Half, Abs, Floor, Ceil
        self.resulted("Neg(6,?x)", "?x", -6)
        self.resulted("Abs(6,?x)", "?x", 6)
        self.resulted("Abs(-2.3,?x)", "?x", 2.3)
        self.resulted("Half(6,?x)", "?x", 3)
        self.resulted("Half(13,?x)", "?x", 6)
        self.resulted("Ceil(6,?x)", "?x", 6)
        self.resulted("Ceil(6.54,?x)", "?x", 7)
        self.resulted("Floor(6.54,?x)", "?x", 6)
        self.resulted("Floor(-2.54,?x)", "?x", -3)

        # LT, LTE, GT, GTE, E
        self.isTrue("LT(3,6)")
        self.isTrue("GT(34.5,6)")
        self.isTrue("LTE(6,6)")
        self.isTrue("LTE(-8,6)")
        self.isTrue("GTE(6,6)")
        self.isTrue("GTE(6.01,6)")
        self.isTrue("E(6,6)")
        self.resulted("E(6,?x)", "?x", 6)

        # pi, e
        self.resulted("Pi(?x)", "?x", 3.141592653589793)
        self.resulted("Euler(?x)", "?x", 2.718281828459045)

        # Log, Ln, Logb
        self.resulted("Log(3,?x)", "?x", log(3, 10))

        # cos, sin, tan
        for i in range(1,10):
            self.resulted(f"Sin({i},?x)", "?x", sin(i))
            self.resulted(f"Cos({i},?x)", "?x", cos(i))
            self.resulted(f"Tan({i},?x)", "?x", tan(i))
            self.resulted(f"Sin(?x,{i/10})", "?x", asin(i/10))
            self.resulted(f"Cos(?x,{i/10})", "?x", acos(i/10))
            self.resulted(f"Tan(?x,{i/10})", "?x", atan(i/10))

        self.noSolution("Cos(?x,10)")
        self.noSolution("Sin(?y,10)")

    def test_NumberList_Range(self):
        self.resulted("Range(1,10,?x)", "?x", "[1,2,3,4,5,6,7,8,9,10]")
        self.resulted("Range(53,97,?x)", "?x", "[" + ",".join(map(str, range(53,98))) + "]")

    def test_NumberList_MaxMinSorted(self):
        for _ in range(10):
            rand_list = [randint(-30,30) for i in range(50)]
            shuffle(rand_list)
            lcl_rand_list = "[" + ",".join(map(str, rand_list)) + "]"

            _sorted = list(sorted(rand_list))
            lcl_sorted = "[" + ",".join(map(str, _sorted)) + "]"

            self.resulted(f"Min({lcl_rand_list},?x)", "?x", min(rand_list))
            self.resulted(f"Max({lcl_rand_list},?x)", "?x", max(rand_list))
            self.resulted(f"Sort({lcl_rand_list},?x)", "?x", lcl_sorted)
            self.resulted(f"Sum({lcl_rand_list},?x)", "?x", sum(rand_list))