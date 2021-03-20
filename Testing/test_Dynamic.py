
from Testing.TestingSuper import Testing


class DynamicTest(Testing):

    @classmethod
    def setUpClass(cls) -> None:

        data = """
        
        import Dynamic;
        import List;
       
        declare LL;
        
        """

        cls.compiler = cls.upload(data)

    def test_Assert(self):

        self.isTrue("Create(A)")
        self.isTrue("AssertFE(A(1,5))")
        self.isTrue("AssertFE(A(4,7))")
        self.isTrue("AssertFE(A(8,9))")

        self.multipleSolved("A(?x,?y)", x=("1","4","8"), y=("5","7","9"))

        self.isTrue("SwitchRecursive(A)")
        self.isTrue("AssertF(A(10,10))")

        self.singleSolved("A(?x,?y)", x="10", y="10")

    def test_AssertC(self):

        self.isTrue("Create(Edge)&Create(Connected)")
        self.isTrue("AssertFE(Edge(1,2))&AssertFE(Edge(1,3))&AssertFE(Edge(1,4))&AssertFE(Edge(3,2))")
        self.isTrue("AssertC(Connected(?x,?y)>>(Edge(?x,?y)|Edge(?y,?x)))")

        self.solved("Connected(?x,?y)")

        self.isTrue("Create(Even)")
        self.isTrue("AssertC(Even(?x)>>(Mod(?x,2,0)))")

        self.singleSolved("Filter(Even,[1,5,8,4],?x)", x="[8,4]")
