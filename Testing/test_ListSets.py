
from Testing.TestingSuper import Testing, toLCL
from random import choice, choices, randint
from itertools import chain, combinations


def powerset(iterable):
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))


class ListsTest(Testing):

    @classmethod
    def setUpClass(cls) -> None:
        data = """

        import Sets;
        import List;
        import Strings;
        
        declare T;
        
        set Even 
            case ?x then Mod(?x, 2, 0);
        
        package StartsWith{?c}
            case ?x then Chars(?x, [?c * ?cs]);
        
        set Functional1
            case ?x, ?y then Add(1,?x,?y);
        
        set Functional2
            case ?x, ?y then Appended(1, ?x, ?y); 

        """
        cls.interpreter = cls.upload(data)
        cls.lists = {"[1,2,3,4,5,6,7,8]":["1","2","3","4",'5',"6",'7','8'],
                     "[A,B,C,D,E,F]":["A", "B", "C", "D","E","F"],
                     "[G,H,I,J,K,L]":["G","H","I","J","K","L"],
                     "[Alice*[Bob*[Charlie*[Dave*[Eve*[Frank*[Grace]]]]]]]":["Alice", "Bob", "Charlie","Dave","Eve","Frank","Grace"],
                     "[1,3,5]":["1",'3','5'],
                     "[T(6),T(T(7),T(T(9))),T([1,2,3])]": ["T(6)","T(T(7),T(T(9)))", "T([1,2,3])"],
                     '["&","|","~","%","$"]':['"&"','"|"','"~"','"%"','"$"'],
                     "[2,4,6]":['2','4','6'],
                     "[[1,2,3],[4,5],6]":["[1,2,3]","[4,5]","6"]}

    def g_test_single(self, name, func):
        for lcl, py in self.lists.items():
            query = f"{name}({lcl},?x)"
            self.singleSolved(query, x=func(py))

    def test_Hd(self):
        self.g_test_single("Hd", lambda k: k[0])
        self.noSolution("Hd([],?x)")

    def test_Tl(self):
        self.g_test_single("Tl", lambda k: "[" + ",".join(k[1:]) + "]")
        self.noSolution("Tl([],?x)")

    def test_Last(self):
        self.g_test_single("Last", lambda k: k[-1])
        self.noSolution("Last([],?x)")

    def test_Reverse(self):
        self.g_test_single("Reverse", lambda k: "[" + ",".join(reversed(k)) + "]")
        self.singleSolved("Reverse([],?x)", x="[]")

    def test_Len(self):
        self.g_test_single("Len", lambda k: str(len(k)))
        self.singleSolved("Len([],?nnn)", nnn=0)

    def test_In(self):
        for lcl, py in self.lists.items():
            for _ in range(10):
                t = choice(py)
                query = f"In({t},{lcl})"
                self.isTrue(query)

        self.noSolution("In(3,[1,4,6])")
        self.noSolution("In(3,[1,4,[6,3]])")

    def test_Split(self):
        for lcl, py in self.lists.items():
            for _ in range(10):
                t = choice(py)
                i = py.index(t)
                left, right = py[:i], py[i+1:]
                self.singleSolved(f"Split({lcl},{t},?left,?right)", left=toLCL(left), right=toLCL(right))

    def test_Join(self):
        for i in range(20):
            (lcl1, py1), (lcl2, py2) = choice(list(self.lists.items())), choice(list(self.lists.items()))
            py3 = py1 + py2
            lcl3 = toLCL(py3)
            self.singleSolved(f"Join({lcl1},{lcl2},?x)", x=lcl3)

        for i in range(20):
            k = choices(list(self.lists.items()), k=5)
            lcls, pys = list(zip(*k))
            pyf = []
            for py in pys: pyf += py
            lclFinal = toLCL(pyf)
            lclBegin = toLCL(lcls)
            self.singleSolved(f"Join({lclBegin},?x)", x=lclFinal)

    def test_IndexChange(self):
        for lcl, py in self.lists.items():
            self.multipleSolved(f"Index(?i,{lcl},?x)", i=tuple(map(str, range(len(py)))), x=tuple(py))
        for lcl, py in self.lists.items():
            for i in range(len(py)):
                self.singleSolved(f"Index({i},{lcl},?x)", x=py[i])
            self.noSolution(f"Index({i+1},{lcl},?x)")
        for lcl, py in self.lists.items():
            for x in py:
                self.singleSolved(f"Index(?i,{lcl},{x})", i=py.index(x))

        _l = "[1,2,3,2,6]"
        self.multipleSolved(f"Index(?i,{_l},2)", i=('1','3'))

        for lcl,py in self.lists.items():
            for i in range(len(py)):
                pyf = py.copy()
                x = choice(["T(8)", "7", "[1,2,3,4,5]", "Apple"])
                pyf[i] = x
                lclf = toLCL(pyf)
                self.singleSolved(f"Change({lcl},{i},{x},?changed)", changed=lclf)

    def test_TakeDrop(self):
        for lcl, py in self.lists.items():
            for i in range(len(py)+1):
                take, drop = py[:i], py[i:]
                lcl_take, lcl_drop = toLCL(take), toLCL(drop)
                self.singleSolved(f"Take({lcl},{i},?taken)", taken=lcl_take)
                self.singleSolved(f"Drop({lcl},{i},?dropped)", dropped=lcl_drop)
            self.noSolution(f"Take({lcl},{i+1},?taken)")
            self.singleSolved(f"Drop({lcl},{i+1},?dropped)", dropped="[]")

    def test_Removed(self):
        for lcl, py in self.lists.items():
            for x in py:
                pyf = py.copy()
                pyf.remove(x)
                lclf = toLCL(pyf)
                self.singleSolved(f"Removed({x},{lcl},?without)", without=lclf)
            x = "567"
            self.noSolution(f"Removed({x},{lcl},?without)")

    def test_Appended(self):
        for lcl, py in self.lists.items():
            x = '"Apple, 5$ a share"'
            pyf = py + [x]
            lclf = toLCL(pyf)
            self.singleSolved(f"Appended({x},{lcl},?new)", new=lclf)

        self.singleSolved(f"Appended({x},[],?new)", new=f"[{x}]")

    def test_AllAnyFilter(self):
        lcl1, ls1 =("[1,2,3,4,5,6]", ["1","2",'3','4','5','6'])
        lcl2, ls2 = ("[2,4,8]", ['2','4','8'])
        lcl3, ls3 = ('["Apple","Cherry","Blueberry","Apricot","Banana"]', ['"Apple"', '"Cherry"', '"Blueberry"','"Apricot"','"Banana"'])
        lcl4, ls4 = ('["Khloe","Kate","Kim","Kourtney"]', ['"Khloe"', '"Kate"', '"Kim"', '"Kourtney"'])

        self.noSolution(f"All(Even,{lcl1})")
        self.isTrue(f"Any(Even,{lcl1})")
        self.singleSolved(f"Filter(Even,{lcl1},?x)&All(Even,?x)", x="[2,4,6]")

        self.isTrue(f"All(Even,{lcl2})")
        self.isTrue(f"Filter(Even,{lcl2},{lcl2})")

        self.noSolution('All(StartsWith{"C"},' + lcl3 + ")")
        self.isTrue('Any(StartsWith{"C"},' + lcl3 + ")")
        self.singleSolved("Filter(StartsWith{\"B\"}," + lcl3 + ",?filtered)&All(StartsWith{\"B\"},?filtered)", filtered='["Blueberry","Banana"]')

        self.isTrue("All(StartsWith{\"K\"}," + lcl4 + ")")

    def test_ConcatBreak(self):
        self.singleSolved("Break(Apple,?x)", x="[A,p,p,l,e]")
        self.noSolution("Break(,?x)")
        self.noSolution("Break(?y,?x)")

        self.singleSolved("Concat([A,p,p,l,e],?x)", x='Apple')

    def test_Map(self):
        self.singleSolved("Map(Functional1,[2,5,7],?mapped)", mapped="[3,6,8]")
        self.singleSolved("Map(Functional2,[[1,2],[3,4,7],[]],?mapped)", mapped="[[1,2,1],[3,4,7,1],[1]]")

    def test_Duplicate(self):
        self.singleSolved("Duplicate([1,2,3],5,?x)", x=toLCL(['1','2','3']*5))
        self.singleSolved("Duplicate([[]],5,?x)", x=toLCL([[]]*5))

    def test_ZipUnzip(self):
        self.singleSolved("Zip([1,2,3],[A,B,\"Charlie\"],?x)", x=toLCL(["(1/A)","(2/B)",'(3/"Charlie")']))
        self.singleSolved("Zip(?x,?y,[(1/2),(3/4),(G/H)])", x="[1,3,G]", y="[2,4,H]")
        self.singleSolved("Unzip([[1,2,3],[4,5,6,G,H],[A,B,\"Hello You There\"]],2,?x)", x='[3,6,"Hello You There"]')

    def test_AddToEach(self):
        try:
            self.singleSolved('AddToEach(T(7),[[1,2,3],[4,5,6,G,H],[A,B,"Hello You There"]],?x)', x='[[T(7)*[1,2,3]],[T(7),4,5,6,G,H],[T(7),A,B,"Hello You There"]]')
        except AssertionError:
            self.singleSolved('AddToEach(T(7),[[1,2,3],[4,5,6,G,H],[A,B,"Hello You There"]],?x)',
                              x='[[T(7),1,2,3],[T(7),4,5,6,G,H],[T(7),A,B,"Hello You There"]]')

    def test_Sublist(self):
        for lcl, py in self.lists.items():
            i = randint(0, len(py)-1)
            j = randint(i, len(py)-1)
            pyf = py[i:j]
            lclf = toLCL(pyf)
            self.singleSolved(f"Sublist({lcl},{i},{j},?sub)", sub=lclf)
            if pyf:
                self.singleSolved(f"Sublist({lcl},?i,?j,{lclf})", i=i, j=j)

    def test_Nested(self):
        self.isTrue("Nested([[]])")
        self.isTrue("Nested([[1,4,6],[A,B,\"CCC\"]])")
        self.noSolution("Nested([2,5])")
        self.noSolution("Nested(Apple)")

    def test_Unpack(self):
        self.singleSolved("Unpack([[1,2,[3]],4],?x)", x="[1,2,3,4]")

    def test_ToSet(self):
        self.singleSolved("ToSet([1,6,6,6,6],?x)", x="[1,6]")
        self.singleSolved("ToSet([A,B,\"A\"],?x)", x="[A,B,\"A\"]")

    def test_SetEquals(self):
        self.isTrue("SetEquals([1,5,4],[1,4,5])")
        self.isTrue("SetEquals([A,B,C,D],[D,B,A,C])")

    def test_SubSet(self):
        self.isTrue("SubSet([1,2,3],[1,2,3,4,5])")
        self.isTrue("SubSet([1,2,3,4,5],[1,2,3,4,5])")
        self.isTrue("ProperSubSet([1,2,3],[1,2,3,4,5])")
        self.noSolution("ProperSubSet([1,2,3,4,5],[1,2,3,4,5])")

    def test_Union(self):
        self.singleSolved("Union([1,2],[3,4],?x)", x="[1,2,3,4]")
        self.singleSolved("Union([1,2,3],[3,4,A],?x)", x="[1,2,3,4,A]")

    def test_Intersection(self):
        self.singleSolved("Intersection([1,2],[3,4],?x)", x="[]")
        self.singleSolved("Intersection([1,2,3],[3,4,A],?x)", x="[3]")
        self.singleSolved("Intersection([1,2,3],[3,1,2],?x)", x="[1,2,3]")

    def test_Choice(self):

        py = ["1","2","3","4","5","6","7"]
        pyf = []
        for i in range(len(py)):
            for j in range(i+1, len(py)):
                for k in range(j+1, len(py)):
                    pyf.append([py[i],py[j],py[k]])
        lclf = toLCL(pyf)
        lcl = toLCL(py)

        self.singleSolved(f"Choice({lcl},3,?x)", x=lclf)

    def test_PowerSet(self):
        py = ["1", "2", "A", "6","B","9"]
        lcl = toLCL(py)
        lclf = toLCL(map(list, powerset(py)))
        self.singleSolved(f"PowerSet({lcl},?p)", p=lclf)

    def test_Cartesian(self):
        py1 = ["1","2","3","4"]
        py2 = ["A","B","C"]
        pyf = []
        for a in py1:
            for b in py2:
                pyf.append([a,b])
        lclf = toLCL(pyf)
        self.singleSolved(f"Cartesian({toLCL(py1)},{toLCL(py2)},?pairs)", pairs=lclf)

    def test_Difference(self):
        self.singleSolved("Difference([1,2,3,4],[1,2],?x)", x="[3,4]")
