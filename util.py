"""

Tools

includes a lot of different functions used in the project

"""

from func_timeout import func_timeout, FunctionTimedOut
from types import GeneratorType


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
    Returns the match type ("constant", "var", "head" (headed list), "list" (expanded list), "title", "pack")

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
    for i, c in enumerate(string):
        if c == "[":
            count += 1
        if c == "]":
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

    if match_type(_list) == 'title':
        t_name, _, t_pat = _list.partition("(")
        t_pat = t_pat[:-1]
        if t_pat == "":
            return []

    if match_type(_list) == 'pack':
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
            if t == "pack":
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
        "!"
    ]
    for c in string:

        if c == "\"":
            inQuote = not inQuote

        if c == "?":
            if current_var:
                if current_var == "?":
                    pass
                else:
                    new_s += replace_dict.get(current_var, current_var)
                    current_var = ""
            current_var += "?"
        elif c in ending_chars and current_var:
            new_s += replace_dict.get(current_var, current_var)
            new_s += c
            current_var = ""
        elif current_var:
            current_var += c
        else:
            new_s += c

    if current_var:
        new_s += replace_dict.get(current_var, current_var)

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
    if enclosed:
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
        return "[" + ",".join(processed_comps) + "]"
    if mt == 'title':
        if "*" not in string:
            return string
        title_name, _, t_pat = string.partition("(")
        t_pat = t_pat[:-1]
        processed_comps = []
        for comp in splitWithoutParen(t_pat):
            processed_comps.append(processHead(comp))
        return title_name + "(" + ",".join(processed_comps) + ")"
    if mt != 'head':
        return string

    string = string[1:-1]
    hd, tail = splitWithoutParen(string, "*")

    hd = processHead(hd)

    tail_type = match_type(tail)
    if tail_type in ["list", "head"]:
        tail = processHead(tail)
        tail_type = match_type(tail)

    if tail_type == 'list':
        if tail == "[]":
            return f"[{hd}]"
        return f"[{hd},{tail[1:-1]}]"
    if tail_type == 'head' or tail_type == 'var':
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

    if 'with' in string:
        parts = string.split('with')
        if len(parts) != 2:
            return False
        assertive = parts[1].strip()
        if assertive == 'assertions':
            string = parts[0]
            withe = 1
        else:
            return False

    s = ""
    inString = False
    inPython = False
    for char in string:
        if char == "@" and not inString and inPython:
            return False
        if char == "#" and not inString and not inPython:
            break
        if char == '"' and not inPython:
            inString = not inString
        if char == '!' and not inString:
            inPython = not inPython
        if char in " \t" and not inString and not inPython:
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
        if key[1]=="@":
            continue
        t = match_type(sol_dict[key])
        if t == "constant":
            continue
        if t == "var":
            if sol_dict[key] in variable_count.keys():
                variable_count[sol_dict[key]] += 1
            else:
                variable_count[sol_dict[key]] = 1
        if t in ["list", "head", 'title']:
            sol_dict[key] = processHead(sol_dict[key])
            t = match_type(sol_dict[key])
            basic_comps = get_all_basics(sol_dict[key], {"list":",", "head":"*", 'title':","}[t])
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
        if key[1] == "@":
            continue
        final_sol[key] = smart_replace(sol_dict[key], variable_replacing)
        if final_sol[key][0] == '"':
            final_sol[key] = final_sol[key].replace("\n", "\\n")
            final_sol[key] = final_sol[key].replace("\t", "\\t")

    s_final = ''
    for key in final_sol.keys():
        s_final += f"{key} ← {final_sol[key]}\n"

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
    for key in d1.keys():
        if d1[key] in d2.keys():
            d[key] = d2[d1[key]]
        elif match_type(d1[key]) in ['list', 'title', 'pack']:
            original = d1[key]
            comps = get_all_basics(d1[key])
            comp_dict = {}
            for comp in comps:
                if comp in d2.keys():
                    comp_dict[comp] = d2[comp]
            new = smart_replace(original, comp_dict)
            d[key] = new
        elif match_type(d1[key]) == "head":
            original = d1[key]
            comps = get_all_basics(d1[key], "*")
            comp_dict = {}
            for comp in comps:
                if comp in d2.keys():
                    comp_dict[comp] = d2[comp]
            new = smart_replace(original, comp_dict)
            d[key] = new
        else:
            d[key] = d1[key]
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
        return x
    if t == 'var':
        return 'Unknown'
    x = processHead(x)
    t = match_type(x)
    if t == 'list' or t == 'title':
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

    string = processParen(string)
    if not string: return False

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
    inPython = False

    for c in string:
        if c == "!" and not inQuote:
            inPython = not inPython
        if c == "\"" and not inPython:
            inQuote = not inQuote
        if c == " " and not inQuote and not inPython:
            continue
        if c == "\t" and not inQuote and not inPython:
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
    print(lookup("(A^d>3)^+(B^d>7)", ['^+', '^d>']))
