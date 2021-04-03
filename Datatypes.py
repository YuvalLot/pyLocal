
from abc import ABC, abstractmethod
from util import match_type, splitWithoutParen, outString
import Match


class AbstractDataStructure(ABC):

    @abstractmethod
    def insert(self, arg):
        pass

    @abstractmethod
    def remove(self, arg):
        pass

    @abstractmethod
    def lookup(self, arg):
        pass

    @abstractmethod
    def clear(self):
        pass


class Dataset(AbstractDataStructure):

    def __init__(self, name):
        self.name = name
        self.set = set()

    def insert(self, value):
        if len(splitWithoutParen(value)) != 1:
            return
        if match_type(value) == "constant":
            self.set.add(value)
            yield {}

    def remove(self, value):
        if value in self.set:
            self.set.remove(value)
            yield {}

    def lookup(self, pattern):
        if len(splitWithoutParen(pattern)) != 1:
            return
        if match_type(pattern) == "constant" and pattern in self.set:
            yield {}
        elif match_type(pattern) == "var":
            for value in self.set:
                yield {pattern: value}

    def clear(self):
        self.set = set()
        yield {}


class Datahash(AbstractDataStructure):

    def __init__(self, interpreter, name):
        self.name = name
        self.interpreter = interpreter
        self.front = {}

    def insert(self, values):
        values = splitWithoutParen(values)
        if len(values) != 2:
            return
        value1, value2 = values

        if match_type(value1) == "constant" and not outString(value2, "?"):
            self.front[value1] = value2
            yield {}

    def lookup(self, values):

        part_values = splitWithoutParen(values)
        if len(part_values) != 2:
            return

        value1, value2 = part_values

        t1 = match_type(value1)

        if t1 == "constant" and value1 in self.front:
            m = Match.MatchDictionary.match(self.interpreter, value2, self.front[value1])
            if m:
                yield m[1]

        else:
            for key, value in self.front.items():
                pair = f"{key},{value}"
                m = Match.MatchDictionary.match(self.interpreter, values, pair)
                if m:
                    yield m[1]

    def remove(self, values):
        part_values = splitWithoutParen(values)
        if len(part_values) != 2:
            return

        value1, value2 = part_values

        t1 = match_type(value1)

        if t1 == "constant" and value1 in self.front:
            m = Match.MatchDictionary.match(self.interpreter, value2, self.front[value1])
            if m:
                del self.front[value1]
                yield {}

        else:
            deleted = False
            for key, value in list(self.front.items()):
                pair = f"{key},{value}"
                m = Match.MatchDictionary.match(self.interpreter, values, pair)
                if m:
                    del self.front[key]
                    deleted = True
            if deleted:
                yield {}

    def clear(self):
        self.front = {}
        yield {}


