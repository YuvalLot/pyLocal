
from Testing.TestingSuper import Testing
from collections import defaultdict
from math import factorial
from random import choice


class RandomTypesSaveTest(Testing):

    @classmethod
    def setUpClass(cls) -> None:
        data = """
        import Random;
        import Types;
        import Save;
        
        set A
            case Some, Thing;
        
        set B
            case Another, Thing;
        
        package I{?x}
            case ?x;
        
        package G{?x, ?y}
            case then I{?x}(?y);
        
        declare T;
        
        use I{4} as Four;
        
        """
        cls.compiler = cls.upload(data)

    def test_General(self):

        query = "A(?x)"
        self.generic(query, [])

        query = "A(?x,?y)"
        self.generic(query, [{"?x":"Some", "?y":"Thing"}])

        query = "B(?x)"
        self.generic(query, [])

        query = "B(?x,?y)"
        self.generic(query, [{"?x": "Another", "?y": "Thing"}])

        query = "G{3,3}()"
        self.generic(query, [{}])

        query = "I{T(4)}(?x)"
        self.generic(query, [{"?x":"T(4)"}])

        query = "E(G{T(4),T(4)},?x)&?x()"
        self.generic(query, [{"?x":"G{T(4),T(4)}"}])

    def test_Random_Flip(self):

        query = "Flip(?c)"
        count = defaultdict(int)
        for _ in range(100):
            sols = list(self.compiler.mixed_query(query, 0, 300, unP=True))
            if {"?c":"1"} not in sols and {"?c":"0"} not in sols:
                self.assertEqual(0, 1, msg="Flip returned something different than 0 and 1")
            else:
                count[sols[0]["?c"]] += 1

        self.assertLess(abs(count["0"]-count["1"]), 20)

    def test_Random_RandBool(self):

        N = 500

        query = "RandBool()"
        count = defaultdict(int)
        for _ in range(N):
            sols = list(self.compiler.mixed_query(query, 0, 300, unP=True))
            if len(sols) not in (0,1):
                self.assertEqual(0, 1, msg="RandBool returned multiple solutions")
            if len(sols) == 1 and sols[0] != {}:
                self.assertEqual(0, 1, msg="RandBool returned solution with variables")
            count[len(sols)] += 1
        self.assertLess(abs(count[0]-count[1]), 70)

    def g_test_Random_RandInt(self, a, b, N):
        query1 = f"RandInt({a},{b},?x)"
        count = defaultdict(int)
        for _ in range(N):
            sols = list(self.compiler.mixed_query(query1, 0, 300, unP=True))
            self.assertEqual(len(sols), 1)
            count[sols[0]["?x"]] += 1
        expected = N // (b - a + 1)
        for key in count.keys():
            self.assertLess(abs(count[key] - expected), 5 / 100 * N)

    def test_Random_RandInt(self):

        self.g_test_Random_RandInt(3, 19, 500)
        self.g_test_Random_RandInt(26, 234, 1000)

    def g_test_Random_Choice(self, l:list, N:int):

        query = f"Choice([{','.join(l)}],?x)"
        count = defaultdict(int)
        for _ in range(N):
            sols = list(self.compiler.mixed_query(query, 0, 300, unP=True))
            self.assertEqual(len(sols), 1)
            self.assertIn(sols[0]["?x"], l)
            count[sols[0]["?x"]] += 1
        expected = N // (len(l))
        for key in count.keys():
            self.assertLessEqual(abs(count[key] - expected), 10 / 100 * N)

    def test_Random_Choice(self):

        self.g_test_Random_Choice(['1','2','3','4','5','6','7','8','9','10','11'],500)
        self.g_test_Random_Choice(['Alice', 'Bob', 'Charlie', 'Dave', 'Eve'], 500)

    def assertPermut(self, l1:list, l2:str):
        l2 = l2[1:-1].split(",")
        self.assertEqual(sorted(l1), sorted(l2))

    def g_test_Random_Shuffle(self, l:list, N:int, test_random=False):

        query = f"Shuffle([{','.join(l)}],?x)"
        count = defaultdict(int)
        for _ in range(N):
            sols = list(self.compiler.mixed_query(query, 0, 300, unP=True))
            self.assertEqual(len(sols), 1)
            self.assertPermut(l, sols[0]["?x"])
            count[sols[0]["?x"]] += 1
        if test_random:
            expected = N // (factorial(len(l)))
            for key in count.keys():
                self.assertLessEqual(abs(count[key] - expected), 15 / 100 * N)

    def test_Random_Shuffle(self):

        l1 = ['1','2','3']
        self.g_test_Random_Shuffle(l1, 500, True)

        l2 = ['Alice','Bob','Charlie','Dave','Eve','Fish']
        self.g_test_Random_Shuffle(l2, 100)

    def test_Random_RandNum(self):

        N = 500

        query = 'RandNum(?x)'
        count = defaultdict(int)
        for _ in range(N):
            sols = list(self.compiler.mixed_query(query, 0, 300, True))
            self.assertEqual(len(sols), 1)
            num = sols[0]["?x"][:4]
            count[num] += 1
        expected = N // 100
        for key in count.keys():
            self.assertLess(abs(count[key] - expected), 10/100 * N)

    def test_Types_Atom(self):

        self.isTrue('Atom(3)')
        self.isTrue('Atom("Alice")')
        self.isTrue('Atom(Alice)')
        self.isTrue('Atom(4.76)')
        self.isTrue('Atom(4_5-6)')
        self.isTrue('Atom(Bob_And_alice)')

        self.noSolution("Atom(?x)")
        self.noSolution("Atom(Add)")
        self.noSolution("Atom([1,2,3,4])")

        self.generic("Add(3,4,?x)&Atom(?x)", [{"?x":"7"}])

    def test_Types_Variable(self):

        self.solved('Variable(?x)')
        self.solved('Variable(?Apple_Oranges)')
        self.solved('Variable(?@1)')

        self.noSolution('Variable(1)')
        self.noSolution('Variable([1,2,3])')
        self.noSolution('Add(1,2,?x)&Variable(?x)')
        self.noSolution('Variable(Add)')

    def test_Types_List(self):
        self.isTrue('List([1,2,3])')
        self.isTrue('List([A,"A","Hello Old Chum"])')

        self.solved('List([1,2,?x])')
        self.solved('List([?x*?xs])')
        self.solved('List([?x*[?y*?ys]])')

        self.noSolution('List(1)')
        self.noSolution('List(4)')
        self.noSolution('List(Apple)')
        self.noSolution('List("123")')

    def test_Types_Predicate(self):
        self.isTrue("Predicate(Add)")
        self.isTrue("Predicate(A)")
        self.isTrue("Predicate(B)")
        self.isTrue("Predicate(Removed)")
        self.isTrue("Predicate(RandBool)")
        self.isTrue("Predicate(Predicate)")

        self.noSolution('Predicate(1)')
        self.noSolution('Predicate(4)')
        self.noSolution('Predicate(Apple)')
        self.noSolution('Predicate("123")')
        self.noSolution('Predicate([A,B,C])')
        self.noSolution('Predicate(G)')

    def test_Types_Package(self):
        self.isTrue('Package(G)')
        self.isTrue('Package(I)')

        self.noSolution('Package(1)')
        self.noSolution('Package(4)')
        self.noSolution('Package(Apple)')
        self.noSolution('Package("123")')
        self.noSolution('Package([A,B,C])')
        self.noSolution('Package(A)')
        self.noSolution('Package(T)')

    def test_Types_Title(self):
        self.isTrue("Title(T())")
        self.isTrue("Title(T(1,2))")

        self.solved("Title(T(?x))")

        self.noSolution('Title(1)')
        self.noSolution('Title(4)')
        self.noSolution('Title(?x)')
        self.noSolution('Title("123")')
        self.noSolution('Title([A,B,C])')
        self.noSolution('Title(A)')

    def test_Types_SameType(self):

        Atoms = ['Apple', '"123"', '45', 'Jong_8-9']
        Variables = ['?x', '?y', '?@45', '?87j']
        Predicates = ['Add', 'Logb', 'A', 'B', 'Four']
        Packages = ['G', 'I']
        Lists_without_vars = ['[1,2,3,4]','[1*[2*[3*[]]]]', '[[1,2],[3,4],[5,6]]']
        Lists_with_vars = ['[?x,1,?y]', "[[?x,?y]*?zs]"]
        Titles = ['T(6,T(7,T()))', 'T(6,7,[1,2,3])']

        choose = lambda: choice([(0,Titles),
                                 (1,Variables),
                                 (2,Predicates),
                                 (3,Packages),
                                 (4,Atoms),
                                 (5,Lists_with_vars+Lists_without_vars)])

        for _ in range(100):
            t1, x1 = choose()
            t2, x2 = choose()
            x1, x2 = choice(x1), choice(x2)
            if t1 == t2:
                self.solved(f"SameType({x1},{x2})")
            else:
                self.noSolution(f"SameType({x1},{x2})")

    def test_Types_Known(self):

        known = ['1', 'Apple', '"Hello Old Chum"', '[1,2,3,[4,5,6]]', 'T(1,3)', '"???"']
        unknown = ['?x', '?@3', '[1,2,3,?z]', 'T(1,T(5,T(7,T(?d,T(7)))))']

        for k in known:
            self.isTrue(f"Known({k})")
        for u in unknown:
            self.noSolution(f"Known({u})")

    def test_Save_Save(self):
        self.isTrue("Save(10)")
        self.isTrue("Save(Apple)")
        self.isTrue('Save("??ABC??")')
        self.isTrue("Save(4)")
        self.isTrue("Save(T(6))")
        self.isTrue("Save([1,2,3,4])")
        self.isTrue("Save(I{5})")

        self.noSolution("Save(?x)")
        self.generic("Add(3,4,?x)&Save(?x)", [{"?x":"7"}])
        self.load()

    def load(self):
        self.generic("Load(?x)&Sub(?x,4,?y)", [{"?x":"7","?y":"3"}])
        self.generic("Load(?x)&?x(?y)", [{"?x":"I{5}", "?y":"5"}])
        self.generic("Load(3,?x)", [{"?x":"[[1,2,3,4],T(6),4]"}])
        self.generic("View(?x)", [{"?x":'"??ABC??"'}])
        self.generic("LoadAll(?x)", [{"?x":'["??ABC??",Apple,10]'}])
        self.noSolution("Load(?x)")
        self.generic("LoadAll(?x)", [{"?x":"[]"}])
        self.generic("Load(4,?x)", [{"?x":"[]"}])
