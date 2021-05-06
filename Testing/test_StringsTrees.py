
from Testing.TestingSuper import Testing


class StringsTrees(Testing):

    @classmethod
    def setUpClass(cls) -> None:
        data = """
        import Strings;
        import BinaryTrees;
        
        set SampleTree
            case Branch(Apple, Branch(Orange, Leaf, Branch(Cherry, Leaf, Leaf)), Branch(Blueberry,Branch(Lemon, Leaf, Leaf),Branch(Pineapple, Leaf, Leaf)));

        """
        cls.interpreter = cls.upload(data)

    def test_Tree_Tree(self):
        self.solved("SampleTree(?x)&BinaryTree(?x)")

    def test_Tree_CompTree(self):
        self.singleSolved("CompTree(3,?x)&BinaryTree(?x)",
                          x="Branch(1,Branch(2,Branch(4,Leaf,Leaf),Branch(5,Leaf,Leaf)),Branch(3,Branch(6,Leaf,Leaf),Branch(7,Leaf,Leaf)))")

    def test_Tree_Size(self):
        self.multipleSolved("SampleTree(?x)&Size(?x,?y)", not_care=("?x",), y=("6",))
        self.multipleSolved("CompTree(3,?x)&Size(?x,?y)", not_care=("?x",), y=("7",))

    def test_Tree_Depth(self):
        self.multipleSolved("SampleTree(?x)&Depth(?x,?y)", not_care=("?x",), y=("3",))
        self.multipleSolved("CompTree(5,?x)&Depth(?x,?y)", not_care=("?x",), y=("5",))
