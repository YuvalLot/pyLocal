
import hashlib
import re
from io import UnsupportedOperation
from random import randint, random

import Lexer
import MathHelper
from Domain import Domain
from Match import MatchDictionary
from OnlineRequest import url_opener
from Predicate import Predicate
from util import processParen, remove_whitespace, splitWithoutParen, match_type, outString, smart_replace, formatPrint, joinPrint, get_all_basics, \
    independent


def builtin(interpreter, query_name, query_pat, depth, found):
    """
    Builtin predicates (many different libraries).

    :param interpreter: Interpreter
    :param query_name: str
    :param query_pat: str
    :param depth: Counter
    :param found: "pointer" bool
    :return: Generator
    """

    found[0] = True

    # checks for terminal match
    if query_name == "GuaranteeUnify":
        comps = splitWithoutParen(query_pat)
        if len(comps) != 2:
            return
        comp1, comp2 = comps
        m = MatchDictionary.match(interpreter, comp1, comp2)
        if m and not m[2]:
            yield {}
        return

    # Can be unified
    if query_name == "CanUnify":
        comps = splitWithoutParen(query_pat)
        if len(comps) != 2:
            return
        comp1, comp2 = comps
        m = MatchDictionary.match(interpreter, comp1, comp2)
        if m:
            yield {}
        return

    # Exact copy of a pattern
    if query_name == "ExactCopy":
        comps = splitWithoutParen(query_pat)
        if len(comps) != 2:
            return
        comp1, comp2 = comps
        bs = get_all_basics(comp1)
        copy = MatchDictionary.transform(comp1, bs, {})
        m = MatchDictionary.match(interpreter, comp2, copy)
        if m:
            print(m[1])
            yield m[1]
        return

    # Online Request
    if query_name == "Request":
        parts = splitWithoutParen(query_pat)
        if len(parts) != 2:
            return
        try:
            inLcl = url_opener(parts[0][1:-1])
            if inLcl is None:
                return
            m = MatchDictionary.match(interpreter, parts[1], inLcl)
            if m:
                yield m[1]
        except Exception as e:
            print(e)
        finally:
            return

    # Ref.new - Create reference
    if query_name == "Ref.new":
        comps = splitWithoutParen(query_pat)
        if len(comps) != 1:
            return
        comp1, = comps
        if match_type(comp1) != "var":
            return
        rand = hex(randint(10000, 10000000))
        while rand in interpreter.references:
            rand = hex(randint(100, 100000))
        interpreter.references[rand] = "nil"
        yield {comp1: rand}
        return

    # Ref.del - delete a reference
    if query_name == "Ref.del":
        comps = splitWithoutParen(query_pat)
        if len(comps) != 1:
            return
        comp1, = comps
        if comp1 not in interpreter.references:
            return
        del interpreter.references[comp1]
        yield {}
        return

    if query_name == "SecIns":
        print(">> ", end="")
        inspect = input()
        try:
            print(eval(inspect))
            yield {}
        except Exception as e:
            print(e)
        return

    # Break predicate
    if query_name == 'hBreak' and (interpreter.list_added or interpreter.types_added):
        parts = splitWithoutParen(query_pat)
        if len(parts) != 2 or "[" in parts[0] or "?" in parts[0]:
            return
        broken = list(parts[0])
        if len(broken) == 0:
            return
        inLcl = '['
        for broke in broken:
            inLcl += broke + ","
        inLcl = inLcl[:-1] + "]"
        m = MatchDictionary.match(interpreter, parts[1], inLcl)
        if m:
            yield m[1]
        return

    # domain generator
    if query_name == "Domain-Generator":
        parts = splitWithoutParen(query_pat)
        if len(parts) != 4 or any(match_type(part) != "list" for part in parts):
            return
        variables = splitWithoutParen(parts[0][1:-1])
        if any(match_type(pattern) != "var" for pattern in variables):
            return
        ranges = splitWithoutParen(parts[1][1:-1])
        if len(ranges) != len(variables):
            return
        constraints = splitWithoutParen(parts[2][1:-1])
        elims = splitWithoutParen(parts[3][1:-1])
        D = Domain(interpreter, "~~Anon")
        D.variables = variables
        D.raw_vars = parts[0][1:-1]
        for i, var in enumerate(variables):
            D.range_searches[var] = ranges[i]
        for const in constraints:
            D.insert_constraint(const, "", -1)
        for elim in elims:
            D.insert_elimination(elim, "", -1)
        yield from D.search(depth, parts[0][1:-1])

    # Input
    if query_name == "hInput" and interpreter.strings_added:
        parts = splitWithoutParen(query_pat)
        if len(parts) != 1:
            return
        if parts[0][0] != "?":
            return
        yield "Request"
        inp = interpreter.received_input
        interpreter.received_input = False
        yield {parts[0]: '"' + inp + '"'}

    # isList predicate (checks if list)
    if query_name == 'isList' and interpreter.types_added:
        parts = splitWithoutParen(query_pat)
        if len(parts) != 1:
            return
        if parts[0][0] == "[":
            yield {}
        return

    # isVar predicate (checks if variable)
    if query_name == 'isVar' and interpreter.types_added:
        parts = splitWithoutParen(query_pat)
        if len(parts) != 1:
            return
        if '?' == parts[0][0]:
            yield {}
        return

    # Title predicate (checks if title)
    if query_name == 'isTitle' and interpreter.types_added:
        parts = splitWithoutParen(query_pat)
        if len(parts) != 1:
            return
        try:
            T_name, _, T_pat = parts[0].partition("(")
            if T_name in interpreter.titles:
                yield {}
        except IndexError:
            pass
        except ValueError:
            pass
        return

    # Integer predicate (checks if integer)
    if query_name == 'isInteger' and interpreter.types_added:
        parts = splitWithoutParen(query_pat)
        if len(parts) != 1:
            return
        try:
            a = int(parts[0])
            yield {}
        except IndexError:
            pass
        except ValueError:
            pass
        return

    # Floating predicate (checks if float)
    if query_name == 'isFloating' and interpreter.types_added:
        parts = splitWithoutParen(query_pat)
        if len(parts) != 1:
            return
        try:
            a = float(parts[0])
            yield {}
        except IndexError:
            pass
        except ValueError:
            pass
        return

    # Known Predicate (checks if variables in predicate)
    if query_name == 'isKnown' and interpreter.types_added:
        parts = splitWithoutParen(query_pat)
        if len(parts) != 1:
            return
        if outString(parts[0], "?"):
            return
        yield {}

    # Predicate predicate (is it a predicate)
    if query_name == 'isPredicate' and interpreter.types_added:
        parts = splitWithoutParen(query_pat)
        if len(parts) != 1:
            return
        if parts[0] in interpreter.predicates or \
                (parts[0] in ['Add', 'Sub', 'Mul', 'Div', 'Mod', 'Floor', 'Ceil', 'Power', 'Log', 'Sin', 'Cos', 'Tan',
                              'LT'] and interpreter.math_added) \
                or parts[0] == 'Print' or parts[0] == 'Predicate' or (parts[0] == 'Break' and interpreter.list_added):
            yield {}
        return

    # isPackage predicate (is it a package)
    if query_name == 'isPackage' and interpreter.types_added:
        parts = splitWithoutParen(query_pat)
        if len(parts) != 1:
            return
        if parts[0] in interpreter.packages:
            yield {}
        return

    # Math Predicates
    if query_name in ['hAdd', 'hSub', 'hMul', 'hDiv', 'hMod', 'hFloor', 'hCeil', 'hPower', 'hLog',
                      'hSin', 'hCos', 'hTan', 'hLT', 'hE'] and interpreter.math_added:
        yield from MathHelper.Reader(query_name, query_pat)
        return

    # Print 'predicate'
    if query_name == 'Print':
        parts = splitWithoutParen(query_pat)
        printible = []
        for part in parts:
            printible.append(formatPrint(part))
        printed = joinPrint(printible)
        interpreter.message(printed)
        yield "Print"
        if len(query_pat) != 0 and query_pat[-1] == ",":
            interpreter.newline = True
        else:
            interpreter.newline = False
        yield {}

    # AllSolutions predicate
    if query_name == 'hAllSolutions' and interpreter.predicates_added:
        parts = splitWithoutParen(query_pat)
        if len(parts) != 3:
            return
        if parts[0][0] == "?":
            return
        try:
            n = int(parts[1])
        except ValueError:
            return
        sols = []
        pattern = ",".join([f"?x{j}" for j in range(n)])
        q = f"{parts[0]}({pattern})"
        for sol in interpreter.mixed_query(q, 0, depth.count, True):
            sols.append(smart_replace(f"[{pattern}]", sol))
        final = "[" + ",".join(sols) + "]"
        m = MatchDictionary.match(interpreter, parts[2], final)
        if m:
            yield m[1]
        return

    # Save predicate
    if query_name == 'hSave' and interpreter.save_added:
        parts = splitWithoutParen(query_pat)
        if len(parts) != 1:
            return
        if outString(parts[0], "?"):
            return
        to_save = parts[0]
        interpreter.saved.insert(0, to_save)
        yield {}
        return

    # helper Load predicate
    if query_name == 'hLoad' and interpreter.save_added:
        parts = splitWithoutParen(query_pat)
        if len(parts) == 1:
            if len(interpreter.saved) == 0:
                return
            else:
                to_load = interpreter.saved.popleft()
                t = MatchDictionary.match(interpreter, parts[0], to_load)
                if t:
                    yield t[1]
        return

    # Chars predicate
    if query_name == 'ToChars' and interpreter.strings_added:

        parts = splitWithoutParen(query_pat)
        if len(parts) != 2 or outString("[", parts[0]) or outString(parts[0], "?") or parts[0][0] != '"' or parts[0][-1] != '"':
            return
        broken = list(parts[0][1:-1])
        inLcl = '[' + ",".join(list(map(lambda c: f'"{c}"', broken))) + "]"
        m = MatchDictionary.match(interpreter, parts[1], inLcl)
        if m:
            yield m[1]
        return

    # Chars to String
    if query_name == 'ToString' and interpreter.strings_added:
        parts = splitWithoutParen(query_pat)
        if len(parts) != 2 or outString(parts[0], "?") or "[" != parts[0][0] or "]" != parts[0][-1]:
            return

        broken = splitWithoutParen(parts[0][1:-1])
        inLcl = '"'
        for broke in broken:
            if broke[0] != '"' or broke[-1] != '"':
                return
            inLcl += broke[1:-1]
        inLcl += '"'
        m = MatchDictionary.match(interpreter, parts[1], inLcl)
        if m:
            yield m[1]
        return

    # open file
    if query_name == 'hOpen' and interpreter.filestream_added:
        parts = splitWithoutParen(query_pat)
        if len(parts) != 3:
            return
        file_name, file_type, file_var = parts
        if match_type(file_var) != "var":
            return
        file_name = file_name[1:-1]
        print(file_name)
        if file_type not in ["r", "w", "a", "rp"]:
            if file_type == "rp":
                file_type = "r+"
            interpreter.raiseError(f"Error: Illegal file type '{file_type}'")
            return
        if ":" not in file_name:
            try:
                f = open(interpreter.filepath + "/" + file_name, file_type)
            except FileNotFoundError:
                interpreter.raiseError(f"Error: File not found, '{file_name}'")
                return
        else:
            try:
                f = open(file_name, file_type)
            except FileNotFoundError:
                interpreter.raiseError(f"Error: File not found, '{file_name}'")
                return
        file_hash = hashlib.md5((random().as_integer_ratio()[0] + random().as_integer_ratio()[1]).__str__().encode()).hexdigest()
        interpreter.files[file_hash] = f
        yield {file_var: file_hash}
        return

    # read file
    if query_name == 'hRead' and interpreter.filestream_added:
        parts = splitWithoutParen(query_pat)
        if len(parts) != 2:
            return
        file_name, char_to = parts
        if match_type(char_to) != 'var':
            return False
        if file_name not in interpreter.files:
            interpreter.raiseError(f"Error: File '{file_name}' not opened.")
            return
        file_read = interpreter.files[file_name]
        try:
            c = file_read.read(1)
        except UnsupportedOperation:
            interpreter.raiseError(f"Error: File '{file_name}' not readable.")
            return

        yield {char_to: '"' + c + '"'}
        return

    # write in file
    if query_name == 'hWrite' and interpreter.filestream_added:
        parts = splitWithoutParen(query_pat)
        if len(parts) != 2:
            return
        file_name, write = parts
        if write[0] == '"':
            write = write[1:-1]
        if file_name not in interpreter.files:
            interpreter.raiseError(f"Error: File '{file_name}' not opened.")
            return

        try:
            interpreter.files[file_name].write(write)
        except UnsupportedOperation:
            interpreter.raiseError(f"Error: File '{file_name}' not writable.")
            return

        yield {}

    # close file
    if query_name == 'hClose' and interpreter.filestream_added:
        parts = splitWithoutParen(query_pat)
        if len(parts) != 1:
            return

        file_name = parts[0]
        if file_name in interpreter.files:
            interpreter.files[file_name].close()
            interpreter.files.pop(file_name)
            yield {}
            return
        else:
            interpreter.raiseError(f"Error: file '{file_name}' not found.")
            return

    # Tracing searching algorithm
    if query_name == "Trace" and interpreter.inspect_added:
        if query_pat == "On":
            interpreter.trace_on = True
        elif query_pat == "Off":
            interpreter.trace_on = False
        elif query_pat == "OnOn":
            interpreter.console_trace_on = True
        elif query_pat == "OffOff":
            interpreter.console_trace_on = False
        else:
            return
        yield {}
        return

    # Show Memory
    if query_name == "ShowMem" and interpreter.inspect_added:
        interpreter.message(f"{interpreter.memory}\n{interpreter.references}\n")
        yield "Print"
        yield {}
        return

    # Listing - list all cases of predicate
    if query_name == "Listing" and interpreter.inspect_added:
        p_name = query_pat

        if p_name == "ALL":
            for predicate in interpreter.predicates.values():
                interpreter.message(predicate.__str__())
            yield 'Print'
            yield {}
            return

        if p_name not in interpreter.predicates:
            return
        else:
            predicate_match = interpreter.predicates[p_name]
            interpreter.message(predicate_match.__str__())
            yield "Print"
            yield {}
            return

        return

    if interpreter.dynamic_added and query_name in {"AssertF", "AssertFE", "AssertN", "AssertNE", "AssertC", "AssertCE", "DeleteF",
                                                    "DeleteN", "DeleteC", "Create", "SwitchRecursive", "SwitchRandom", 'Clear', 'Delete'} \
            :

        parts = splitWithoutParen(query_pat)
        if len(parts) != 1:
            return

        if query_name == "Create":
            if re.fullmatch(r'[a-zA-Z_0-9\-\.]+', query_pat) and query_pat not in Lexer.reserved:
                new_pred = Predicate(interpreter, query_pat, False, False)
                interpreter.predicates[new_pred.name] = new_pred
                yield {}
            return
        if query_name == "SwitchRecursive":
            if query_pat in interpreter.predicates:
                pred = interpreter.predicates[query_pat]
                pred.recursive = not pred.recursive
                yield {}
            return
        if query_name == "SwitchRandom":
            if query_pat in interpreter.predicates:
                pred = interpreter.predicates[query_pat]
                pred.random = not pred.random
                yield {}
            return
        if query_name == 'Delete':
            if query_pat in interpreter.predicates:
                del interpreter.predicates[query_pat]
                yield {}
            return

        predicate_changed, _, body = query_pat.partition("(")
        body = "(" + body
        body = remove_whitespace(body)

        if predicate_changed not in interpreter.predicates:
            return

        predicate_changed = interpreter.predicates[predicate_changed]

        if query_name == "AssertFE":
            basic = processParen(body)
            if basic:
                predicate_changed.addBasic(basic)
                yield {}
                return
            else:
                return
        if query_name == "AssertF":
            basic = processParen(body)
            if basic:
                predicate_changed.addBasic(basic, insert=True)
                yield {}
                return
            else:
                return

        if query_name == "AssertNE":
            basic = processParen(body)
            if basic:
                predicate_changed.addNot(basic)
                yield {}
                return
            else:
                return
        if query_name == "AssertN":
            basic = processParen(body)
            if basic:
                predicate_changed.addNot(basic, insert=True)
                yield {}
                return
            else:
                return

        if query_name == "AssertCE":
            to_match, _, then = body.partition(">")
            to_match, then = processParen(to_match), processParen(then)
            if not to_match or not then:
                return
            predicate_changed.addCase(to_match, then)
            yield {}
            return
        if query_name == "AssertC":
            to_match, _, then = body.partition(">")
            to_match, then = processParen(to_match), processParen(then)
            if not to_match or not then:
                return
            predicate_changed.addCase(to_match, then, insert=True)
            yield {}
            return

        if query_name == "DeleteF":
            body = processParen(body)
            if body in predicate_changed.basic:
                predicate_changed.basic.remove(body)
                yield {}
                return
            else:
                return
        if query_name == "DeleteN":
            body = processParen(body)
            if body in predicate_changed.nope:
                predicate_changed.nope.remove(body)
                yield {}
                return
            else:
                return
        if query_name == 'DeleteC':
            to_match, _, then = body.partition(">")
            to_match, then = processParen(to_match), processParen(then)
            if to_match in predicate_changed.cases:
                index = predicate_changed.cases.index(to_match)
                if then != predicate_changed.then[index]:
                    return
                predicate_changed.cases.remove(to_match)
                predicate_changed.then.remove(then)
                predicate_changed.count -= 1
                yield {}
                return
            else:
                return

        if query_name == 'Clear':
            predicate_changed.cases = []
            predicate_changed.then = []
            predicate_changed.count = 0
            predicate_changed.basic = []
            predicate_changed.nope = []
            yield {}
            return

        return

    found[0] = False
