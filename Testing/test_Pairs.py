
from Testing.TestingSuper import Testing


class PairTest(Testing):

    @classmethod
    def setUpClass(cls) -> None:
        data = """

        set A
            case 1/2;
        
        set B
            case ?x, ?y, ?x/?y;
        
        set C
            case [], [], []
            case [?x * ?xs], [?y * ?ys], [?z * ?more] then B(?x, ?y, ?z) & C(?xs, ?ys, ?more);

        """

        cls.compiler = cls.upload(data)

    def test_BasicPair(self):
        self.singleSolved("A(?x)", x="1/2")
        self.singleSolved("A(?x/?y)", x="1", y="2")

    def test_PairConstructor(self):
        self.singleSolved("B(apple,orange,?x)", x="apple/orange")
        self.singleSolved("B(?x,?y,(1/2)/(3/4))", x="(1/2)", y="(3/4)")

    def test_ComplexPairings(self):
        self.singleSolved("C([1,2,3,4],[5,6,7,8],?x)", x="[(1/5),(2/6),(3/7),(4/8)]")
        self.singleSolved("C([1,2,3,4],[5,6,7/[1,2,3,D(1)],8],?x)", x="[(1/5),(2/6),[3/[7/[1,2,3,D(1)]]],(4/8)]")
