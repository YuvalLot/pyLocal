
import Testing.TestingSuper


class BackChainingTest(Testing.TestingSuper.Testing):

    @classmethod
    def setUpClass(cls) -> None:

        data = """
        
        (*
        
        hellllllooo
        
        *)
        
        import Strings;
        import List;
        
        (*
        
        COMMENT AFTER IMPORT
        
        *)
        
        
        set Father
            case (Abraham, Isaac)
            case (Isaac, Jacob)
            case (Isaac, Esau)
            case (Jacob, Joseph)
            case (Jacob, Judah);
            
        set Mother
            case (Sarah, Isaac)
            case (Rebecca, Jacob)
            case (Rebecca, Esau)
            case (Rachel, Joseph);
        
        package StartsWith{?c}
            case ?x then Chars(?x, [?c * ?xs]);
        
        set Grandfather
            case (?x, ?y) then Father(?x, ?z) & Father(?z, ?y);
        
        set Partners
            case (?x, ?y) then Father(?x, ?z) & Mother(?y, ?z);  
        
        set Brothers
            case (?x, ?y) then Father(?z, ?x) & Father(?z, ?y);
            
        set True
            case ;
        
        set False;
        
        set A
            case 1;
        
        extend A
            case 2
            case ?x then Father(?x, ?y);
        
        """

        cls.compiler = cls.upload(data)

    def test_Father(self):

        query = "Father(?x,?y)"
        expected = [{"?x":"Abraham", "?y":"Isaac"},
                    {"?x":"Isaac","?y":"Jacob"},
                    {"?x":"Isaac", "?y":"Esau"},
                    {"?x":"Jacob", "?y":"Joseph"},
                    {"?x":"Jacob", "?y":"Judah"}]

        self.generic(query, expected)

    def test_Mother(self):
        query = "Mother(?x,?y)"
        expected = [{"?x": "Sarah", "?y": "Isaac"},
                    {"?x": "Rebecca", "?y": "Jacob"},
                    {"?x": "Rebecca", "?y": "Esau"},
                    {"?x": "Rachel", "?y": "Joseph"}]

        self.generic(query, expected)


    def test_Grandfather(self):
        query = "Grandfather(?x,?y)"
        expected = [{"?x":"Abraham", "?y":"Jacob"},
                    {"?x":"Abraham", "?y":"Esau"},
                    {"?x":"Isaac", "?y":"Joseph"},
                    {"?x":"Isaac", "?y":"Judah"}]

        self.generic(query, expected)

    def test_Print(self):
        query = "Print(4,6,NL)"
        self.generic(query, ["Print",{}])

    def test_Packages(self):

        query = 'Filter(StartsWith{?c},["apple","apricot","orange"],["apple","apricot"])'
        self.singleSolved(query, c='"a"')

    def test_Empty(self):
        self.isTrue("True()")
        self.noSolution("False()")

    def test_Extend(self):
        self.isTrue("A(1)")
        self.isTrue("A(2)")
        self.isTrue("A(Abraham)")