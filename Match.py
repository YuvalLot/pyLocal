"""

Match

Class that matches two patterns, a query pattern and a case pattern

"""
import functools

from util import match_type, smart_replace, splitWithoutParen, processParen, \
    lookup, get_all_basics, processHead


# Class used to match two patterns
class MatchDictionary:
    index = 1

    # A method that receives a datatype list, head or title, and transforms each variable into a new variable
    @classmethod
    def transform(cls, component, basics, target):
        """
        A method that receives a datatype list, head or title, and transforms each variable into a new variable

        :param component: str
        :param basics: list
        :param target: str
        :return:
        """
        r_d = {}  # replacing dictionary for the variables
        for basic in basics:
            if match_type(basic) == 'var':
                if basic in target:
                    new_var = target[basic]
                else:
                    new_var = f"?@{cls.index}"
                    cls.index += 1
                    target[basic] = new_var
                r_d[basic] = new_var

        return smart_replace(component, r_d)

    # DONE
    @classmethod
    def reset(cls):
        cls.index = 1

    # DONE
    def __init__(self, interp):
        self.forward = {}  # the forward direction
        self.backward = {}  # the backward direction
        self.inside = {}
        self.wiggle_room = False  # checks if the matching is essential, i.e. whether it can be avoided
        self.interpreter = interp

    # DONE
    @classmethod
    def match(cls, interp, patternA: str, patternB: str):
        """
        Matches two patterns

        :param interp: Interpreter
        :param patternA: str
        :param patternB: str
        :return: (forward:dict, backward:dict, bool)
        """

        if patternB == "...":
            MD = MatchDictionary(interp)
            forward = {"...": f"[{patternA}]"}
            backward = functools.reduce(lambda a, b: a.update(b) or a, [{d: d for d in get_all_basics(comp) if match_type(d) == "var"} for comp in splitWithoutParen(patternA)], {})
            return forward, backward, False

        MD = MatchDictionary(interp)
        matched = MD.outside_push(patternA, patternB)
        if not matched:
            return False
        MD.o_update()
        return MD.forward, MD.backward, MD.wiggle_room

    def outside_push(self, patternA, patternB):
        try:
            comps_A = splitWithoutParen(patternA)
            comps_B = splitWithoutParen(patternB)
        except TypeError:
            return False

        if len(comps_A) != len(comps_B):
            return False

        for i in range(len(comps_A)):
            compA = comps_A[i]
            compB = comps_B[i]
            success = self.o_single_push(compA, compB)
            if not success:
                return False

        return True

    def o_single_push(self, compA, compB):

        compA = processParen(compA)
        compB = processParen(compB)

        if compB == "_" or compA == "_":
            return True

        if not compA or not compB:
            return

        if any(map(lambda infx: infx in compA, self.interpreter.infixes)):
            compA = lookup(compA, self.interpreter.infixes)
        if any(map(lambda infx: infx in compB, self.interpreter.infixes)):
            compB = lookup(compB, self.interpreter.infixes)

        if not compA or not compB:
            return False

        typeA = match_type(compA)
        typeB = match_type(compB)

        # print(compA, typeA, compB, typeB)

        if typeA in ['list', 'head']:
            compA = processHead(compA)
            typeA = match_type(compA)
        if typeB in ['list', 'head']:
            compB = processHead(compB)
            typeB = match_type(compB)

        if typeA == 'constant' and typeB == 'constant':
            return compA == compB

        # var with var & var with constant
        if typeA == 'var' and typeB == 'var':
            return self.o_var_with_var(compA, compB)
        if typeA == 'var' and typeB == 'constant':
            return self.o_var_with_const(compA, compB)
        if typeA == 'constant' and typeB == 'var':
            return self.o_const_with_var(compA, compB)

        # Lists with vars
        if typeA == 'list' and typeB == 'var':
            return self.o_list_with_var(compA, compB)
        if typeA == 'var' and typeB == 'list':
            return self.o_var_with_list(compA, compB)

        # Appended lists with vars
        if typeA == 'head' and typeB == 'var':
            return self.o_head_with_var(compA, compB)
        if typeA == 'var' and typeB == 'head':
            return self.o_var_with_head(compA, compB)

        # lists with lists, lists with appended lists.
        if typeA == 'list' and typeB == 'list':
            return self.o_list_with_list(compA, compB)
        if typeA == 'head' and typeB == 'head':
            return self.o_head_with_head(compA, compB)
        if typeA == 'list' and typeB == 'head':
            return self.o_list_with_head(compA, compB)
        if typeA == 'head' and typeB == 'list':
            return self.o_head_with_list(compA, compB)

        # titles match
        if typeA == 'title' and typeB == 'title':
            return self.o_title_with_title(compA, compB)
        if typeA == 'var' and typeB == 'title':
            return self.o_var_with_title(compA, compB)
        if typeA == 'title' and typeB == 'var':
            return self.o_title_with_var(compA, compB)

        # Packages match
        if typeA == 'pack' and typeB == 'pack':
            return self.o_pack_with_pack(compA, compB)
        if typeA == 'pack' and typeB == 'var':
            return self.o_pack_with_var(compA, compB)
        if typeA == 'var' and typeB == 'pack':
            return self.o_var_with_pack(compA, compB)

        return False

    def o_var_with_var(self, q_var, c_var):

        q_exists = q_var in self.backward.keys()
        c_exists = c_var in self.forward.keys()

        if q_exists and c_exists:
            q_to = self.backward[q_var]
            c_to = self.forward[c_var]
            return self.i_single_push(q_to, c_to)

        elif c_exists:
            self.wiggle_room = True
            self.backward[q_var] = self.forward[c_var]
            return True

        elif q_exists:
            self.forward[c_var] = self.backward[q_var]
            return True

        else:
            new_var = f"?@{MatchDictionary.index}"
            MatchDictionary.index += 1
            self.forward[c_var] = new_var
            self.backward[q_var] = new_var
            return True

    def o_const_with_var(self, q_const, c_var):

        c_exists = c_var in self.forward.keys()

        if c_exists:
            return self.i_single_push(q_const, self.forward[c_var])
        else:
            self.forward[c_var] = q_const
            return True

    def o_var_with_const(self, q_var, c_const):

        self.wiggle_room = True
        q_exists = q_var in self.backward.keys()

        if q_exists:
            return self.i_single_push(c_const, self.backward[q_var])
        else:
            self.backward[q_var] = c_const
            return True

    def o_list_with_list(self, q_list, c_list):
        return self.outside_push(q_list[1:-1], c_list[1:-1])

    def o_var_with_list(self, q_var, c_list):

        self.wiggle_room = True

        if q_var in self.backward.keys():
            q_to = self.backward[q_var]
            c_basics = get_all_basics(c_list)
            c_trans = MatchDictionary.transform(c_list, c_basics, self.forward)
            matched = self.i_single_push(q_to, c_trans)
            if not matched:
                return False
            self.backward[q_var] = smart_replace(self.backward[q_var], self.inside)
            for b in c_basics:
                if match_type(b) == 'var' and self.forward[b] in self.inside.keys():
                    self.forward[b] = self.inside[self.forward[b]]
            return True

        else:
            c_basics = get_all_basics(c_list)
            c_trans = MatchDictionary.transform(c_list, c_basics, self.forward)
            self.backward[q_var] = c_trans
            return True

    def o_list_with_var(self, q_list, c_var):
        if c_var in self.forward.keys():
            c_to = self.forward[c_var]
            q_basics = get_all_basics(q_list)
            q_trans = MatchDictionary.transform(q_list, q_basics, self.backward)
            matched = self.i_single_push(c_to, q_trans)
            if not matched:
                return False
            self.forward[c_var] = smart_replace(self.forward[c_var], self.inside)
            for b in q_basics:
                if match_type(b) == 'var' and self.backward[b] in self.inside.keys():
                    self.backward[b] = self.inside[self.backward[b]]
            return True

        else:
            q_basics = get_all_basics(q_list)
            q_trans = MatchDictionary.transform(q_list, q_basics, self.backward)
            self.forward[c_var] = q_trans
            return True

    def o_head_with_head(self, q_head, c_head):
        q_comps = splitWithoutParen(q_head[1:-1], "*")
        c_comps = splitWithoutParen(c_head[1:-1], "*")
        if len(q_comps) != 2 or len(c_comps) != 2:
            return False
        return self.o_single_push(q_comps[0], c_comps[0]) and self.o_single_push(q_comps[1], c_comps[1])

    def o_var_with_head(self, q_var, c_head):

        self.wiggle_room = True

        if q_var in self.backward.keys():
            q_to = self.backward[q_var]
            c_basics = get_all_basics(c_head, "*")
            c_trans = MatchDictionary.transform(c_head, c_basics, self.forward)
            matched = self.i_single_push(q_to, c_trans)
            if not matched:
                return False
            self.backward[q_var] = smart_replace(self.backward[q_var], self.inside)
            for b in c_basics:
                if self.forward[b] in self.inside.keys():
                    self.forward[b] = self.inside[self.forward[b]]
            return True

        else:
            c_basics = get_all_basics(c_head, "*")
            c_trans = MatchDictionary.transform(c_head, c_basics, self.forward)
            self.backward[q_var] = c_trans
            return True

    def o_head_with_var(self, q_head, c_var):
        if c_var in self.forward.keys():
            c_to = self.forward[c_var]
            q_basics = get_all_basics(q_head, "*")
            q_trans = MatchDictionary.transform(q_head, q_basics, self.backward)
            matched = self.i_single_push(c_to, q_trans)
            if not matched:
                return False
            self.forward[c_var] = smart_replace(self.forward[c_var], self.inside)
            for b in q_basics:
                if match_type(b) == "var" and self.backward[b] in self.inside.keys():
                    self.backward[b] = self.inside[self.backward[b]]
            return True

        else:
            q_basics = get_all_basics(q_head, "*")
            q_trans = MatchDictionary.transform(q_head, q_basics, self.backward)
            self.forward[c_var] = q_trans
            return True

    def o_list_with_head(self, q_list, c_head):
        if q_list == "[]":
            return False
        q_comps = splitWithoutParen(q_list[1:-1])
        c_comps = splitWithoutParen(c_head[1:-1], "*")
        if len(c_comps) != 2:
            return False
        return self.o_single_push(q_comps[0], c_comps[0]) and self.o_single_push("[" + ",".join(q_comps[1:]) + "]", c_comps[1])

    def o_head_with_list(self, q_head, c_list):

        self.wiggle_room = True

        if c_list == "[]":
            return False
        q_comps = splitWithoutParen(q_head[1:-1], "*")
        c_comps = splitWithoutParen(c_list[1:-1])
        if len(q_comps) != 2:
            return False
        return self.o_single_push(q_comps[0], c_comps[0]) and self.o_single_push(q_comps[1], "[" + ",".join(c_comps[1:]) + "]")

    def o_title_with_title(self, q_title, c_title):

        q_name, _, q_pat = q_title.partition("(")
        q_pat = q_pat[:-1]

        c_name, _, c_pat = c_title.partition("(")
        c_pat = c_pat[:-1]

        if q_name != c_name:
            return False

        return self.outside_push(q_pat, c_pat)

    def o_var_with_title(self, q_var, c_title):

        self.wiggle_room = True

        c_name, _, c_pat = c_title.partition("(")

        if q_var in self.backward.keys():
            q_to = self.backward[q_var]
            c_basics = get_all_basics(c_title)
            c_trans = MatchDictionary.transform(c_title, c_basics, self.forward)
            matched = self.i_single_push(q_to, c_trans)
            if not matched:
                return False
            for b in c_basics:
                if match_type(b) == 'var' and self.forward[b] in self.inside.keys():
                    self.forward[b] = self.inside[self.forward[b]]
            return True
        else:
            c_basics = get_all_basics(c_title)
            c_trans = MatchDictionary.transform(c_title, c_basics, self.forward)
            self.backward[q_var] = c_trans
            return True

    def o_title_with_var(self, q_title, c_var):

        q_name, _, q_pat = q_title.partition("(")

        if c_var in self.forward.keys():
            c_to = self.forward[c_var]
            q_basics = get_all_basics(q_title)
            q_trans = MatchDictionary.transform(q_title, q_basics, self.backward)
            matched = self.i_single_push(c_to, q_trans)
            if not matched:
                return False
            self.forward[c_var] = smart_replace(self.forward[c_var], self.inside)
            for b in q_basics:
                if match_type(b) == 'var' and self.backward[b] in self.inside.keys():
                    self.backward[b] = self.inside[self.backward[b]]
            return True

        else:
            q_basics = get_all_basics(q_title)
            q_trans = MatchDictionary.transform(q_title, q_basics, self.backward)
            self.forward[c_var] = q_trans
            return True

    def o_pack_with_pack(self, q_pack, c_pack):
        q_name, _, q_pat = q_pack.partition("{")
        q_pat = q_pat[:-1]
        c_name, _, c_pat = c_pack.partition("{")
        c_pat = c_pat[:-1]

        if q_name != c_name or q_name not in self.interpreter.packages_names:
            return False

        return self.outside_push(q_pat, c_pat)

    def o_var_with_pack(self, q_var, c_pack):

        c_name, _, c_pat = c_pack.partition("{")

        if c_name not in self.interpreter.packages_names:
            return False

        if q_var in self.backward.keys():
            q_to = self.backward[q_var]
            c_basics = get_all_basics(c_pack)
            c_trans = MatchDictionary.transform(c_pack, c_basics, self.forward)
            matched = self.i_single_push(q_to, c_trans)
            if not matched:
                return False
            for b in c_basics:
                if match_type(b) == 'var' and self.forward[b] in self.inside.keys():
                    self.forward[b] = self.inside[self.forward[b]]
            return True
        else:
            c_basics = get_all_basics(c_pack)
            c_trans = MatchDictionary.transform(c_pack, c_basics, self.forward)
            self.backward[q_var] = c_trans
            return True

    def o_pack_with_var(self, q_pack, c_var):

        q_name, _, q_pat = q_pack.partition("{")

        if q_name not in self.interpreter.packages_names:
            return False

        if c_var in self.forward.keys():
            c_to = self.forward[c_var]
            q_basics = get_all_basics(q_pack)
            q_trans = MatchDictionary.transform(q_pack, q_basics, self.backward)
            matched = self.i_single_push(c_to, q_trans)
            if not matched:
                return False
            self.forward[c_var] = smart_replace(self.forward[c_var], self.inside)
            for b in q_basics:
                if match_type(b) == 'var' and self.backward[b] in self.inside.keys():
                    self.backward[b] = self.inside[self.backward[b]]
            return True

        else:
            q_basics = get_all_basics(q_pack)
            q_trans = MatchDictionary.transform(q_pack, q_basics, self.backward)
            self.forward[c_var] = q_trans
            return True

    """
    inside pushes : dealing only with managing the inside dictionary, 
                    a dictionary that doesn't have anything to do with 
                    with the forward and  
    """

    def inside_push(self, patternA, patternB):
        comps_A = splitWithoutParen(patternA)
        comps_B = splitWithoutParen(patternB)

        if len(comps_A) != len(comps_B):
            return False

        for i in range(len(comps_A)):
            compA = comps_A[i]
            compB = comps_B[i]
            success = self.i_single_push(compA, compB)
            if not success:
                return False

        return True

    def i_single_push(self, compA, compB):

        if compA == "_" or compB == "_":
            return True

        typeA = match_type(compA)
        typeB = match_type(compB)

        if typeA in ['list', 'head']:
            compA = processHead(compA)
            typeA = match_type(compA)
        if typeB in ['list', 'head']:
            compB = processHead(compB)
            typeB = match_type(compB)

        if typeA == 'constant' and typeB == 'constant':
            return compA == compB

        matched = False
        # var with var & var with constant
        if typeA == 'var' and typeB == 'var':
            matched = self.i_var_with_var(compA, compB)
        if typeA == 'var' and typeB == 'constant':
            matched = self.i_const_with_var(compB, compA)
        if typeA == 'constant' and typeB == 'var':
            matched = self.i_const_with_var(compA, compB)

        # Lists with vars
        if typeA == 'list' and typeB == 'var':
            matched = self.i_var_with_list(compB, compA)
        if typeA == 'var' and typeB == 'list':
            matched = self.i_var_with_list(compA, compB)

        # Appended lists with vars
        if typeA == 'head' and typeB == 'var':
            matched = self.i_var_with_head(compB, compA)
        if typeA == 'var' and typeB == 'head':
            matched = self.i_var_with_head(compA, compB)

        # lists with lists, lists with appended lists.
        if typeA == 'list' and typeB == 'list':
            matched = self.i_list_with_list(compA, compB)
        if typeA == 'head' and typeB == 'head':
            matched = self.i_head_with_head(compA, compB)
        if typeA == 'list' and typeB == 'head':
            matched = self.i_list_with_head(compA, compB)
        if typeA == 'head' and typeB == 'list':
            matched = self.i_list_with_head(compB, compA)

        # titles match
        if typeA == 'title' and typeB == 'title':
            matched = self.i_title_with_title(compA, compB)
        if typeA == 'var' and typeB == 'title':
            matched = self.i_var_with_title(compA, compB)
        if typeA == 'title' and typeB == 'var':
            matched = self.i_var_with_title(compB, compA)

        # Package match
        if typeA == 'pack' and typeB == 'pack':
            matched = self.i_pack_with_pack(compA, compB)
        if typeA == 'var' and typeB == 'pack':
            matched = self.i_var_with_pack(compA, compB)
        if typeA == 'pack' and typeB == 'var':
            matched = self.i_var_with_pack(compB, compA)

        if not matched:
            return False

        self.update()
        return True

    def i_var_with_var(self, i1_var, i2_var):

        if i1_var == i2_var:
            return True

        i1_exists = i1_var in self.inside.keys()
        i2_exists = i2_var in self.inside.keys()

        if i1_exists and i2_exists:
            success = self.i_single_push(self.inside[i1_var], self.inside[i2_var])
            if not success:
                return False
            self.inside[i1_var] = smart_replace(self.inside[i1_var], self.inside)
            self.inside[i2_var] = smart_replace(self.inside[i2_var], self.inside)
            return True
        elif i1_exists:
            self.inside[i2_var] = self.inside[i1_var]
            return True
        elif i2_exists:
            self.inside[i1_var] = self.inside[i2_var]
            return True
        else:
            self.inside[i1_var] = i2_var
            return True

    def i_const_with_var(self, i1_const, i2_var):

        i2_exists = i2_var in self.inside.keys()

        if i2_exists:
            return self.i_single_push(i1_const, self.inside[i2_var])
        else:
            self.inside[i2_var] = i1_const
            return True

    def i_list_with_list(self, i1_list, i2_list):
        return self.inside_push(i1_list[1:-1], i2_list[1:-1])

    def i_var_with_list(self, i1_var, i2_list):
        i2_list = smart_replace(i2_list, self.inside)
        if i1_var + "," in i2_list or i1_var + "]" in i2_list or i1_var + "*" in i2_list or i1_var + ")" in i2_list:
            return False
        if i1_var in self.inside.keys():
            i1_to = self.inside[i1_var]
            matched = self.i_single_push(i1_to, i2_list)
            if not matched:
                return False
            return True
        else:
            self.inside[i1_var] = i2_list
            return True

    def i_head_with_head(self, i1_head, i2_head):
        i1_comps = splitWithoutParen(i1_head[1:-1], "*")
        i2_comps = splitWithoutParen(i2_head[1:-1], "*")
        if len(i1_comps) != 2 or len(i2_comps) != 2:
            return False
        return self.o_single_push(i1_comps[0], i2_comps[0]) and self.o_single_push(i1_comps[1], i2_comps[1])

    def i_var_with_head(self, i1_var, i2_head):
        i2_head = smart_replace(i2_head, self.inside)
        if i1_var + "," in i2_head or i1_var + "]" in i2_head or i1_var + "*" in i2_head or i1_var + ")" in i2_head:
            return False
        if i1_var in self.inside.keys():
            i1_to = self.inside[i1_var]
            matched = self.i_single_push(i1_to, i2_head)
            if not matched:
                return False
            return True
        else:
            self.inside[i1_var] = i2_head
            return True

    def i_list_with_head(self, i1_list, i2_head):
        if i1_list == "[]":
            return False
        i1_comps = splitWithoutParen(i1_list[1:-1])
        i2_comps = splitWithoutParen(i2_head[1:-1], "*")
        if len(i2_comps) != 2:
            return False
        return self.i_single_push(i1_comps[0], i2_comps[0]) and self.i_single_push("[" + ",".join(i1_comps[1:]) + "]", i2_comps[1])

    def i_title_with_title(self, i1_title, i2_title):
        i1_name, _, i1_pat = i1_title.partition("(")
        i1_pat = i1_pat[:-1]
        i2_name, _, i2_pat = i2_title.partition("(")
        i2_pat = i2_pat[:-1]
        if i1_name != i2_name:
            return False
        return self.inside_push(i1_pat, i2_pat)

    def i_var_with_title(self, i1_var, i2_title):
        i2_title = smart_replace(i2_title, self.inside)
        if i1_var + "," in i2_title or i1_var + "]" in i2_title or i1_var + "*" in i2_title or i1_var + ")" in i2_title:
            return False
        if i1_var in self.inside.keys():
            i1_to = self.inside[i1_var]
            matched = self.i_single_push(i1_to, i2_title)
            if not matched:
                return False
            return True
        else:
            self.inside[i1_var] = i2_title
            return True

    def i_pack_with_pack(self, i1_pack, i2_pack):
        i1_name, _, i1_pat = i1_pack.partition("{")
        i1_pat = i1_pat[:-1]
        i2_name, _, i2_pat = i2_pack.partition("{")
        i2_pat = i2_pat[:-1]
        if i1_name != i2_name:
            return False
        return self.inside_push(i1_pat, i2_pat)

    def i_var_with_pack(self, i1_var, i2_pack):
        i2_pack = smart_replace(i2_pack, self.inside)
        if i1_var + "," in i2_pack or i1_var + "]" in i2_pack or i1_var + "*" in i2_pack or i1_var + ")" in i2_pack:
            return False
        if i1_var in self.inside.keys():
            i1_to = self.inside[i1_var]
            matched = self.i_single_push(i1_to, i2_pack)
            if not matched:
                return False
            return True
        else:
            self.inside[i1_var] = i2_pack
            return True

    def update(self):

        found_repeat = False
        for i_key in self.inside:
            new_value = smart_replace(self.inside[i_key], self.inside)
            if new_value != self.inside[i_key]:
                self.inside[i_key] = new_value
                found_repeat = True
        if found_repeat:
            self.update()
            return

    def o_update(self):

        for q_key in self.backward.keys():
            if match_type(self.backward[q_key]) == 'var':
                if self.backward[q_key] in self.inside.keys():
                    self.backward[q_key] = self.inside[self.backward[q_key]]
            else:
                self.backward[q_key] = processHead(smart_replace(self.backward[q_key], self.inside))

        for c_key in self.forward.keys():
            if match_type(self.forward[c_key]) == 'var':
                if self.forward[c_key] in self.inside.keys():
                    self.forward[c_key] = self.inside[self.forward[c_key]]
            else:
                self.forward[c_key] = processHead(smart_replace(self.forward[c_key], self.inside))


if __name__ == "__main__":
    class Foo:
        titles = ['^+', '^-', '^*', '^/', '^d>'] + ["mem"]
        infixes = titles
        packages_names = ["Addition"]


    pA = '?x,?y,?z'
    pB = '...'

    # SampleTree(?x) & BinaryTree(?x)

    print(MatchDictionary.match(Foo, pA, pB))
