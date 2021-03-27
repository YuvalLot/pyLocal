"""

Lexer

Build returns a reader of tokens.

"""
import re

import ply.lex as lex


SyntaxErrors = []
line = 1

# reserved words
reserved = {
    'set': 'SET',
    'extend': 'EXTEND',
    'case': 'CASE',
    'then': 'THEN',
    'package': 'PACKAGE',
    'NOT':'NOT',
    'as': 'AS',
    'import': 'IMP',
    'use': 'USE',
    'declare': 'DECLARE',
    'infix': 'INFIX',
    'ALL': 'ALL',
    'connect': 'CON',
    'bundle': 'BUNDLE',
    'domain': 'DOMAIN',
    'over': 'OVER',
    'elim': 'ELIM',
    'of': 'OF',
    'const': 'CONST',
    'final': 'FINAL',
    'when': 'WHEN',
}

# tokens
tokens = [
    'PYTHON',
    'ARROW',
    'CUT',
    'EXCLAMATION',
    'STRING',
    'EQ',
    'FILENAME',
    'FILTER',
    'AND',
    'OR',
    'LBRACKET',
    'RBRACKET',
    'LPAREN',
    'RPAREN',
    'LCURLY',
    'RCURLY',
    'COMMA',
    'NAME',
    'VARIABLE',
    'COLON',
    'SEMI',
    'HEAD',
    'XOR',
    'FOLD',
    'NEWLINE',
    'OP',
    'PLUS',
    'MULTILINECOMMENT',
    'SUBS',
 ] + list(reserved.values())

# set regular expressions for tokens
t_ARROW = r'>>'
t_CUT = r'\-cut\-'
t_EXCLAMATION = r'\!'
t_COLON = r':'
t_EQ = r'='
t_FILTER = r'~'
t_AND = r'&'
t_OR = r'\|'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACKET = r'\['
t_RBRACKET = r'\]'
t_LCURLY = r'\{'
t_RCURLY = r'\}'
t_COMMA = r','
t_SEMI = r';'
t_HEAD = r'\*'
t_XOR = r'\$'
t_FOLD = r'%'
t_OP = r'\^[^;^ ^,^\n]+'
t_PLUS = r'\+'


# multi-lined comments
def t_MULTILINECOMMENT(t):
    r'(\(\*(.|\n)*?\*\))'
    t.value = t.value.count("\n")
    global line
    try:
        line += t.value
    except UnboundLocalError:
        pass
    return t

def t_PYTHON(t):
    r'<python>(.|\n)+</python>'
    return t

def t_SUBS(t):
    r'<subs>(.|\n)*</subs>'
    return t

# Filename token
def t_FILENAME(t):
    r'@[a-zA-Z_0-9\-\.\\\/: ]+'
    t.type = 'FILENAME'
    t.value = t.value[1:]
    return t


# String token
def t_STRING(t):
    r'"[^"]*"'
    t.type = 'STRING'
    t.value = t.value.replace("\\n", "\n").replace("\\t", "\t")
    return t


# New line token
def t_NEWLINE(t):
    r'\n'
    global line
    t.value = "\n"
    line += 1
    return t


# match with a variable
def t_VARIABLE(t):
    r'\?[a-zA-Z_0-9\-\.]+'
    t.type = 'VARIABLE'
    return t


# match with a name (constant or reserved words)
def t_NAME(t):
    r'[a-zA-Z_0-9\-\.]+'
    t.type = reserved.get(t.value, 'NAME')
    return t


# error
def t_error(t):
    SyntaxErrors.append(f"Syntax Error: Illegal token {t.value[0]}, line {line}")
    t.lexer.skip(1)


t_ignore = ' \t'
t_ignore_COMMENT = r'(\#.*)'



class PreProcessor:

    def __init__(self):
        self.lex = lex.lex()

    def input(self, data:str):
        a = re.search(r'<subs>(.|\n)+</subs>', data)
        if a:
            subs1 = {}
            subs2 = {}
            temp_index = 0
            s = a.string
            for (org, to) in re.findall(r"(.+)>>(.+)", s):
                org = org.strip()
                to = to.strip()
                temp = f"`{temp_index}`"
                temp_index += 1
                subs1[org] = temp
                subs2[temp] = to
            for key, value in subs1.items():
                data = data.replace(key, value)
            for key, value in subs2.items():
                data = data.replace(key, value)
        self.lex.input(data)

    def token(self):
        return self.lex.token()


# build the lexer
def build():
    global line
    line = 1
    return PreProcessor()


if __name__ == "__main__":
    l = PreProcessor()
    l.input("""
    
<subs>

?nations >> [?n1, ?n2, ?n3, ?n4, ?n5]
?colors >> [?c1, ?c2, ?c3, ?c4, ?c5]
?beverages >> [?b1, ?b2, ?b3, ?b4, ?b5]
?smokes >> [?s1, ?s2, ?s3, ?s4, ?s5]
?pets >> [?p1, ?p2, ?p3, ?p4, ?p5]

</subs>

import List;
import @riddle_tools;

(*

Prompt:
A. In a street there are five houses, painted five different colors.
B. In each house lives a person of different nationality
C. These five homeowners each drink a different kind of beverage, smoke different brand of cigar and keep a different pet.

Hints:
1. The Brit lives in a red house.
2. The Swede keeps dogs as pets.
3. The Dane drinks tea.
4. The Green house is next to, and on the left of the White house.
5. The owner of the Green house drinks coffee.
6. The person who smokes Pall Mall rears birds.
7. The owner of the Yellow house smokes Dunhill.
8. The man living in the centre house drinks milk.
9. The Norwegian lives in the first house.
10. The man who smokes Blends lives next to the one who keeps cats.
11. The man who keeps horses lives next to the man who smokes Dunhill.
12. The man who smokes Blue Master drinks beer.
13. The German smokes Prince.
14. The Norwegian lives next to the blue house.
15. The man who smokes Blends has a neighbour who drinks water.

Question: Who owns the fish?

*)

set Color case red case green case yellow case blue case white;
set Nation case Brit case Swede case Dane case Norwegian case German;
set Beverage case (*almond*)milk case tea case coffee case beer case water;
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

   const OneOf(Brit, red, ?nations, ?colors)
   const OneOf(Swede, dog, ?nations, ?pets)
   const OneOf(Dane, tea, ?nations, ?beverages)
   const ExactlyLeft(green, white, ?colors, ?colors)
   const OneOf(green, coffee, ?colors, ?beverages)
   const OneOf(pallmall, bird, ?smokes, ?pets);

    
    """)
    ts = []
    while True:
        tk = l.token()
        if not tk:
            break
        ts.append(tk)
    print(SyntaxErrors, ts)
