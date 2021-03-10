"""

Lexer

Build returns a reader of tokens.

"""

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
    'bundle': 'BUNDLE'
}

# tokens
tokens = [
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
 ] + list(reserved.values())

# set regular expressions for tokens
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


# build the lexer
def build():
    global line
    line = 1
    lexer = lex.lex()
    return lexer


if __name__ == "__main__":
    l = build()
    l.input("""
    
    import Math;

    set on-start
        case then Print("hello");
    
    """)
    ts = []
    while True:
        tk = l.token()
        if not tk:
            break
        print(tk)
    print(SyntaxErrors)