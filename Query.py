import time
from util import processParen, splitWithoutParen, outString, joinPrint, smart_replace, smartUpdate, \
    formatPrint, remove_whitespace, processHead, Counter, match_type, find_package_end, unfold
from Match import MatchDictionary
import MathHelper
import re
import Lexer
from Predicate import Predicate
from io import UnsupportedOperation
import hashlib
from random import random, randint


# Query Class
class Query:
    """

    Query class represents queries. Queries are questions asked by the programmer and solved by the database that the programmer has provided.
    Queries can be simple, or they can include many logical gates (see more in solving techniques).

    """

    start = 0

    def __init__(self, interpreter):
        """
        initiates empty query (don't call this, use @classmethod Query.Create(...))

        :param interpreter: Interpreter
        """
        self.gateA = None
        self.gateB = None
        self.type = None
        self.interpreter = interpreter

    # Create a new query
    @classmethod
    def create(cls, interpreter, query):
        """
        Main way of creating queries. Used class method and not __init__ because it calls itself recursively. While it is possible to use __init__ and call
        input recursively, this way is more aesthetically pleasing (in my opinion), because it allows the __init__ to behave as a private method behind the
        scenes.

        :param interpreter: Interpreter
        :param query: str
        :return: Query (None if illegal)
        """
        X = Query(interpreter)
        query = processParen(query)
        if not query:
            interpreter.raiseError("Error: Incomplete Parentheses")
            return
        X.input(query)
        return X

    # A function that defines the query - matches the type and recursively defines queries
    def input(self, query: str):
        """
        Main function that builds queries.
        Searches for logical gates (&, |, $, ~).
        Searches for package calls (G{...}(...))

        :param query: str
        :return: None
        """

        # looking for ands
        searchForAnd = splitWithoutParen(query, "&")
        if len(searchForAnd) != 1:
            self.gateB = Query.create(self.interpreter, searchForAnd[-1])
            self.gateA = Query.create(self.interpreter, "&".join(searchForAnd[:-1]))
            self.type = '&'
            return

        # looking for ors
        searchForOr = splitWithoutParen(query, "|")
        if len(searchForOr) != 1:
            self.gateA = Query.create(self.interpreter, searchForOr[0])
            self.gateB = Query.create(self.interpreter, "|".join(searchForOr[1:]))
            self.type = '|'
            return

        # looking for Xor
        searchForXor = splitWithoutParen(query, "$")
        if len(searchForXor) != 1:
            # print(searchForXor)
            self.gateA = Query.create(self.interpreter, searchForXor[0])
            self.gateB = Query.create(self.interpreter, "$".join(searchForXor[1:]))
            self.type = '$'
            return

        # looking for not
        searchForFilter = splitWithoutParen(query, "~")
        if len(searchForFilter) != 1:
            if len(searchForFilter) != 2 or searchForFilter[0] != '':
                self.interpreter.raiseError("Error: ~ must have 1 side!")
                return
            self.gateA = Query.create(self.interpreter, searchForFilter[1])
            self.type = "~"
            return

        # Folding
        if outString(query, "%") and len(splitWithoutParen(query, "%")) == 1:
            self.gateA = query
            self.type = "%"
            return

        # case that package
        searchForPackage = outString(query, "}(")
        if searchForPackage:
            self.gateA = query
            self.type = 'pi'
            return

        # case that it is a simple clause
        self.gateA = query
        self.type = 'r'
        return

    # Given new information (in the form of a dictionary) change the query
    def add_new_info(self, info: dict):
        """
        Adding new information to a current query.
        Useful in And Gates where a solution to a previous query is used in a following query(s).

        :param info: dict (of translations between variables and atoms|lists|variables)
        :return: Query (updated)
        """
        Q = Query(self.interpreter)
        if self.type == 'r' or self.type == 'pi' or self.type == 'pc' or self.type == "%":
            # print(f"New Info is {info}")
            Q.gateA = smart_replace(self.gateA, info)
            Q.type = self.type
        elif self.type in ['&', '|', '$']:
            try:
                Q.gateA = self.gateA.add_new_info(info)
                Q.gateB = self.gateB.add_new_info(info)
                Q.type = self.type
            except AttributeError as e:
                print(type(Q), Q.type, Q.gateA, Q.gateB)
                raise e
        elif self.type == '~':
            Q.gateA = self.gateA.add_new_info(info)
            Q.type = self.type

        # Chefs(?x) & h2(?x) & h5(?x) & h78(?x) & h3(?x) & h4(?x) & h6(?x) & h10(?x) & h1(?x) & h9(?x)

        return Q

    # to string
    def __str__(self):
        """
        Query as string

        :return: str
        """
        if self.type == "r" or self.type == 'pi' or self.type == 'pc' or self.type == "%":
            return f"{self.gateA}"
        if self.type == '&':
            return "(" + str(self.gateA) + ")" + "&" + "(" + str(self.gateB) + ")"
        if self.type == "|":
            return "(" + str(self.gateA) + ")" + "|" + "(" + str(self.gateB) + ")"
        if self.type == "~":
            return "~" + str(self.gateA)
        if self.type == "$":
            return "(" + str(self.gateA) + ")" + "$" + "(" + str(self.gateB) + ")"
        if self.type == "!":
            return str(self.gateA)

    # Main function. Searches for query
    def search(self, depth):
        """
        Search. Uses generators (yield statements) to generate solutions for this query.
        Given type "r" looks for predicates
        Given type "~" looks to see that a predicate doesn't have a solution
        Given type "&" looks for both gates of query, uses the first to 'feed' the second
        Given type "|" yields from first gate, and from second gate
        Given type "$" yields from first gate, if none yielded, yields from second gate
        Given type "pi", represents Package{param}(variables), searched packages
        Given type "%", unfolds (if possible) and searches normally ('r')

        :param depth: a Counter object, maximum recursion depth
        :return: a generator object that can generate solutions for this query, dict[str, str]
        """

        if depth.count < 0:
            return

        # print(f"Searching for {self.__str__()}, with accumulated depth of {depth}, type {self.type}")

        if self.interpreter.trace_on:
            self.interpreter.message(f"Searching for {self.__str__()}")
            yield "Print"

        # regular query
        if self.type == 'r':

            query_name, _, query_pat = self.gateA.partition("(")
            query_pat = query_pat[:-1]

            for mac in self.interpreter.macros:
                if mac in query_pat:
                    flag = True
                    break
            else:
                flag = False

            if flag:
                query_pat = self.interpreter.macroSimplified(query_pat, depth)
                if query_pat is None:
                    return

            if query_name == "True":
                yield {}
                return

            if "{" in query_name:
                self.type = "pi"
                yield from self.search(depth)
                return

            # if predicate is variable
            if query_name[0] == "?":
                for predicate in self.interpreter.predicates:
                    sol_with_predicate = {query_name: predicate.name}
                    Q = Query.create(self.interpreter, smart_replace(self.__str__(), sol_with_predicate))
                    depth.sub(1)
                    for sol in Q.search(depth):
                        complete_sol = smartUpdate(sol_with_predicate, sol)
                        yield complete_sol
                return

            if query_name == "Time":
                parts = splitWithoutParen(query_pat)
                if len(parts) != 1:
                    return
                m = MatchDictionary.match(self.interpreter, parts[0], str((time.time() - Query.start).__round__(2)))
                if m:
                    yield m[1]
                return

            if query_name == "ClockInit":
                if query_pat != "":
                    return
                Query.start = time.time()
                yield {}
                return

            # Break predicate
            if query_name == 'hBreak' and (self.interpreter.list_added or self.interpreter.types_added):
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
                m = MatchDictionary.match(self.interpreter, parts[1], inLcl)
                if m:
                    yield m[1]
                return

            # Init a reference
            if query_name == 'hInit' and self.interpreter.ref_added:
                parts = splitWithoutParen(query_pat)
                if len(parts) != 1 or match_type(parts[0]) != "constant":
                    return
                self.interpreter.references[parts[0]] = "nil"
                yield {}
                return

            # auto generate a reference name
            if query_name == 'hAuto' and self.interpreter.ref_added:
                parts = splitWithoutParen(query_pat)
                if len(parts) != 1 or match_type(parts[0]) != "var":
                    return
                generated = "ref_"+"".join([chr(randint(97,122)) for _ in range(randint(3,9))])
                while generated in self.interpreter.references:
                    generated = "ref_"+"".join([chr(randint(97,122)) for _ in range(randint(3,9))])
                self.interpreter.references[generated] = "nil"
                yield {parts[0]:generated}
                return

            # assign helper
            if query_name == "hAssign" and self.interpreter.ref_added:
                parts = splitWithoutParen(query_pat)
                if len(parts) != 2 or match_type(parts[0]) != "constant" or outString(parts[1], "?") or parts[0] not in self.interpreter.references:
                    return
                if self.interpreter.references[parts[0]] == 'nil':
                    if None in self.interpreter.memory:
                        index = self.interpreter.memory.index(None)
                        self.interpreter.memory[index] = parts[1]
                        self.interpreter.references[parts[0]] = index
                    else:
                        self.interpreter.memory.append(parts[1])
                        self.interpreter.references[parts[0]] = len(self.interpreter.memory) - 1
                else:
                    self.interpreter.memory[self.interpreter.references[parts[0]]] = parts[1]
                yield {}
                return

            # Get Reference
            if query_name == "hRef" and self.interpreter.ref_added:
                parts = splitWithoutParen(query_pat)
                if len(parts) != 2 or match_type(parts[0]) != "constant" or parts[0] not in self.interpreter.references:
                    return
                if self.interpreter.references[parts[0]] == 'nil':
                    ref = 'nil'
                else:
                    ref = self.interpreter.memory[self.interpreter.references[parts[0]]]

                if ref is None:
                    self.interpreter.raiseError("Error: Trying to access a deleted value.")
                    return
                t = MatchDictionary.match(self.interpreter, parts[1], ref)
                if t:
                    yield t[1]
                return

            # From reference to another
            if query_name == "FromRef" and self.interpreter.ref_added:
                # Init(r) & Ref(r, 5) & FromRef(r, ?x >> ADD(1, ?x))
                parts = splitWithoutParen(query_pat)
                if len(parts) != 2 or match_type(parts[0]) != "constant" or parts[0] not in self.interpreter.references:
                    return
                if self.interpreter.references[parts[0]] == 'nil':
                    self.interpreter.raiseError("Error: attempting to change from an empty reference.")
                    return
                else:
                    ref = self.interpreter.memory[self.interpreter.references[parts[0]]]
                if ref is None:
                    self.interpreter.raiseError("Error: Trying to access a deleted value.")
                    return
                if ">>" not in parts[1]:
                    self.interpreter.raiseError("Error: illegal pattern for from reference.")
                    return
                toMatch, _, toChange = parts[1].partition(">>")
                print(toMatch, toChange)
                t = MatchDictionary.match(self.interpreter, toMatch, ref)
                if t:
                    toReplace = smart_replace(toChange, t[1])
                    if any(mac in toReplace for mac in self.interpreter.macros):
                        toReplace = self.interpreter.macroSimplified(toReplace, depth, simplify_arrow=True)
                    self.interpreter.memory[self.interpreter.references[parts[0]]] = toReplace
                    yield t[1]
                return

            if query_name == "hDel" and self.interpreter.ref_added:
                parts = splitWithoutParen(query_pat)
                if len(parts) != 1 or match_type(parts[0]) != "constant" or parts[0] not in self.interpreter.references:
                    return
                if self.interpreter.references[parts[0]] == 'nil':
                    yield {}
                    return
                self.interpreter.memory[self.interpreter.references[parts[0]]] = None
                self.interpreter.references[parts[0]] = 'nil'
                yield {}
                return

            if query_name == "hScope" and self.interpreter.ref_added:
                parts = splitWithoutParen(query_pat)
                if len(parts) != 1 or match_type(parts[0]) != "constant" or parts[0] not in self.interpreter.references:
                    return
                del self.interpreter.references[parts[0]]
                yield {}
                return

            if query_name == "hFlush" and self.interpreter.ref_added:
                if query_pat != "":
                    return
                self.interpreter.references = {}
                self.interpreter.memory = []
                yield {}
                return

            if query_name == "hCopy" and self.interpreter.ref_added:
                parts = splitWithoutParen(query_pat)
                if len(parts) != 2 or match_type(parts[0]) != "constant" or match_type(parts[1]) != "constant" or \
                        parts[0] not in self.interpreter.references or parts[1] not in self.interpreter.references:
                    return
                self.interpreter.references[parts[1]] = self.interpreter.references[parts[0]]
                yield {}
                return

            # Input
            if query_name == "hInput" and self.interpreter.strings_added:
                parts = splitWithoutParen(query_pat)
                if len(parts) != 1:
                    return
                if parts[0][0] != "?":
                    return
                yield "Request"
                inp = self.interpreter.received_input
                self.interpreter.received_input = False
                yield {parts[0]: '"' + inp + '"'}

            # isList predicate (checks if list)
            if query_name == 'isList' and self.interpreter.types_added:
                parts = splitWithoutParen(query_pat)
                if len(parts) != 1:
                    return
                if parts[0][0] == "[":
                    yield {}
                return

            # isVar predicate (checks if variable)
            if query_name == 'isVar' and self.interpreter.types_added:
                parts = splitWithoutParen(query_pat)
                if len(parts) != 1:
                    return
                if '?' == parts[0][0]:
                    yield {}
                return

            # Title predicate (checks if title)
            if query_name == 'isTitle' and self.interpreter.types_added:
                parts = splitWithoutParen(query_pat)
                if len(parts) != 1:
                    return
                try:
                    T_name, _, T_pat = parts[0].partition("(")
                    if T_name in self.interpreter.titles:
                        yield {}
                except IndexError:
                    pass
                except ValueError:
                    pass
                return

            # Known Predicate (checks if variables in predicate)
            if query_name == 'isKnown' and self.interpreter.types_added:
                parts = splitWithoutParen(query_pat)
                if len(parts) != 1:
                    return
                if outString(parts[0], "?"):
                    return
                yield {}

            # Predicate predicate (is it a predicate)
            if query_name == 'isPredicate' and self.interpreter.types_added:
                parts = splitWithoutParen(query_pat)
                if len(parts) != 1:
                    return
                if parts[0] in self.interpreter.predicates_names or \
                        (parts[0] in ['Add', 'Sub', 'Mul', 'Div', 'Mod', 'Floor', 'Ceil', 'Power', 'Log', 'Sin', 'Cos', 'Tan',
                                      'LT'] and self.interpreter.math_added) \
                        or parts[0] == 'Print' or parts[0] == 'Predicate' or (parts[0] == 'Break' and self.interpreter.list_added):
                    yield {}
                return

            # isPackage predicate (is it a package)
            if query_name == 'isPackage' and self.interpreter.types_added:
                parts = splitWithoutParen(query_pat)
                if len(parts) != 1:
                    return
                if parts[0] in self.interpreter.packages_names:
                    yield {}
                return

            # Math Predicates
            if query_name in ['hAdd', 'hSub', 'hMul', 'hDiv', 'hMod', 'hFloor', 'hCeil', 'hPower', 'hLog',
                              'hSin', 'hCos', 'hTan', 'hLT'] and self.interpreter.math_added:
                yield from MathHelper.Reader(query_name, query_pat)
                return

            # Print 'predicate'
            if query_name == 'Print':
                parts = splitWithoutParen(query_pat)
                printible = []
                for part in parts:
                    printible.append(formatPrint(part))
                printed = joinPrint(printible)
                self.interpreter.message(printed)
                yield "Print"
                if query_pat[-1] == ",":
                    self.interpreter.newline = True
                else:
                    self.interpreter.newline = False
                yield {}

            # AllSolutions predicate
            if query_name == 'hAllSolutions' and self.interpreter.predicates_added:
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
                for sol in self.interpreter.mixed_query(q, 0, depth.count, True):
                    sols.append(smart_replace(f"[{pattern}]", sol))
                final = "[" + ",".join(sols) + "]"
                m = MatchDictionary.match(self.interpreter, parts[2], final)
                if m:
                    yield m[1]
                return

            # Save predicate
            if query_name == 'hSave' and self.interpreter.save_added:
                parts = splitWithoutParen(query_pat)
                if len(parts) != 1:
                    return
                if outString(parts[0], "?"):
                    return
                to_save = parts[0]
                self.interpreter.saved.insert(0, to_save)
                yield {}
                return

            # helper Load predicate
            if query_name == 'hLoad' and self.interpreter.save_added:
                parts = splitWithoutParen(query_pat)
                if len(parts) == 1:
                    if len(self.interpreter.saved) == 0:
                        return
                    else:
                        to_load = self.interpreter.saved.popleft()
                        t = MatchDictionary.match(self.interpreter, parts[0], to_load)
                        if t:
                            yield t[1]
                return

            # Chars predicate
            if query_name == 'ToChars' and self.interpreter.strings_added:

                parts = splitWithoutParen(query_pat)
                if len(parts) != 2 or outString("[", parts[0]) or outString(parts[0], "?") or parts[0][0] != '"' or parts[0][-1] != '"':
                    return
                broken = list(parts[0][1:-1])
                inLcl = '[' + ",".join(list(map(lambda c: f'"{c}"', broken))) + "]"
                m = MatchDictionary.match(self.interpreter, parts[1], inLcl)
                if m:
                    yield m[1]
                return

            # Chars to String ToChars("123456(())    ))){}{}({{{{{{{", ?x) & ToString(?x, ?y)
            if query_name == 'ToString' and self.interpreter.strings_added:
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
                m = MatchDictionary.match(self.interpreter, parts[1], inLcl)
                if m:
                    yield m[1]
                return

            # open file
            if query_name == 'hOpen' and self.interpreter.filestream_added:
                parts = splitWithoutParen(query_pat)
                if len(parts) != 3:
                    return
                file_name, file_type, file_var = parts
                if match_type(file_var) != "var":
                    return
                file_name = file_name[1:-1]
                print(file_name)
                file_type = file_type[1:-1]
                if file_type not in ["r", "w", "a", "r+"]:
                    self.interpreter.raiseError(f"Error: Illegal file type '{file_type}'")
                    return
                if ":" not in file_name:
                    try:
                        f = open(self.interpreter.filepath + "/" + file_name, file_type)
                    except FileNotFoundError:
                        self.interpreter.raiseError(f"Error: File not found, '{file_name}'")
                        return
                else:
                    try:
                        f = open(file_name, file_type)
                    except FileNotFoundError:
                        self.interpreter.raiseError(f"Error: File not found, '{file_name}'")
                        return
                file_hash = hashlib.md5((random().as_integer_ratio()[0] + random().as_integer_ratio()[1]).__str__().encode()).hexdigest()
                self.interpreter.files[file_hash] = f
                yield {file_var: file_hash}
                return

            # read file
            if query_name == 'hRead' and self.interpreter.filestream_added:
                parts = splitWithoutParen(query_pat)
                if len(parts) != 2:
                    return
                file_name, char_to = parts
                if match_type(char_to) != 'var':
                    return False
                if file_name not in self.interpreter.files:
                    self.interpreter.raiseError(f"Error: File '{file_name}' not opened.")
                    return
                file_read = self.interpreter.files[file_name]
                try:
                    c = file_read.read(1)
                except UnsupportedOperation:
                    self.interpreter.raiseError(f"Error: File '{file_name}' not readable.")
                    return

                yield {char_to: '"' + c + '"'}
                return

            # write in file
            if query_name == 'hWrite' and self.interpreter.filestream_added:
                parts = splitWithoutParen(query_pat)
                if len(parts) != 2:
                    return
                file_name, write = parts
                if write[0] == '"':
                    write = write[1:-1]
                if file_name not in self.interpreter.files:
                    self.interpreter.raiseError(f"Error: File '{file_name}' not opened.")
                    return

                try:
                    self.interpreter.files[file_name].write(write)
                except UnsupportedOperation:
                    self.interpreter.raiseError(f"Error: File '{file_name}' not writable.")
                    return

                yield {}

            # close file
            if query_name == 'hClose' and self.interpreter.filestream_added:
                parts = splitWithoutParen(query_pat)
                if len(parts) != 1:
                    return

                file_name = parts[0]
                if file_name in self.interpreter.files:
                    self.interpreter.files[file_name].close()
                    self.interpreter.files.pop(file_name)
                    yield {}
                    return
                else:
                    self.interpreter.raiseError(f"Error: file '{file_name}' not found.")
                    return

                return

            # Tracing searching algorithm

            if query_name == "Trace" and self.interpreter.inspect_added:
                if query_pat == "On":
                    self.interpreter.trace_on = True
                elif query_pat == "Off":
                    self.interpreter.trace_on = False
                else:
                    return
                yield {}

            # Listing - list all cases of predicate
            if query_name == "Listing" and self.interpreter.inspect_added:
                p_name = query_pat

                if p_name == "ALL":
                    for predicate in self.interpreter.predicates:
                        self.interpreter.message(predicate.__str__())
                    yield 'Print'
                    yield {}
                    return

                if p_name not in self.interpreter.predicates_names:
                    return
                else:
                    predicate_match = self.interpreter.predicates[self.interpreter.predicates_names.index(p_name)]
                    self.interpreter.message(predicate_match.__str__())
                    yield "Print"
                    yield {}
                    return

                return

            if self.interpreter.dynamic_added and query_name in ["AssertF",
                                                                 "AssertFE",
                                                                 "AssertN",
                                                                 "AssertNE",
                                                                 "AssertC",
                                                                 "AssertCE",
                                                                 "DeleteF",
                                                                 "DeleteN",
                                                                 "DeleteC",
                                                                 "Create",
                                                                 "SwitchRecursive",
                                                                 "SwitchRandom",
                                                                 'Clear',
                                                                 'Delete']:

                parts = splitWithoutParen(query_pat)
                if len(parts) != 1:
                    return

                if query_name == "Create":
                    if re.fullmatch(r'[a-zA-Z_0-9\-\.]+', query_pat) and query_pat not in Lexer.reserved:
                        new_pred = Predicate(self.interpreter, query_pat, False, False)
                        self.interpreter.predicates.append(new_pred)
                        self.interpreter.predicates_names.append(query_pat)
                        yield {}
                        return
                    else:
                        return
                if query_name == "SwitchRecursive":
                    if query_pat in self.interpreter.predicates_names:
                        pred = self.interpreter.predicates[self.interpreter.predicates_names.index(query_pat)]
                        pred.recursive = not pred.recursive
                        yield {}
                        return
                    else:
                        return
                if query_name == "SwitchRandom":
                    if query_pat in self.interpreter.predicates_names:
                        pred = self.interpreter.predicates[self.interpreter.predicates_names.index(query_pat)]
                        pred.random = not pred.random
                        yield {}
                        return
                    else:
                        return
                if query_name == 'Delete':
                    if query_pat in self.interpreter.predicates_names:
                        predicate_changed = self.interpreter.predicates[self.interpreter.predicates_names.index(query_pat)]
                        self.interpreter.predicates.remove(predicate_changed)
                        self.interpreter.predicates_names.remove(predicate_changed.name)
                        yield {}
                        return
                    return

                predicate_changed, _, body = query_pat.partition("(")
                body = "(" + body
                body = remove_whitespace(body)

                if predicate_changed not in self.interpreter.predicates_names:
                    return

                predicate_changed = self.interpreter.predicates[self.interpreter.predicates_names.index(predicate_changed)]

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
                    to_match, _, then = body.partition(">>")
                    to_match, then = processParen(to_match), processParen(then)
                    if not to_match or not then:
                        return
                    predicate_changed.addCase(to_match, then)
                    yield {}
                    return
                if query_name == "AssertC":
                    to_match, _, then = body.partition(">>")
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
                    to_match, _, then = body.partition(">>")
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

            if query_name in self.interpreter.domains:
                domain = self.interpreter.domains[query_name]
                print(f"Found the domain {domain.name}")
                for sol in domain.search(depth, query_pat):
                    print(f"Found a solution {sol}")
                    m = MatchDictionary.match(self.interpreter, query_pat, smart_replace(domain.raw_vars, sol))
                    if m:
                        yield m[1]
                return

            if query_name not in self.interpreter.predicates_names:
                return

            predicate_match = self.interpreter.predicates[self.interpreter.predicates_names.index(query_name)]

            if predicate_match:
                for search, backward, forwards in predicate_match.match(query_pat):
                    if search == 1:
                        solution = forwards
                        solution_as_dict = {}
                        for key in backward.keys():
                            if backward[key] in solution.keys():
                                solution_as_dict[key] = solution[backward[key]]
                            elif match_type(backward[key]) in ['list', 'head', 'title']:
                                solution_as_dict[key] = processHead(smart_replace(backward[key], solution))
                            else:
                                solution_as_dict[key] = backward[key]

                        yield solution_as_dict
                    else:
                        next_q = Query.create(self.interpreter, search)
                        depth.sub(1)
                        for solution in next_q.search(depth):

                            if solution == "Request":
                                yield "Request"
                                continue
                            if solution == "Print":
                                yield "Print"
                                continue
                            # print(f"Solution to original problem: {solution}")
                            solution_as_dict = {}
                            for key in backward.keys():

                                if backward[key] in solution.keys():
                                    solution_as_dict[key] = solution[backward[key]]
                                elif match_type(backward[key]) in ['list', 'head', 'title', 'pack']:
                                    solution_as_dict[key] = processHead(smart_replace(backward[key], solution))
                                else:
                                    solution_as_dict[key] = backward[key]

                            yield solution_as_dict

        # filter clause
        if self.type == "~":
            # not can only come after & and $
            new_depth = Counter(depth.count // 2)
            for _ in self.gateA.search(new_depth):
                return
            depth.sub(depth.count // 2 - new_depth.count)
            yield {}

        # and clause
        if self.type == "&":

            if self.gateB.gateA == "-cut-":
                try:
                    yield next(self.gateA.search(depth))
                except StopIteration:
                    pass
                finally:
                    return

            for p_solution in self.gateA.search(depth):

                # print(f"The solution to {str(self.gateA)} is {str(p_solution)}")

                if p_solution == "Request":
                    yield "Request"
                    continue
                if p_solution == "Print":
                    yield "Print"
                    continue
                try:
                    updated_gate_B = self.gateB.add_new_info(p_solution)
                except AttributeError as e:
                    print(self, self.gateB, self.type)
                    raise e
                if updated_gate_B.type == "~":
                    yes = updated_gate_B.gateA.search(depth)
                    try:
                        next(yes)
                    except StopIteration:

                        yield p_solution

                else:
                    for solution in updated_gate_B.search(depth):
                        if solution == "Request":
                            yield "Request"
                            continue
                        if solution == "Print":
                            yield "Print"
                            continue

                        q_solution = p_solution.copy()
                        # print(f"The Two solutions are {q_solution} and {solution}")
                        q_solution = smartUpdate(q_solution, solution)

                        yield q_solution

        # or clause
        if self.type == '|':
            yield from self.gateA.search(depth)
            yield from self.gateB.search(depth)

        # Lazy Or
        if self.type == "$":
            first_solutions = self.gateA.search(depth)
            found_in_first = False
            for sol in first_solutions:
                found_in_first = True
                yield sol
            if not found_in_first:
                yield from self.gateB.search(depth)

        # Package with input
        if self.type == 'pi':

            X = find_package_end(self.gateA)
            if not X:
                return

            p_pred, q_inp = X
            q_inp = q_inp[1:-1]
            p_name, _, p_inp = p_pred.partition("{")
            p_inp = p_inp[:-1]

            if p_name not in self.interpreter.packages_names:
                return

            flag_p = False
            flag_q = False

            for macro in self.interpreter.macros:
                if macro in p_inp:
                    flag_p = True
                if macro in q_inp:
                    flag_q = True
                if flag_p and flag_q:
                    break

            if flag_p:
                p_inp = self.interpreter.macroSimplified(p_inp, depth)
            if flag_q:
                q_inp = self.interpreter.macroSimplified(q_inp, depth)

            package_match = self.interpreter.packages[self.interpreter.packages_names.index(p_name)]

            for search, backward in package_match.match(p_inp, q_inp):
                if search == 1:
                    yield backward
                    continue

                new_query = Query.create(self.interpreter, search)

                depth.sub(1)

                for solution in new_query.search(depth):
                    solution_as_dict = {}
                    for key in backward:
                        solution_as_dict[key] = smart_replace(backward[key], solution)
                    yield solution_as_dict

        # Folding
        if self.type == '%':
            query_name, query_pat = self.gateA.split("(")
            query_pat = query_pat[:-1]

            query_pat = unfold(query_pat)
            if not query_pat:
                return
            new_query = Query.create(self.interpreter, f"{query_name}({query_pat})")
            yield from new_query.search(depth)
            return
