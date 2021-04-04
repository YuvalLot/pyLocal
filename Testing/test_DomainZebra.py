from Testing.TestingSuper import Testing


class DomainZebraTest(Testing):

    @classmethod
    def setUpClass(cls) -> None:
        data = """
        
        import List;
        import Zebra;
        
        set Child
           case Carrie
           case Elisa
           case Lynne
           case Robert;
        
        set Room
           case bathroom
           case garage
           case laundry
           case mud;
        
        domain Riddle1
           over ?c8, ?c9, ?c10, ?c11, ?r8, ?r9, ?r10, ?r11
        
           of ?c8 : Child(?c8)
           of ?c9 : Child(?c9)
           of ?c10 : Child(?c10)
           of ?c11 : Child(?c11)
        
           of ?r8 : Room(?r8)
           of ?r9 : Room(?r9)
           of ?r10 : Room(?r10)
           of ?r11 : Room(?r11)
        
           elim Repeat([?c8, ?c9, ?c10, ?c11])
           elim Repeat([?r8, ?r9, ?r10, ?r11])
        
           # Clue 1
           const Align(Carrie, bathroom, [?c8, ?c9, ?c10, ?c11], [?r8, ?r9, ?r10, ?r11])
        
           # Clue 2
           const (E(?r9, garage) | E(?r9, bathroom))
        
           # Clue 3
           const (E(?r8, bathroom) & E(?c10, Robert)) | (E(?r8, bathroom) & E(?c10, Robert))
        
           # Clue 4
           const Align(Elisa, mud, [?c8, ?c9, ?c10, ?c11], [?r8, ?r9, ?r10, ?r11]);
        
        set solve1
           case [[8, ?c8, ?r8], [9, ?c9, ?r9], [10, ?c10, ?r10], [11, ?c11, ?r11]] then
              Riddle1(?c8, ?c9, ?c10, ?c11, ?r8, ?r9, ?r10, ?r11);
        
        set Color case red case green case yellow case blue case white;
        set Nation case Brit case Swede case Dane case Norwegian case German;
        set Beverage case milk case tea case coffee case beer case water;
        set Smokes case pallmall case dunhill case blends case prince case bluemaster;
        set Pet case dog case bird case fish case horse case cat;
        
        domain EinsteinRiddle
           over ?c1, ?n1, ?b1, ?s1, ?p1,
                ?c2, ?n2, ?b2, ?s2, ?p2,
                ?c3, ?n3, ?b3, ?s3, ?p3,
                ?c4, ?n4, ?b4, ?s4, ?p4,
                ?c5, ?n5, ?b5, ?s5, ?p5
        
           of ?c1 : Color(?c1)
           of ?n1 : Nation(?n1)
           of ?b1 : Beverage(?b1)
           of ?s1 : Smokes(?s1)
           of ?p1 : Pet(?p1)
        
           of ?c2 : Color(?c2)
           of ?n2 : Nation(?n2)
           of ?b2 : Beverage(?b2)
           of ?s2 : Smokes(?s2)
           of ?p2 : Pet(?p2)
        
           of ?c3 : Color(?c3)
           of ?n3 : Nation(?n3)
           of ?b3 : Beverage(?b3)
           of ?s3 : Smokes(?s3)
           of ?p3 : Pet(?p3)
        
           of ?c4 : Color(?c4)
           of ?n4 : Nation(?n4)
           of ?b4 : Beverage(?b4)
           of ?s4 : Smokes(?s4)
           of ?p4 : Pet(?p4)
        
           of ?c5 : Color(?c5)
           of ?n5 : Nation(?n5)
           of ?b5 : Beverage(?b5)
           of ?s5 : Smokes(?s5)
           of ?p5 : Pet(?p5)
        
           elim Repeat(?nations)
           elim Repeat(?colors)
           elim Repeat(?pets)
           elim Repeat(?beverages)
           elim Repeat(?smokes)
        
           # The Brit lives in a red house.
           const Align(Brit, red, ?nations, ?colors)
           # The Swede keeps dogs as pets.
           const Align(Swede, dog, ?nations, ?pets)
           # The Dane drinks tea.
           const Align(Dane, tea, ?nations, ?beverages)
           # The Green house is next to, and on the left of the White house.
           const ExactlyLeft(green, white, ?colors, ?colors)
           # The owner of the Green house drinks coffee.
           const Align(green, coffee, ?colors, ?beverages)
           # The person who smokes Pall Mall rears birds.
           const Align(pallmall, bird, ?smokes, ?pets)
           # The owner of the Yellow house smokes Dunhill
           const Align(yellow, dunhill, ?colors, ?smokes)
           # The man living in the centre house drinks milk
           const E(?b3, milk)
           # The Norwegian lives in the first house.
           const E(?n1, Norwegian)
           # The man who smokes Blends lives next to the one who keeps cats.
           const NextTo(blends, cat, ?smokes, ?pets)
           # The man who keeps horses lives next to the man who smokes Dunhill.
           const NextTo(horse, dunhill, ?pets, ?smokes)
           # The man who smokes Blue Master drinks beer.
           const Align(bluemaster, beer, ?smokes, ?beverages)
           # The German smokes Prince.
           const Align(German, prince, ?nations, ?smokes)
           # The Norwegian lives next to the blue house.
           const NextTo(Norwegian, blue, ?nations, ?colors)
           # The man who smokes Blends has a neighbour who drinks water.
           const NextTo(blends, water, ?smokes, ?beverages);
        
        set Nice
           case ?fish_owner then
              EinsteinRiddle(?c1, ?n1, ?b1, ?s1, ?p1,
                   ?c2, ?n2, ?b2, ?s2, ?p2,
                   ?c3, ?n3, ?b3, ?s3, ?p3,
                   ?c4, ?n4, ?b4, ?s4, ?p4,
                   ?c5, ?n5, ?b5, ?s5, ?p5) &
              Align(?fish_owner, fish, [?n1, ?n2, ?n3, ?n4, ?n5], [?p1, ?p2, ?p3, ?p4, ?p5]);
        
        <subs>
        
        ?nations >> [?n1, ?n2, ?n3, ?n4, ?n5]
        ?colors >> [?c1, ?c2, ?c3, ?c4, ?c5]
        ?beverages >> [?b1, ?b2, ?b3, ?b4, ?b5]
        ?smokes >> [?s1, ?s2, ?s3, ?s4, ?s5]
        ?pets >> [?p1, ?p2, ?p3, ?p4, ?p5]
        
        </subs>
        """

        cls.compiler = cls.upload(data)

    def test_riddle1(self):
        self.singleSolved("solve1(?x)", x="[[8,Carrie,bathroom],[9,Lynne,garage],[10,Robert,laundry],[11,Elisa,mud]]")

    def test_riddel2(self):
        self.singleSolved("Nice(?x)", x="German")
