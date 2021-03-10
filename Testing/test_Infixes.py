
import Testing.TestingSuper


class InfixesTest(Testing.TestingSuper.Testing):

    @classmethod
    def setUpClass(cls) -> None:
        data = """

        import Math;
        
        infix ^+, ^-, ^*, ^/, ^app;
        
        set Eval as recursive
           case (?a ^+ ?b), ?c then Eval(?a, ?ea) & Eval(?b, ?eb)
                               & Add(?ea, ?eb, ?c)
           case (?a ^- ?b), ?c then Eval(?a, ?ea) & Eval(?b, ?eb)
                               & Sub(?ea, ?eb, ?c) 
           case (?a ^* ?b), ?c then Eval(?a, ?ea) & Eval(?b, ?eb)
                               & Mul(?ea, ?eb, ?c) 
           case (?a ^/ ?b), ?c then Eval(?a, ?ea) & Eval(?b, ?eb)
                               & Div(?ea, ?eb, ?c) 
           case ?x, ?x then E(1,1);

        set AppendEval
            case ([] ^app ?xs), ?xs
            case ([?x*?xs] ^app ?ys), [?x*?zs] then AppendEval(?xs ^app ?ys, ?zs);
        
        """

        cls.compiler = cls.upload(data)

    def test_Math_Infixes(self):
        self.singleSolved("Eval(3^+4,?x)", x="7")
        self.singleSolved("Eval(3^-4,?x)", x="-1")
        self.singleSolved("Eval(3^*4,?x)", x="12")
        self.singleSolved("Eval(12^/4,?x)", x="3")

        self.noSolution("Eval((?y^+?z)^/2^*(?g^+?h),?x)")

        self.multipleSolved("E(?y,4)&E(?z,8)&E(?g,3)&E(?h,9)" +
                            "&Eval((?y^+?z)^/2^*(?g^+?h),?x)", not_care=("?y", "?z", "?g", "?h"), x=("72",))

    def test_Append_Infix(self):
        self.singleSolved("AppendEval([1,2,3,4]^app[4,5,6],?x)", x="[1,2,3,4,4,5,6]")
