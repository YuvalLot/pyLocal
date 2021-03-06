"""

Tools

includes a lot of different functions used in the project

"""

from func_timeout import func_timeout, FunctionTimedOut
from types import GeneratorType
import re


# Splits a string into parts according to a splitter
def splitWithoutParen(string, splitter=","):
    """
    Splits a string based on a splitter.

    :param string: str
    :param splitter: str (singlie charecter)
    :return: list of str

    """
    elements = []
    current_element = ''
    current_paren = 0
    inQuote = False
    for char in string:
        if char == "\"":
            inQuote = not inQuote
        if char in "([{" and not inQuote:
            current_paren += 1
            current_element += char
        elif char in ")]}" and not inQuote:
            current_paren -= 1
            current_element += char
        elif char == splitter and not inQuote:
            if current_paren == 0:
                elements.append(current_element)
                current_element = ''
            else:
                current_element += char
        else:
            current_element += char

    return elements + [current_element] if current_element != '' else elements


# finds if a char is in a string outside of parentheses
def smartIn(string, find):
    """
    Finds if a char is in a string outside of parentheses

    :param string: str
    :param find: str (single character)
    :return: boolean
    """
    count = 0
    inQuote = False
    for char in string:
        if char == "\"":
            inQuote = not inQuote
        if char == find and count < 2 and not inQuote:
            return True
        if char in "([{" and not inQuote:
            count += 1
        if char in ")]}" and not inQuote:
            count -= 1
    return False


# finds the type of component
def match_type(pattern):
    """
    Returns the match type ("constant", "var", "head" (headed list), "list" (expanded list), "title", "pack", "pair")

    >>> match_type("Apple")
    'constant'

    >>> match_type("?x")
    'var'

    >>> match_type('[3 * ?x]')
    'head'

    >>> match_type("[1,2,3,4,?x,?y]")
    'list'

    >>> match_type("G{?a,?b}")
    'pack'

    >>> match_type("Branch(?v,?t1,?t2)")
    'title'

    :param pattern: str
    :return: str
    """
    if "/" in pattern and pattern[0] == "(" and pattern[-1] == ")":
        parts = splitWithoutParen(pattern[1:-1], "/")
        if len(parts) == 2 and parts[0][-1] != "^":
            return "pair"
    if pattern[0] == "\"" and pattern[-1] == "\"":
        return 'constant'
    if pattern[-1] == "}":
        return 'pack'
    if pattern[0] == "?":
        return 'var'
    if "(" in pattern and pattern[0] != "(" and pattern[-1] == ")":
        return 'title'
    if '[' in pattern and smartIn(pattern, "*") and "<" not in pattern:
        return 'head'
    if '[' in pattern and "<" not in pattern:
        return 'list'
    return 'constant'


# removes bracket from lists
def remove_bracket(string):
    """
    Removes (if necessary) brackets.

    :param string: str
    :return: str
    """
    count = 0
    inQ = False
    for i, c in enumerate(string):
        if c == '"':
            inQ = not inQ
        if c == "[" and not inQ:
            count += 1
        if c == "]" and not inQ:
            count -= 1
        elif count == 0 and len(string) != i+1:
            return string
    if string[0] == "[" and string[-1] == "]":
        return string[1:-1]
    return string


# Extends two Lists as sets
def smartExtend(A, B):
    """
    merges two lists into one.

    :param A: list
    :param B: list
    :return: list
    """
    C = A.copy()
    for b in B:
        if b not in C:
            C.append(b)
    return C


# Gets the basic components in a list
def get_all_basics(_list, splitter=","):
    """
    Gets all the basic components of a datatype, including lists, packages, titles.

    >>> get_all_basics("[1,?x,[?z,[?t * ?ts]]]")
    ['1','?x','?z','?t','?ts']

    >>> get_all_basics("plus(minus(9,4),times(3,1.2))")
    ['9','4','3','1.2']

    :param _list: str
    :param splitter: str (character to split by, used to differentiate between lists and heads)
    :return: list
    """
    if _list == "":
        return []

    t = (splitter == "/" and "pair") or match_type(_list)

    if t == "pair":
        _list = _list[1:-1]
        a, b = splitWithoutParen(_list, "/")
        return list(set(get_all_basics(a) + get_all_basics(b)))

    if t == 'title':
        t_name, _, t_pat = _list.partition("(")
        t_pat = t_pat[:-1]
        if t_pat == "":
            return []

    if t == 'pack':
        package_name, _, package_param = _list.partition("{")
        package_param = package_param[:-1]
        return get_all_basics("["+package_param+"]")

    _list = remove_bracket(_list)
    components = splitWithoutParen(_list, splitter)
    basic_components = []
    for comp in components:
        t = match_type(comp)
        if t in ['var', 'constant']:
            basic_components.append(comp)
        else:
            if t == 'list':
                basic_components = smartExtend(basic_components, get_all_basics(comp))
            if t == 'head':
                basic_components = smartExtend(basic_components, get_all_basics(comp, "*"))
            if t == 'title':
                _, _, param = comp.partition("(")
                param = param[:-1]
                basic_components = smartExtend(basic_components, get_all_basics(param))
            if t == "pack" or t == "pair":
                basic_components = smartExtend(basic_components, get_all_basics(comp))
    return list(set(basic_components))


# replaces variables with other variables/constants/lists
def smart_replace(string, replace_dict):
    """
    Replaces all variables in a string based on a forward dictionary (or solution)

    :param string: str
    :param replace_dict: dict
    :return: str
    """

    if "..." in replace_dict:
        string = string.replace("...", replace_dict["..."])

    current_var = ""
    new_s = ""
    inQuote = False
    ending_chars = [
        "?",
        ")",
        ".",
        ",",
        "]",
        "*",
        "(",
        "{",
        "}",
        "^",
        "\"",
        ">",
        " ",
        "\'",
        "!",
        '%',
        '&',
        '|',
        '$',
        ":",
        "/"
    ]
    for c in string:

        if c == "\"":
            inQuote = not inQuote

        if c == "?":
            if current_var:
                if current_var == "?":
                    pass
                else:
                    addition = replace_dict.get(current_var, current_var)
                    new_s += addition
                    current_var = ""
            current_var += "?"
        elif c in ending_chars and current_var:
            addition = replace_dict.get(current_var, current_var)
            new_s += addition
            new_s += c
            current_var = ""
        elif current_var:
            current_var += c
        else:
            new_s += c

    if current_var:
        addition = replace_dict.get(current_var, current_var)
        new_s += addition

    return new_s


# Checks if parentheses are legal and if any can be removed
def processParen(string: str):
    """
    Processes an expression in terms of regular parentheses

    :param string: str
    :return: False (if the string has illegal parentheses), str
    """
    if len(string) == 0:
        return string

    lcount = 0
    rcount = 0
    inQuote = False
    for c in string:
        if c == "\"":
            inQuote = not inQuote
        if c == "(" and not inQuote:
            lcount += 1
        if c == ")" and not inQuote:
            rcount += 1

    if lcount != rcount or inQuote:
        return False

    enclosed = False
    if string[0] == "(" and string[-1] == ")":
        enclosed = True
        cnt = 1
        for char in string[1:]:
            if cnt == 0:
                enclosed = False
            if char == "\"":
                inQuote = not inQuote
            if char == "(" and not inQuote:
                cnt += 1
            if char == ")" and not inQuote:
                cnt -= 1
    if enclosed and match_type(string) != "pair":
        string = string[1:-1]
        string = processParen(string)
    return string


# Process a head list (e.g. [1*[1,2]] -> [1,1,2])
def processHead(string: str):
    """
    Processes a head variable (if it can be simplified)

    >>> processHead("[1*[1,2]]")
    "[1,1,2]"

    :param string: str
    :return: str
    """
    mt = match_type(string)

    if mt == "pack":
        return string
    if mt == 'list':
        string = string[1:-1]
        components = splitWithoutParen(string, ',')
        processed_comps = []
        for comp in components:
            processed_comps.append(processHead(comp))
        if None in processed_comps:
            return None
        return "[" + ",".join(processed_comps) + "]"
    if mt == 'title':
        if "*" not in string:
            return string
        title_name, _, t_pat = string.partition("(")
        t_pat = t_pat[:-1]
        processed_comps = []
        for comp in splitWithoutParen(t_pat):
            processed_comps.append(processHead(comp))
        if None in processed_comps:
            return None
        return title_name + "(" + ",".join(processed_comps) + ")"
    if mt != 'head':
        return string

    string = string[1:-1]
    hd, tail = splitWithoutParen(string, "*")

    hd = processHead(hd)

    tail_type = match_type(tail)
    if tail_type in ["list", "head"]:
        tail = processHead(tail)
        if tail is None:
            return
        tail_type = match_type(tail)

    if tail_type == 'list':
        if tail == "[]":
            return f"[{hd}]"
        return f"[{hd},{tail[1:-1]}]"
    if tail_type == 'head' or tail_type == 'var' or tail == "_":
        return f"[{hd}*{tail}]"


# Deletes breaks from Queries
def processQuery(string:str):
    """
    Formats queries to Local Language

    :param string: str
    :return: str
    """
    withe = 0

    string = string.replace("\\n", "\n").replace("\\t", "\t")

    if re.fullmatch(r'\bwith\b', string):
        parts = string.split('with')
        if len(parts) != 2:
            return False
        assertive = parts[1].strip()
        if assertive == 'assertions':
            string = parts[0]
            withe = 1

    s = ""
    inString = False
    for char in string:
        if char == "@" and not inString:
            return False
        if char == "#" and not inString:
            break
        if char == '"':
            inString = not inString
        if char in " \t" and not inString:
            continue
        s += char

    if inString:
        return False

    return withe, s


# Pattern includes variables
def independent(string):
    """
    Whether has variables.
    The reason this exists is because I might make it more sophisticated at some point, not just "?" in string

    :param string: str
    :return: boolean
    """
    return outString(string, "?")


# Processes solution and makes into a string
def processSolutionDict(sol_dict):
    """
    Solution dict to nice string
    {"?x":"5", "?y":7} ----->
    ?x <- 5
    ?y <- 7

    :param sol_dict: dict
    :return: str
    """

    if sol_dict == {}:
        return {}

    if sol_dict == "Request":
        return "Request"
    if sol_dict == "Print":
        return "Print"

    variable_count = {}

    for key in sol_dict.keys():
        if key[1] == "@" or key[0] != "?":
            continue
        t = match_type(sol_dict[key])
        if t == "constant":
            continue
        if t == "var":
            if sol_dict[key] in variable_count.keys():
                variable_count[sol_dict[key]] += 1
            else:
                variable_count[sol_dict[key]] = 1
        if t in ["list", "head", 'title', 'pair']:
            sol_dict[key] = processHead(sol_dict[key])
            t = match_type(sol_dict[key])
            basic_comps = get_all_basics(sol_dict[key], {"list":",", "head":"*", 'title':",", 'pair':"/"}[t])
            for comp in basic_comps:
                tb = match_type(comp)
                if tb == "constant":
                    continue
                if tb == "var":
                    if comp in variable_count.keys():
                        variable_count[comp] += 1
                    else:
                        variable_count[comp] = 1

    variable_replacing = {}
    i = 1
    for var in variable_count.keys():
        if variable_count[var] > 1:
            variable_replacing[var] = f" _{i} "
            i += 1
        else:
            variable_replacing[var] = " _ "

    final_sol = {}
    for key in sol_dict.keys():
        if key[1] == "@" or key[0] != "?":
            continue
        final_sol[key] = smart_replace(sol_dict[key], variable_replacing)
        if final_sol[key][0] == '"':
            final_sol[key] = final_sol[key].replace("\n", "\\n")
            final_sol[key] = final_sol[key].replace("\t", "\\t")

    s_final = ''
    for key in final_sol.keys():
        s_final += f"{key} ??? {final_sol[key]}\n"

    return s_final[:-1]


# updates two dictionaries in a way that makes sense
def smartUpdate(d1, d2):
    """
    updates two dictionaries in a way that fits local.
    Using the information of both dictionaries to make conclusions about values and keys.

    :param d1: dict
    :param d2: dict
    :return: dict
    """

    d = {}
    for key in d1:
        d[key] = smart_replace(d1[key], d2)

    d.update(d2)
    return d


# generates next solution given a generator, with time limit
def next_solution(solution_gen, limit):
    """
    Finds next solution of generator within time limit

    :param solution_gen: generator
    :param limit: number
    :return: dict
    """
    if type(solution_gen) != GeneratorType:
        return 0
    try:
        sol = func_timeout(limit, next, (solution_gen,), {})
        return sol
    except StopIteration:
        return 0
    except FunctionTimedOut:
        return 1
    except RecursionError:
        return 3

    return 2


# Formats for printing in console
def formatPrint(x:str):
    """
    Formats it as it should be printed

    :param x: str
    :return: str
    """
    if x == "NL":
        return "\n"
    t = match_type(x)
    if t == 'constant':
        if x[0] == "\"" and x[-1] == "\"":
            x = x[1:-1]
            x = x.replace("??", "?")
        return x
    if t == 'var':
        return 'Unknown'
    x = processHead(x)
    t = match_type(x)
    if t == 'list' or t == 'title' or t == "pair":
        r_dict = {}
        basics = get_all_basics(x)
        for key in basics:
            t2 = match_type(key)
            if t2 == "var":
                r_dict[key] = 'Unknown'
        return smart_replace(x, r_dict)
    if t == 'head':
        r_dict = {}
        basics = get_all_basics(x, "*")
        for key in basics:
            t2 = match_type(key)
            if t2 == "var":
                r_dict[key] = 'Unknown'
        return smart_replace(x, r_dict)


# Gets a string of components "1,2,%[1,2]" -> "1,2,1,2"
def unfold(string:str):
    """
    Unfolds lists.

    :param string: str
    :return: str (if can be folded), False
    """
    if "%" not in string:
        return string

    comps = splitWithoutParen(string)
    new_comps = []
    for comp in comps:
        if not outString(comp, "%"):
            new_comps.append(comp)
            continue
        if "{" in comp:
            package_name,_, package_pattern = comp.partition("{")
            package_pattern = package_pattern[:-1]
            package_pattern = unfold(package_pattern)
            if not package_pattern:
                return
            new_comps.append(package_name + "{" + package_pattern + "}")
        else:
            n_comp = comp
            if n_comp[0] != "%":
                return False
            n_comp = n_comp[1:]

            if n_comp[0] != "[" or n_comp[-1] != "]":
                return False
            if "*" in n_comp:
                n_comp = processHead(n_comp)
            if "*" in n_comp:
                return False

            if n_comp == "[]":
                continue

            n_comp = n_comp[1:-1]
            new_comps.append(n_comp)

    return ",".join(new_comps)


# Dereferences References
def deref(interpreter, string:str):

    if "!" not in string:
        return string

    comps = splitWithoutParen(string)
    new_comps = []
    for comp in comps:

        if comp.startswith("%"):
            unfolding = True
        else:
            unfolding = False

        t = match_type(comp)
        if t == "constant" and comp.startswith("!"):
            comp = deref(interpreter, comp[1:])
            if comp not in interpreter.references:
                return False
            new_comps.append(interpreter.references[comp])
        elif t in ["var", "constant"]:
            new_comps.append(comp)
        elif t == "head":
            head, tail = splitWithoutParen(comp[1:-1], '*')
            head, tail = deref(interpreter, head), deref(interpreter, tail)
            if False in [head, tail]:
                return False

            final = f"[{head}*{tail}]"
            final = processHead(final)
            if not final:
                return
            new_comps.append(final)
        elif t == "list":
            elems = splitWithoutParen(comp[1:-1])
            elems = [deref(interpreter, elem) for elem in elems]
            if False in elems:
                return False
            new_comps.append("[" + ",".join(elems) + "]")
        elif t == "pair":
            comp = comp[1:-1]
            first, second = splitWithoutParen(comp, "/")
            first, second = deref(interpreter, first), deref(interpreter, second)
            if False in [first, second]:
                return False
            new_comps.append(f"{first}/{second}")
        elif t == "pack":
            p_name, _, p_pattern = comp.partition("{")
            p_pattern = deref(interpreter, p_pattern[:-1])
            new_comps.append(f"{p_name}{{{p_pattern}}}")
        elif t == "title":
            t_name, _, t_pat = comp.partition("(")
            t_pat = t_pat[:-1]
            a = [deref(interpreter, sub_comp) for sub_comp in splitWithoutParen(t_pat)]
            if False in a:
                return False
            new_comps.append(t_name + "(" + ",".join(a) + ")")
        else:
            return False

        if unfolding:
            new_comps[-1] = "%" + new_comps[-1]

    return ",".join(new_comps)


# finds if a substring is inside a string but not inside quotation marks
def outString(string, find):
    """
    finds if a substring is inside a string but not inside quotation marks

    :param string: str
    :param find: str
    :return: boolean
    """
    n = len(find)
    inQuote = False
    for i in range(len(string) - n + 1):
        substring = string[i:i+n]
        if substring[0] == "\"":
            inQuote = not inQuote
        elif substring == find and not inQuote:
            return True
    return False


# Variable find in a string (query)
def var_in_query(string, find):
    return outString(string, find + ",") or \
           outString(string, find + ")") or \
           outString(string, find + "(") or \
           outString(string, find + "]") or \
           outString(string, find + "&") or \
           outString(string, find + "$") or \
           outString(string, find + "|") or \
           outString(string, find + "}") or \
           outString(string, find + "{") or \
           outString(string, find + "*") or \
           outString(string, find + "/")


# Join a list of printable objects
def joinPrint(l:list):
    """
    Join a list of printable objects

    :param l: list of str
    :return: str
    """
    s = ""
    if len(l) == 0:
        return ""
    s = f"{l[0]}"
    newLined = False
    for item in l[1:]:
        if item == "\n":
            s += "\n"
            newLined = True
        elif not newLined:
            s += f" {item}"
        else:
            s += f"{item}"
            newLined = False
    return s


# Split for infixes
def splitByInfix(string, infx):
    """
    Split for infixes

    :param string: str
    :param infx: str
    :return: list[str]
    """
    n = len(infx)
    parts = ["",""]
    inQuote = False
    count = 0
    for i in range(len(string)-n):
        if string[i] == '"':
            inQuote = not inQuote
        if string[i] in "([{":
            count += 1
        if string[i] in ")]}":
            count -= 1

        if string[i:i+n] == infx and count == 0 and not inQuote:
            parts[1] = string[i+n:]
            break
        else:
            parts[0] += string[i]
    else:
        parts = [string]
    return parts


# Search for infixes
def lookup(string, infixes):
    """
    Search for infixes

    :param string: str
    :param infixes: list
    :return: str
    """

    if len(infixes) == 0:
        return string

    string = processParen(string)
    if not string:
        return False

    inside = False

    for infx in infixes:
        if string.startswith(infx):
            return string
        if infx in string:
            inside = True

    if not inside:
        return string

    for infx in infixes:
        parts = splitByInfix(string, infx)
        if len(parts) == 2:
            up1 = lookup(parts[0], infixes)
            up2 = lookup(parts[1], infixes)
            if not up1 or not up2:
                return False
            return f'{infx}({up1},{up2})'

    t = match_type(string)
    if t == "list":
        parts = splitWithoutParen(string[1:-1])
        final = []
        for part in parts:
            final.append(lookup(part, infixes))
        return "[" + ",".join(final) + "]"
    if t == "pair":
        first, second = splitWithoutParen(string[1:-1], "/")
        first, second = lookup(first, infixes), lookup(second, infixes)
        return f"{first}/{second}"
    if t == "head":
        head, tail = splitWithoutParen(string[1:-1], "*")
        head, tail = lookup(head, infixes), lookup(tail, infixes)
        return f"[{head}*{tail}]"
    if t == "title":
        title, _, rest = string.partition('(')
        rest = splitWithoutParen(rest[:-1])
        final = []
        for part in rest:
            final.append(lookup(part, infixes))
        if False in final:
            return False
        return title + "(" + ",".join(final) + ")"

    return string


# Finds the end of package ans start of pattern
def find_package_end(expr:str):
    """
    Finds the end of package ans start of pattern. E.g., G{?x,?y}(7) -> [G{?x,?y}, (7)]

    :param expr: str
    :return: bool if unsuccessful, str[2] if successful.
    """
    beg, _, rest = expr.partition("{")
    count = 1
    inQuote = False
    for i, c in enumerate(rest):
        if c == "\"":
            inQuote = not inQuote
        if c == "{" and not inQuote:
            count += 1
        if c == "}" and not inQuote:
            count -= 1
        if count == 0:
            break
    else:
        return False

    return beg+"{"+rest[:i+1], rest[i+1:]


# Removes whitespaces only outside of strings
def remove_whitespace(string:str):
    """
    Removes whitespaces only outside of strings

    :param string: str
    :return: str
    """
    removed = ""
    inQuote = False

    for c in string:
        if c == "\"":
            inQuote = not inQuote
        if c == " " and not inQuote:
            continue
        if c == "\t" and not inQuote:
            continue
        removed += c

    return removed


# Process a connect clause
def processConnectClause(string, start, end):
    """
    Process a string into a connect form.

    :param string: str
    :param: start : str
    :param: end : str
    :return: str
    """
    first_part = string.split(":")
    if len(first_part) > 2:
        return False
    if len(first_part) == 1:
        if "[" == first_part[0][0] and "]" == first_part[0][-1]:
            return f"_C({first_part[0]},{start},{end})"
        elif first_part[0][0] == "{" and first_part[0][-1] == "}":
            return first_part[0][1:-1]
        else:
            return f"{first_part[0]}({start},{end})"
    else:
        return f"{first_part[0]}({start},{end},{first_part[1]})"


# a Counter class for recursion
class Counter:
    """
    a Counter class for recursion
    """
    def __str__(self):
        return str(self.count)

    def __init__(self, count):
        """
        Counter of count

        :param count: the starting count
        """
        self.count = count

    def sub(self, other):
        """
        Subtracts from count

        :param other: a number to subtract from counter
        """
        self.count -= other


if __name__ == "__main__":
    # from collections import namedtuple
    # RefStruct = namedtuple("RefStruct", "references")
    # x = RefStruct(references={'0x981f4c': 'node(1,0x5d116)', '0x5d116': 'node(2,0xe0b14)', '0xe0b14': 'node(3,0xc45f0)', '0xc45f0': 'node(4,0x58d76)', '0x58d76': 'nil'})
    # print(deref(x, "!0x981f4c,node(?@11,?@12)"))
    # print(remove_whitespace("Ref.new(?x) & ?x := [] & ?x := [2 * !?x] & Print(!?x)"))
    print(unfold("Fruit(Apple,15,red),%[]"))
