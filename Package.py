
from Match import MatchDictionary
from util import processParen, smart_replace, smartUpdate, independent
from Predicate import Predicate


# Package class
class Package:
    """

    Packages are unique to LCL, as they provide a way to dynamically create predicates based on some parameters.
    Packages are extremely useful when working with Filter or Map, as they can dynamically create flexible predicates.

    """

    @classmethod
    def createPredicateFromPackage(cls, interpreter, p_inp, name):
        """
        Create a new predicate. Class method that creates a new predicate from a package.

        :param interpreter:  Interpreter
        :param p_inp: str (full package, e.g., G{?a,?b})
        :param name: str
        :return: boolean
        """

        if independent(p_inp):
            interpreter.raiseError(f"Error: Trying to use a package with variables, with name {name}")
            return False

        p_name, _, p_inp = p_inp.partition("{")
        p_inp = p_inp[:-1]

        if p_name not in interpreter.packages:
            interpreter.raiseError(f"Error: Package {p_name} not found.")
            return False

        pack_match = interpreter.packages[p_name]

        t = MatchDictionary.match(interpreter, p_inp, pack_match.p_pat)
        if t:
            forward, backward, _ = t
            new_pred = Predicate(interpreter, name, pack_match.recursive, pack_match.random)
            for basic in pack_match.basic:
                new_pred.addBasic(smart_replace(basic, forward))
            for falsehood in pack_match.nope:
                new_pred.addNot(smart_replace(falsehood, forward))
            for i in range(pack_match.count):
                new_pred.addCase(smart_replace(pack_match.cases[i], forward), smart_replace(pack_match.then[i], forward))

            interpreter.predicates[name] = new_pred

            return True

    def __init__(self, interpreter, name, p_pat, rec, rand):
        """
        Creating an empty Package.

        :param interpreter: Interpreter
        :param name: str
        :param p_pat: str
        :param rec: boolean
        :param rand: boolean
        """
        self.name = name  # Package name
        self.p_pat = p_pat
        self.cases = []  # Predicate cases to match
        self.then = []  # Predicate searches to do if matched with case
        self.basic = []  # Predicate Facts
        self.nope = []  # Predicate False
        self.recursive = rec  # If the predicate is recursive, as son as it matches it stops looking. (Opposite of generative)
        self.random = rand  # Whether to check solutions
        self.count = 0  # Count of cases
        self.interpreter = interpreter  # Interpreter for predicate

    # Adds a case
    def addCase(self, to_match, then):
        """
        Add a translation case to package.

        :param to_match: str, the pattern needs matching
        :param then: str, what to search if the match was successful
        :return: None
        """
        to_match = to_match.strip()
        if len(to_match) == 0:
            self.cases.append('')
            self.then.append(then)
            self.count += 1
            return
        to_match = processParen(to_match)
        if not to_match:
            self.interpreter.raiseError(f"Error: Incomplete parentheses in package {self.name}")
            return
        then = processParen(then)
        if not then:
            self.interpreter.raiseError(f"Error: Incomplete parentheses in package {self.name}")
            return
        if len(to_match) == 0:
            self.cases.append('')
            self.then.append(then)
            self.count += 1
            return
        self.cases.append(to_match)
        self.then.append(then)
        self.count += 1

    # adds a fact
    def addBasic(self, to_match):
        """
        Adding a Fact to package.

        :param to_match: str, pattern to match
        :return: None
        """
        to_match = to_match.strip()
        if len(to_match) == 0:
            self.basic.append('')
            return
        to_match = processParen(to_match)
        if not to_match:
            self.interpreter.raiseError(f"Error: Incomplete parentheses in package {self.name}")
        if len(to_match) == 0:
            self.basic.append('')
            return
        self.basic.append(to_match)

    # adds a false fact
    def addNot(self, to_match):
        """
        Adding a terminal case to package.

        :param to_match: str, pattern to match
        :return: None
        """
        to_match = to_match.strip()
        if len(to_match) == 0:
            self.nope.append('')
            return
        to_match = processParen(to_match)
        if not to_match:
            self.interpreter.raiseError(f"Error: Incomplete parentheses in package {self.name}")
        if len(to_match) == 0:
            self.nope.append('')
            return
        self.nope.append(to_match)

    # Matches to package
    def match(self, p_inp, q_inp):
        """
        Analogous to the match of the predicate class (does a little more than that).
        This matches between a package query with package parameters and query parameters

        :param p_inp: str
        :param q_inp: str
        :return: Generator (search, backward)
        """
        p_match = MatchDictionary.match(self.interpreter, p_inp, self.p_pat)
        if not p_match:
            return False
        p_forward, p_backward, p_wiggle = p_match

        u_cases = list(map(lambda t: smart_replace(t, p_forward), self.cases))
        u_then = list(map(lambda t: smart_replace(t, p_forward), self.then))
        u_not = list(map(lambda t: smart_replace(t, p_forward), self.nope))
        u_base = list(map(lambda t: smart_replace(t, p_forward), self.basic))

        for not_match in u_not:
            q_match = MatchDictionary.match(self.interpreter, q_inp, not_match)
            if q_match and not q_match[2]:
                return False

        for basic in u_base:
            q_match = MatchDictionary.match(self.interpreter, q_inp, basic)
            if not q_match:
                continue
            q_forward, q_backward, _ = q_match
            for p_variable in p_backward:
                p_backward[p_variable] = smart_replace(p_backward[p_variable], q_forward)

            backward = smartUpdate(p_backward, q_backward)
            if self.recursive:
                return

            yield 1, backward

        for i in range(self.count):
            this_case = u_cases[i]
            this_then = u_then[i]

            q_match = MatchDictionary.match(self.interpreter, q_inp, this_case)
            if not q_match:
                continue
            q_forward, q_backward, _ = q_match
            for p_variable in p_backward:
                p_backward[p_variable] = smart_replace(p_backward[p_variable], q_forward)

            forward = smartUpdate(p_forward, q_forward)
            backward = smartUpdate(p_backward, q_backward)
            search = smart_replace(this_then, forward)

            yield search, backward
            if self.recursive:
                return
