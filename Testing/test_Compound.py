
from Testing.TestingSuper import Testing


class CompoundTest(Testing):

    @classmethod
    def setUpClass(cls) -> None:
        data = """

        import List;

        set AddOne
            case ?x, ?y then Add(?x, 1, ?y);

        connect AddThree = AddOne + AddOne + AddOne;

        connect Word1 = As : ?n + Bs : ?n + Cs : ?n;

        connect As : ?n = {E(?n, 0)}
                        | [a] + As : ?m + {Add(?m, 1, ?n)};
        
        connect Bs : ?n = {E(?n, 0)}
                        | [b] + Bs : ?m + {Add(?m, 1, ?n)};
        
        connect Cs : ?n = {E(?n, 0)}
                        | [c] + Cs : ?m + {Add(?m, 1, ?n)};
        
        connect Word2 = As : ?n + Bs : ?m + Cs : ?k;

        """

        cls.compiler = cls.upload(data)

    def test_AddThree(self):
        self.singleSolved("AddThree(4,?x)", x=7)

    def test_Word1(self):
        self.isTrue("Word1([a,b,c],[])")
        self.isTrue("Word1([a,a,b,b,c,c,x],[x])")

        self.noSolution("Word1([a,a,b,b,c,c,c],[])")

    def test_Word2(self):
        self.isTrue("Word2([a,a,b,c,c,c],[])")
        self.isTrue("Word2([],[])")
        self.isTrue("Word2([a,a,c,c,c],[])")
        self.isTrue("Word2([a,a,b],[])")

        self.noSolution("Word2([a,a,b,b,c,c,a],[])")
