import time
from typing import List, Tuple

import BuiltIns
from Datatypes import AbstractDataStructure
from util import processParen, splitWithoutParen, outString, smart_replace, smartUpdate, \
    processHead, Counter, match_type, find_package_end, unfold, deref, independent
from Match import MatchDictionary


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
        self.cond: List[Tuple[Query, Query]] = []

        self.object = None
        self.action = None

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

        # conditional statements
        if query[:4] == "cond":
            processed = processParen(query[5:-1])
            if not processed:
                self.interpreter.raiseError("Error: illegal cond statement")
                return
            self.type = "c"

            parts = splitWithoutParen(processed)
            for part in parts:
                trie = splitWithoutParen(part, ">")
                if len(trie) != 2:
                    self.interpreter.raiseError(f"Error: {part} illegal cond")
                    return
                cond, exe = trie
                cond = Query.create(self.interpreter, cond)
                exe = Query.create(self.interpreter, exe)
                self.cond.append((cond, exe))
            return

        # Changing a reference
        searchForReferenceDefinition = outString(query, ":=")
        if searchForReferenceDefinition:
            parts = query.split(":=")
            if len(parts) != 2:
                self.interpreter.raiseError(f"Error: Illegal pattern for changing a reference, '{query}'")
                return
            self.gateA, self.gateB = parts
            self.type = ":="
            return

        # Dereference
        if outString(query, "!") and len(splitWithoutParen(query, "!")) == 1:
            self.gateA = query
            self.type = "!"
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
        if self.type == 'r' or self.type == 'pi' or self.type == 'pc' or self.type == "%" or self.type == "!":
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
        elif self.type == "c":
            for key, value in self.cond:
                key, value = key.add_new_info(info), value.add_new_info(info)
                Q.cond.append((key, value))
                Q.type = 'c'
        elif self.type == ":=":
            Q.gateA = smart_replace(self.gateA, info)
            Q.gateB = smart_replace(self.gateB, info)
            Q.type = ":="

        return Q

    # to string
    def __str__(self):
        """
        Query as string

        :return: str
        """
        if self.type == "r" or self.type == 'pi' or self.type == 'pc' or self.type == "%" or self.type == "!":
            return f"{self.gateA}"
        elif self.type == '&':
            return "(" + str(self.gateA) + ")" + "&" + "(" + str(self.gateB) + ")"
        elif self.type == "c":
            s = ",".join([f"{cond} > {search}" for cond, search in self.cond])
            return f"cond({s})"
        elif self.type == "|":
            return "(" + str(self.gateA) + ")" + "|" + "(" + str(self.gateB) + ")"
        elif self.type == "~":
            return "~" + str(self.gateA)
        elif self.type == "$":
            return "(" + str(self.gateA) + ")" + "$" + "(" + str(self.gateB) + ")"
        elif self.type == ":=":
            return f"{self.gateA} := {self.gateB}"
        else:
            print(self.type)

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
        Given type "c" conditional.

        :param depth: a Counter object, maximum recursion depth
        :return: a generator object that can generate solutions for this query, dict[str, str]
        """

        if depth.count < 0:
            return

        # MyLen(?xs, 81) & sod(%?xs)

        # print(f"Searching for {self.__str__()}, with accumulated depth of {depth}, type {self.type}")

        if self.interpreter.trace_on:
            self.interpreter.message(f"Searching for {self.__str__()}")
            yield "Print"

        # regular query
        if self.type == 'r':

            if not self.gateA:
                return

            if ":" in self.gateA:
                data_name, _, second_part = self.gateA.partition(":")
                action, _, query_pat = second_part.partition("(")
                query_pat = query_pat[:-1]
                data_struct: AbstractDataStructure = self.interpreter.datasets.get(data_name, None) or self.interpreter.datahashes.get(data_name, None)
                if data_struct:
                    if action == "Insert":
                        yield from data_struct.insert(query_pat)
                    elif action == "Remove":
                        yield from data_struct.remove(query_pat)
                    elif action == "Lookup":
                        yield from data_struct.lookup(query_pat)
                    elif action == "Clear":
                        if query_pat == "":
                            yield from data_struct.clear()

                elif match_type(data_name) == "title":
                    t_name, _, t_pattern = data_name.partition("(")
                    start = ""
                    if f"{t_name}.metacall" in self.interpreter.predicates:
                        start = f"{t_name}.metacall(" + data_name + "," + action + ",[" + query_pat + "])"
                    class_prefix = f"{t_name}.{action}"
                    if class_prefix in self.interpreter.predicates:
                        class_string = start + f"{class_prefix}(" + data_name + (query_pat and "," + query_pat) + ")"
                        print(class_string)
                        class_action = Query.create(self.interpreter, class_string)
                        if class_action:
                            yield from class_action.search(depth)
                    else:
                        if f"{t_name}.call" in self.interpreter.predicates:
                            class_string = start + f"{t_name}.call(" + data_name + "," + action + ",[" + query_pat + "])"
                            yield from Query.create(self.interpreter, class_string).search(depth)

                elif f"{data_name}.new" in self.interpreter.predicates:
                    for construct_dict in Query.create(self.interpreter, f"{data_name}.new(?construct)").search(depth):
                        construct = construct_dict.get("?construct", None)
                        if construct:
                            m = MatchDictionary.match(self.interpreter, action, construct)
                            if m:
                                yield m[1]

                return

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
                if query_pat == "":
                    return
                for predicate in self.interpreter.predicates.values():
                    sol_with_predicate = {query_name: predicate.name}
                    Q = Query.create(self.interpreter, smart_replace(self.__str__(), sol_with_predicate))
                    depth.sub(1)
                    for sol in Q.search(depth):
                        if type(sol) == str:
                            yield sol
                            continue
                        complete_sol = smartUpdate(sol_with_predicate, sol)
                        yield complete_sol
                return

            if query_name in self.interpreter.pythons:
                try:
                    yield from self.interpreter.pythons[query_name](query_pat)
                except Exception as e:
                    self.interpreter.raiseError(f"Python Error: {e}")
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

            found = [False]
            for solution in BuiltIns.builtin(self.interpreter, query_name, query_pat, depth, found):
                builtin_yielded = True
                yield solution
            if found[0]:
                return

            if query_name in self.interpreter.domains:
                domain = self.interpreter.domains[query_name]
                # print(f"Found the domain {domain.name}")
                for sol in domain.search(depth, query_pat):
                    # print(f"Found a solution {sol}")
                    m = MatchDictionary.match(self.interpreter, query_pat, smart_replace(domain.raw_vars, sol))
                    if m:
                        yield m[1]
                return

            predicate_match = self.interpreter.predicates.get(query_name, None)

            if predicate_match:
                for search, backward, forwards in predicate_match.match(query_pat):
                    if search == 1:
                        """
                        solution = forwards
                        solution_as_dict = {}
                        print(forwards, backward)
                        for key in backward.keys():
                            if backward[key] in solution.keys():
                                to_replace = solution[backward[key]]
                                solution_as_dict[key] = to_replace
                            elif match_type(backward[key]) in ['list', 'head', 'title', 'pair', 'pack']:
                                solution_as_dict[key] = processHead(smart_replace(backward[key], solution))
                            else:
                                solution_as_dict[key] = backward[key]
                        yield solution_as_dict
                        """
                        yield backward
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
                            # print(f"Solution to original problem: {solution}, with {backward}")
                            solution_as_dict = {}
                            for key in backward.keys():

                                if backward[key] in solution.keys():
                                    solution_as_dict[key] = solution[backward[key]]
                                elif match_type(backward[key]) in ['list', 'head', 'title', 'pack', 'pair']:
                                    solution_as_dict[key] = processHead(smart_replace(backward[key], solution))
                                else:
                                    solution_as_dict[key] = backward[key]

                            yield solution_as_dict

        # filter clause
        elif self.type == "~":
            if not self.gateA:
                return
            new_depth = Counter(depth.count // 2)
            for _ in self.gateA.search(new_depth):
                return
            depth.sub(depth.count // 2 - new_depth.count)
            yield {}

        # and clause
        elif self.type == "&":

            if not self.gateA or not self.gateB:
                return

            if self.gateB.gateA == "-cut-":
                try:
                    gen = self.gateA.search(depth)
                    x = next(gen)
                    while x in ["Print", "Request"]:
                        print(f"Got Exception : {x}")
                        yield x
                        x = next(gen)
                    yield x
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
        elif self.type == '|':

            if not self.gateA or not self.gateB:
                return

            yield from self.gateA.search(depth)
            yield from self.gateB.search(depth)

        # Lazy Or
        elif self.type == "$":
            if not self.gateA or not self.gateB:
                return

            first_solutions = self.gateA.search(depth)
            found_in_first = False
            for sol in first_solutions:
                found_in_first = True
                yield sol
            if not found_in_first:
                yield from self.gateB.search(depth)

        # Package with input
        elif self.type == 'pi':

            if not self.gateA:
                return

            X = find_package_end(self.gateA)
            if not X:
                return

            p_pred, q_inp = X
            q_inp = q_inp[1:-1]
            p_name, _, p_inp = p_pred.partition("{")
            p_inp = p_inp[:-1]

            if p_name not in self.interpreter.packages:
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

            package_match = self.interpreter.packages[p_name]

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
        elif self.type == '%':

            if not self.gateA:
                return

            if outString(self.gateA, "){"):
                X = find_package_end(self.gateA)
                if not X:
                    return

                p_pred, q_inp = X
                q_inp = q_inp[1:-1]
                p_name, _, p_inp = p_pred.partition("{")
                p_inp = p_inp[:-1]

                if outString(p_inp, "%"):
                    p_inp = unfold(p_inp)
                if outString(q_inp, "%"):
                    q_inp = unfold(q_inp)

                if not p_inp or not q_inp:
                    return

                new_query = Query.create(self.interpreter, f"{p_name}{{{p_inp}}}({q_inp})")
                yield from new_query.search(depth)

            try:
                query_name, query_pat = self.gateA.split("(")
                query_pat = query_pat[:-1]
            except ValueError:
                return

            query_pat = unfold(query_pat)
            if not query_pat:
                return
            new_query = Query.create(self.interpreter, f"{query_name}({query_pat})")
            if new_query:
                yield from new_query.search(depth)
            return

        # Dereference
        elif self.type == "!":

            if not self.gateA:
                return

            if outString(self.gateA, "){"):
                X = find_package_end(self.gateA)
                if not X:
                    return

                p_pred, q_inp = X
                q_inp = q_inp[1:-1]
                p_name, _, p_inp = p_pred.partition("{")
                p_inp = p_inp[:-1]

                if outString(p_inp, "%"):
                    p_inp = deref(self.interpreter, p_inp)
                if outString(q_inp, "%"):
                    q_inp = deref(self.interpreter, q_inp)

                if not p_inp or not q_inp:
                    return

                new_query = Query.create(self.interpreter, f"{p_name}{{{p_inp}}}({q_inp})")
                yield from new_query.search(depth)

            try:
                query_name, _, query_pat = self.gateA.partition("(")
                query_pat = query_pat[:-1]
            except ValueError:
                return

            query_pat = deref(self.interpreter, query_pat)
            if not query_pat:
                return
            new_query = Query.create(self.interpreter, f"{query_name}({query_pat})")
            if new_query:
                yield from new_query.search(depth)
            return

        # Conditional Statements
        elif self.type == 'c':
            for key, value in self.cond:
                if not key or not value:
                    continue
                try:
                    search = key.search(depth)
                    p_solution = next(search)
                    while type(p_solution) is str:
                        yield p_solution
                        p_solution = next(search)
                    for sol in value.add_new_info(p_solution).search(depth):
                        if type(sol) is str:
                            yield sol
                            continue
                        yield smartUpdate(p_solution, sol)
                    return
                except StopIteration:
                    continue

        # Setting Reference
        elif self.type == ':=':
            if self.gateA not in self.interpreter.references:
                self.interpreter.raiseError(f"Error: Trying to change the value of non-existent reference, '{self.gateA}'")
                return
            elif independent(self.gateB):
                self.interpreter.raiseError(f"Error: trying to change the value of a reference to a value containing variables, '{self.gateB}'")
                return
            self.gateB = deref(self.interpreter, self.gateB)
            if not self.gateB:
                return
            self.gateB = processHead(self.gateB)
            if not self.gateB:
                return
            self.interpreter.references[self.gateA] = self.gateB
            yield {}

        else:
            self.interpreter.raiseError(f"Error: Illegal Query")


if __name__ == "__main__":
    q = Query.create(None, "?x:=3")
    print(q)