from copy import deepcopy

from Match import MatchDictionary
from util import processParen, splitWithoutParen, outString, smart_replace, match_type


class Domain:

    def __init__(self, intrp, name):
        self.interpreter = intrp
        self.name = name
        self.variables = []
        self.raw_vars = ""
        self.range_searches = {}
        self.constraints = {}
        self.eliminations = {}
        self.ranges = {}

    def complete(self):
        if set(self.variables) != set(self.range_searches.keys()):
            return False
        return True

    def insert_variables(self, variables, line):
        self.raw_vars = variables
        self.variables = splitWithoutParen(variables)
        if any(match_type(var) != "var" for var in self.variables):
            self.interpreter.raiseError(f"Error: Illegal variables of domain {self.name}, in line {line}")
            return False
        return True

    def insert_range(self, variable, range_search, line):
        if variable not in self.variables:
            self.interpreter.raiseError(f"Error: Variable {variable} not part of Domain {self.name}, in line {line}")
            return False
        range_search = processParen(range_search)
        if not range_search:
            self.interpreter.raiseError(f"Error: Illegal range search in Domain {self.name} of variable {variable}, in line {line}")
            return False
        if variable in self.range_searches:
            self.interpreter.raiseError(f"Error: In Domain {self.name}, variable {variable} already has a defined range, in line {line}")
            return False
        self.range_searches[variable] = range_search
        return True

    def insert_constraint(self, const, line):
        const = processParen(const)
        if not const:
            self.interpreter.raiseError(f"Error: In Domain {self.name}, constraint {const} illegal, in line {line}")
            return False
        self.constraints[const] = {var for var in self.variables if outString(const, var)}
        return True

    def insert_elimination(self, elim, line):
        elim = processParen(elim)
        if not elim:
            self.interpreter.raiseError(f"Error: In Domain {self.name}, elimination {elim} illegal, in line {line}")
            return False
        self.eliminations[elim] = {var for var in self.variables if outString(elim, var)}
        return True

    def generate_ranges(self, depth):
        if self.ranges:
            return
        for var in self.variables:
            if var not in self.range_searches:
                self.ranges = None
                return
            self.ranges[var] = set()
            for search in self.interpreter.mixed_query(self.range_searches[var], 0, depth, True):
                if var in search:
                    self.ranges[var].add(search[var])

    def search(self, depth, query_pat):
        parts = splitWithoutParen(query_pat)
        if len(parts) != len(self.variables):
            return
        self.generate_ranges(depth)

        ranges = deepcopy(self.ranges)
        fixed = {}

        # print(f"Original ranges {ranges}")
        for i, part in enumerate(parts):
            var = self.variables[i]
            for option in self.ranges[var]:
                if not MatchDictionary.match(self.interpreter, part, option):
                    ranges[var].remove(option)
                if len(ranges[var]) == 0:
                    return
                if len(ranges[var]) == 1:
                    fixed[var] = next(iter(ranges[var]))
                    del ranges[var]
                    break
        # print(f"domain ranges {ranges}, with fixed {fixed}\n")
        yield from self.solve(depth, ranges, fixed)

    def solve(self, depth, ranges, fixed, rel_const = None, rel_elim = None):

        if rel_const is None:
            rel_const = self.constraints
        if rel_elim is None:
            rel_elim = self.eliminations

        if self.interpreter.deleted:
            # print("Weird Error lol")
            self.interpreter.deleted = False
            return

        # print(f"With fixed {fixed}, the ranges are {ranges}")

        var = next(iter(ranges))
        rng = ranges[var]

        for option in rng:

            new_ranges = ranges.copy()
            del new_ranges[var]
            new_fixed = fixed.copy()
            new_fixed[var] = option
            new_consts = deepcopy(rel_const)
            new_elim = deepcopy(rel_elim)

            if not self.update_range(depth, new_ranges, new_fixed, new_consts, new_elim):
                continue
            if len(new_ranges) == 0:
                yield new_fixed
            yield from self.solve(depth, new_ranges, new_fixed)

    def update_range(self, depth, ranges, fixed, consts, elims):

        for const in list(consts.keys()):
            possible_sols = {}
            # var: set() for var in consts[const] if var not in fixed

            new_set = set()

            for var in consts[const]:
                if var in fixed:
                    pass
                else:
                    possible_sols[var] = set()
                    new_set.add(var)

            consts[const] = new_set

            if len(possible_sols) == len(self.constraints[const]):
                continue

            original_const = const
            const = smart_replace(const, fixed)

            if len(possible_sols) == 0:
                try:
                    next(self.interpreter.mixed_query(const, 0, depth, True))
                    del consts[original_const]
                    continue
                except StopIteration:
                    return False

            for sol in self.interpreter.mixed_query(const, 0, depth, True):
                # print(f"Solution to {const} is {sol}, with possible solutions {possible_sols}")
                for var in possible_sols:
                    if var in sol:
                        possible_sols[var].add(sol[var])

            # ex5usingDOM(?1, ?2, ?3, ?4, ?5, ?6)
            for var in possible_sols:
                if any(match_type(possible_value) == "var" for possible_value in possible_sols[var]):
                    continue
                ranges[var] = ranges[var].intersection(possible_sols[var])
                if len(ranges[var]) == 0:
                    return False

        for elim in list(elims.keys()):
            impossible_sols = {var: set() for var in self.eliminations[elim] if var not in fixed}

            new_set = set()

            for var in elims[elim]:
                if var in fixed:
                    pass
                else:
                    impossible_sols[var] = set()
                    new_set.add(var)

            elims[elim] = new_set

            if len(impossible_sols) == len(self.eliminations[elim]):
                continue
            original_elim = elim
            elim = smart_replace(elim, fixed)
            if len(impossible_sols) == 0:
                try:
                    next(self.interpreter.mixed_query(elim, 0, depth, True))
                    print(f"Exited due to {elim}")
                    return False
                except StopIteration:
                    del elims[original_elim]
                    continue
            elim = smart_replace(elim, fixed)
            for sol in self.interpreter.mixed_query(elim, 0, depth, True):
                # print(f"Solution to {elim} is {sol}, with possible solutions {possible_sols}")
                for var in impossible_sols:
                    if var in sol:
                        impossible_sols[var].add(sol[var])
            for var in impossible_sols:
                ranges[var] = ranges[var].difference(impossible_sols[var])
                if len(ranges[var]) == 0:
                    return False
        return True


if __name__ == "__main__":
    pass