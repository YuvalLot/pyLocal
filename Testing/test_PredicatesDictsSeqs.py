
import Testing.TestingSuper


class PredsDictsSeqs(Testing.TestingSuper.Testing):

    @classmethod
    def setUpClass(cls) -> None:
        data = """
        
        import Predicates;
        import Dictionary;
        import Sequences;
        import List;
        import Save;
        
        set C
            case Apple, Orange
            case Dog, Elephant;
        
        set A
            case Apple
            case Dog;
        
        package AddC{?x}
            case ?a, ?b then Add(?a, ?x, ?b);
        
        package NextApx{?n} # The next approximation of square root
            case ?x, ?y then Div(?n, ?x, ?c1) & Add(?x, ?c1, ?c2) & Div(?c2, 2, ?y);
        
        set B
            case Apple
            case Orange;
            
        set Libi
            case Name, "Libi"
            case LastName, "Kotchubievsky"
            case Age, 17
            case Friends, ["Yuval", "Hadar"]
            case Location, "Ra'anana";
        
        package NextApx{?n} # The next approximation of square root
           case ?x, ?y then Div(?n, ?x, ?c1) & Add(?x, ?c1, ?c2) & Div(?c2, 2, ?y);
        
        set Sqrt (* Iterate Approximations 11 times *)
           case ?x, ?y then Iterates(1, NextApx{?x}, ?seq) & DropSeq(?seq, 10, ?n)
                          & HdSeq(?n, ?y);
        
        package NotDivisible{?n}
            case ?x then Mod(?x, ?n, ?r) & ~E(?r, 0);
        
        package Primes{?seq}
            case ?p, ?next then ?seq(?p, ?nextUnfiltered) & FilterSeq(?nextUnfiltered, NotDivisible{?p}, ?almost)
                              & E(?next, Primes{?almost});
        
        set Squared
            case ?x, ?y then Mul(?x, ?x, ?y);
        
        """

        cls.compiler = cls.upload(data)

    def test_Preds_PatternToList(self):
        self.noSolution("C([?x,?y])")
        self.multipleSolved("C(%[?x,?y])", x=("Apple","Dog"),y=("Orange","Elephant"))
        self.multipleSolved("PatternToList(C,?p)&?p([?x,?y])", x=("Apple","Dog"), y=("Orange","Elephant"),
                            not_care=("?p",))

    def test_Preds_Repeat(self):
        self.singleSolved("Repeat(4,AddC{3},4,?y)", y=str(4+3*4))
        sols = list(self.compiler.mixed_query("Repeat(20,NextApx{5},4,?y)", 0, 10000, True))
        self.assertEqual(len(sols), 1)
        self.assertAlmostEqual(float(sols[0]["?y"])**2, 5, places=4)

    def test_Preds_AndOrNot(self):
        self.multipleSolved("And(A,B,?C)&?C(?x)", not_care=("?C",), x=("Apple",))
        self.multipleSolved("Or(A,B,?C)&?C(?x)", not_care=("?C",), x=("Apple","Dog","Orange"))
        self.multipleSolved("AndNot(A,B,?C)&?C(?x)", not_care=("?C",), x=("Dog",))
        self.multipleSolved("LazyOr(A,B,?C)&?C(?x)", not_care=("?C",), x=("Apple","Dog"))
        self.multipleSolved("LazyOr(B,A,?C)&?C(?x)", not_care=("?C",), x=("Apple","Orange"))
        self.multipleSolved("LazyOr(NextApx{4},A,?C)&?C(?x)", not_care=("?C",), x=("Apple","Dog"))

    def test_Preds_Compound(self):
        self.multipleSolved("Compound(AddC{4},AddC{8},?x)&?x(4,?y)", not_care=("?x",), y=(str(4+4+8),))

    def test_Preds_Feed(self):
        self.singleSolved("Feed(Join,[[1,2,3],[4,5,6],[7,8,9]],[],?r)", r="[7,8,9,4,5,6,1,2,3]")

    def test_Dicts_AddDict(self):
        self.multipleSolved("AddDict(Libi,nLastNames,2,?new)&?new(nLastNames,?x)&Save(?new)", not_care=("?new",), x=("2",))
        self.multipleSolved('Load(?new)&AddDict(?new,Studies,"To Fart",?newer)&?newer(Studies,?x)&?newer(nLastNames,?y)', not_care=("?new","?newer"), x=('"To Fart"',), y=("2",))

    def test_Dicts_ToDictionary(self):
        self.solved("ListsToDictionary([Name,Location,Job,Favorite_TV],[Yuval,Israel,Student,Friends],?d)&Save(?d)")
        self.multipleSolved("Load(?d)&?d(Job,?x)", not_care=("?d",), x=("Student",))

        self.solved("PairsToDictionary([[Name,Yuval],[Location,Israel],[Job,Student],[Fav_TV,Friends]],?d)&Save(?d)")
        self.multipleSolved("View(?d)&?d(Job,?x)", not_care=("?d",), x=("Student",))
        self.multipleSolved("View(?d)&Keys(?d,?keys)", not_care=("?d",), keys=("[Name,Location,Job,Fav_TV]",))
        self.multipleSolved("View(?d)&Values(?d,?keys)", not_care=("?d",), keys=("[Yuval,Israel,Student,Friends]",))
        self.multipleSolved("View(?d)&DictToPairs(?d,?keys)", not_care=("?d",), keys=("[[Name,Yuval],[Location,Israel],[Job,Student],[Fav_TV,Friends]]",))

    def test_Dicts_Unite(self):
        self.solved("PairsToDictionary([[Name,Yuval],[Location,Israel],[Job,Student],[Fav_TV,Friends]],?d1)" +
                    "&ListsToDictionary([Last,Friend,Name],[Lot,Libi,Amir],?d2)&Unite(?d1,?d2,?d)&Save(?d)")
        self.multipleSolved("View(?d)&?d(?x,Lot)", not_care=("?d",), x=("Last",))
        self.multipleSolved("View(?d)&?d(Name,?x)", not_care=("?d",), x=("Yuval",))

    def test_Seq_General(self):
        self.solved("Save(From{10})")
        self.solved("From{10}(?x,From{11})")
        self.resulted("HdSeq(From{10},?x)", "?x", "10")
        self.singleSolved("TlSeq(From{10},?x)&?x(?y,?z)", x="From{11}", y="11", z="From{12}")
        self.singleSolved("TakeSeq(From{-6},10,?x)", x="[-6,-5,-4,-3,-2,-1,0,1,2,3]")
        self.singleSolved("DropSeq(From{-6},10,?x)", x="From{4}")
        self.multipleSolved("Cons(Apple,From{6},?x)&Next(?x,?item,?seq)", not_care=("?x",), item=("Apple",), seq=("From{6}",))

    def test_Seq_ToFromList(self):
        self.solved("FromList([Apple,Orange,Banana],?seq)&Save(?seq)")
        self.solved("Load(?seq)&JoinSeq(?seq,From{60},?newSeq)&Save(?newSeq)")
        self.multipleSolved("View(?seq)&TakeSeq(?seq,5,?list)", not_care=("?seq",), list=("[Apple,Orange,Banana,60,61]",))
        self.multipleSolved("FromList([Apple,Orange,Banana],?seq)" +
                            "&FromList([1,5],?seq2)&JoinSeq(?seq,?seq2,?final)&ToList(?final,?list)",
                            not_care=("?seq","?seq2","?final"), list=("[Apple,Orange,Banana,1,5]",))

    def test_Seq_Iterates(self):
        sols = list(self.compiler.mixed_query("Sqrt(7,?x)", 0, 10000, True))
        self.assertEqual(len(sols), 1)
        self.assertAlmostEqual(float(sols[0]["?x"])**2, 7, 2)

    def test_Seq_Filter(self):
        self.singleSolved("TakeSeq(Primes{From{2}},10,?x)", x="[2,3,5,7,11,13,17,19,23,29]")

    def test_Seq_Map(self):
        self.multipleSolved("MapSeq(From{1},Squared,?seq)&TakeSeq(?seq,5,?xs)", not_care=("?seq",), xs=("[1,4,9,16,25]",))

    def test_Seq_Map(self):
        self.multipleSolved("Series(From{1},?ser)&TakeSeq(?ser,5,?xs)", not_care=("?ser",), xs=("[1,3,6,10,15]",))



