"""

Interpreter

Includes three classes: Predicate, Query and Interpreter, with the Interpreter class connecting all classes.
This file is the main solving engine that fuels the back chaining algorithm in Local

"""
from typing import Dict

from Domain import Domain
from util import processParen, splitWithoutParen, smart_replace, \
    Counter, processConnectClause, processSolutionDict, match_type
from Match import MatchDictionary
import Lexer
import sys
from collections import deque
import re
from Predicate import Predicate
from Package import Package
from Query import Query
from Datatypes import Dataset, Datahash, AbstractDataStructure


# Interpreter class
class Interpreter:

    # adds message
    def message(self, string):
        """
        Add to the message queue (used for printing and warnings)

        :param string: str
        :return: None
        """
        self.messageLoad.append(string)

    # adds error
    def raiseError(self, string):
        """
        Add to th error load of interpreter.

        :param string:
        :return: None
        """
        self.errorLoad.append(string)

    # Clears errors
    def clearErrors(self):
        """
        Clears all errors.

        :return: None
        """
        self.errorLoad = []
        self.messageLoad = []

    # Empty Interpreter
    def __init__(self, time_limit, imports, path=None, update_delete=True):
        """
        Initiate an empty interpreter. Interpreter read lines of codes and builds database. It also navigates between the different components
        of problem solving.

        :param time_limit: float
        :param imports: list of str
        :param path: str (path to imports, used in unit testing)
        """

        if update_delete:
            self.deleted = False

        # For Printing
        self.newline = False

        if path is None:
            self.path = sys.path[0]
        else:
            self.path = path

        self.predicates = {}  # Predicates dictionary

        self.packages = {}  # Packages Dictionary

        self.errorLoad = []  # List of Errors Raised
        self.messageLoad = []  # List of messages

        self.time_limit = time_limit  # time limit in searches
        self.imports = imports  # list of possible imports (libraries)

        self.math_added = False  # Math Library added
        self.list_added = False  # List Library added
        self.types_added = False  # Types Library added
        self.predicates_added = False  # Predicates Library added
        self.save_added = False  # Save Library added
        self.strings_added = False  # String Library added
        self.inspect_added = False  # Inspect Library Added
        self.dynamic_added = False  # Facts Library Added
        self.ref_added = False

        self.filestream_added = False  # Filestream Library Added
        self.files = {}

        self.saved = deque([])  # Stack of saved - for Save Library
        self.trace_on = False  # For Trace, in Inspect Library

        self.titles = []  # List of titles.
        self.infixes = []  # List of infixes

        self.domains = {}

        self.memory = []
        self.references = {}

        self.datasets: Dict[str, AbstractDataStructure] = {}
        self.datahashes: Dict[str, AbstractDataStructure] = {}

        self.objects = {}

        self.macros = {}  # Macro dictionary between name->(pattern, query, success, failure)

        self.pythons = {}

        self.received_input = False  # Requesting input from console

        self.filepath = None  # for imports and such

    def setFilePath(self, path):
        """
        when a new file is uploaded.

        :param path: str
        :return: None
        """
        self.filepath = path

    # For building connect predicates
    @staticmethod
    def buildThen(string: str):

        string = processParen(string)
        if not string:
            return False

        splitByAnd = splitWithoutParen(string, "&")
        if len(splitByAnd) > 1:
            then = ""
            for clause in splitByAnd:
                partial_then = Interpreter.buildThen(clause)
                if not partial_then:
                    return False
                then += "(" + partial_then + ")"
                then += "&"
            return then[:-1]

        splitByAnd = splitWithoutParen(string, "|")
        if len(splitByAnd) > 1:
            then = ""
            for clause in splitByAnd:
                partial_then = Interpreter.buildThen(clause)
                if not partial_then:
                    return False
                then += "(" + partial_then + ")"
                then += "|"
            return then[:-1]

        splitByAnd = splitWithoutParen(string, "$")
        if len(splitByAnd) > 1:
            then = ""
            for clause in splitByAnd:
                partial_then = Interpreter.buildThen(clause)
                if not partial_then:
                    return False
                then += "(" + partial_then + ")"
                then += "$"
            return then[:-1]

        searchForFilter = splitWithoutParen(string, "~")
        if len(searchForFilter) != 1:
            if len(searchForFilter) != 2 or searchForFilter[0] != '':
                return False
            return "~" + Interpreter.buildThen(searchForFilter[1])

        parts = splitWithoutParen(string, "+")

        d_con, d_reg = {}, {}
        for i, part in enumerate(parts):
            if re.fullmatch(r'[a-zA-Z_0-9\-\.]+', part) or re.fullmatch(r'[a-zA-Z_0-9\-\.]+:.+', part) or re.fullmatch(r'\[(.| |,|\n)*]',
                                                                                                                                        part):
                d_con[i] = part
            elif re.fullmatch(r'\{.+\}', part):
                d_reg[i] = part[1:-1]
            else:
                print(part)
                return False

        if len(d_con) == 0:
            return "E(?inp,?out)&" + "&".join(d_reg.values())

        con_keys = list(d_con.keys())

        if len(d_con) == 1:
            d_con[con_keys[0]] = processConnectClause(d_con[con_keys[0]], "?inp", "?out")

        else:
            first_key = con_keys[0]
            d_con[first_key] = processConnectClause(d_con[first_key], "?inp", "?temp1")

            index = 1
            for con_ind in con_keys[1:-1]:
                d_con[con_ind] = processConnectClause(d_con[con_ind], f"?temp{index}", f"?temp{index + 1}")
                index += 1

            last_key = con_keys[-1]
            d_con[last_key] = processConnectClause(d_con[last_key], f"?temp{index}", "?out")

        processed_parts = []
        for i in range(len(parts)):
            if i in con_keys:
                processed_parts.append(d_con[i])
            else:
                processed_parts.append(d_reg[i])

        return "&".join(processed_parts)

    # Reading tokens and creating predicates (main compiling)
    def read(self, tokens):
        """
        Reads tokens handed from the Lexer and creates predicates, titles, infixes, packages and imports based on the tokens inputted.

        :param tokens: List of tokens
        :return: None
        """

        # starting tokens : ('PACKAGE', 'IMP', 'SET', 'EXTEND', 'USE', 'CONNECT', 'DOMAIN')
        properties = ('recursive', 'generative', 'random')
        line = 1

        # Package Variables
        in_pack = False
        new_package = None
        package_rand = False
        package_recursive = False
        package_name = ''
        package_param = ''
        package_case = ''
        package_then = ''

        # Sub
        in_sub = False

        opened_pack_param = False
        closed_pack_param = False
        opened_pack_prop = False
        closed_pack_prop = False
        opened_pack_prop_second = False
        closed_pack_prop_second = False
        moved_to_cases_pack = False
        moved_to_then_pack = False

        # Setting Variables
        in_set = False
        new_predicate = None
        predicate_name = ''
        predicate_rand = False
        predicate_recursive = False
        predicate_case = ''
        predicate_then = ''

        opened_predicate_prop = False
        opened_predicate_prop_second = False
        closed_predicate_prop = False
        closed_predicate_prop_second = False
        moved_to_cases_predicate = False
        moved_to_then_predicate = False

        # Domain
        in_domain = False
        new_domain = None
        domain_name = ""

        domain_entered_vars = False
        domain_variables = ""

        domain_new_range = False
        domain_var_range = ""
        domain_moved_to_search = False
        domain_range = ""

        domain_moved_to_const = False
        domain_const = ""
        domain_is_const = False
        domain_elim = ""
        domain_moved_to_when = False
        domain_when = ""

        domain_moved_to_final = False
        domain_final = ""

        # Import Variables
        in_imp = False
        imp_name = ''

        # Extending Variables
        in_ext = False
        ext_case = ""
        ext_then = ""
        ext_predicate = None
        ext_predicate_name = ""
        moved_to_then_ext = False
        moved_to_cases_ext = False

        # Use Variables
        in_use = False
        use_package = ''
        use_moved_to_name = False
        use_predicate_name = ''
        use_end_name = False

        use_build_queue = {}

        # Declare variables
        in_declare = False
        ready_for_dec = False
        title_declared = ""

        # Dataset variables
        in_dataset = False
        ready_for_dataset = False
        dataset_declared = ""

        # Datahash variables
        in_datahash = False
        ready_for_datahash = False
        datahash_declared = False

        # Infix variables
        in_infix = False
        ready_for_infix = False
        infix_declared = ""

        sum_of_ins = lambda: \
            int(in_imp) + int(in_ext) + int(in_set) + int(in_use) + int(in_pack) + int(in_declare) + int(in_con) + int(in_macro) + int(in_domain) + \
            int(in_dataset) + int(in_datahash)
        more_than_one = lambda: sum_of_ins() > 1
        at_least_one = lambda: sum_of_ins() > 0

        # Connect Variables
        in_con = False
        con_name = ''
        con_moved_to_out = False
        con_output = ''
        con_moved_to_then = False
        con_then = ''

        # Macros
        in_macro = False
        macro_name = ""
        macro_moved = 0
        macro_pattern = ""
        macro_query = ""
        macro_success = ""
        macro_failure = ""

        for token in tokens:

            if token.type == "PYTHON":
                python_text = token.value[8:-9].strip()
                exec(python_text, self.pythons)
                line += token.value.count("\n")

            elif token.type == "SUBS":
                line += token.value.count("\n")

            elif token.type == 'NEWLINE':
                line += 1
                continue

            elif token.type == 'BUNDLE':
                continue

            elif token.type == "EXCLAMATION" and not at_least_one():
                in_macro = True
                if more_than_one():
                    self.raiseError(f'Error: Attempting to define a macro inside another statement, in line {line}.')
                    return

            elif token.type == 'MULTILINECOMMENT':
                line += token.value

            elif token.type == 'IMP':
                if in_imp:
                    self.raiseError(f'Error: can not import inside an import, in line {line}.')
                    return
                in_imp = True
                if more_than_one():
                    self.raiseError(f'Error: Attempting to import inside another statement, in line {line}.')
                    return
                in_imp = True

            elif token.type == 'DOMAIN':
                if in_domain:
                    self.raiseError(f'Error: can declare a domain inside another domain, in line {line}.')
                    return
                in_domain = True
                if more_than_one():
                    self.raiseError(f'Error: Attempting to declare a domain inside another statement, in line {line}.')
                    return
                in_domain = True

            elif token.type == 'SET':
                if in_set:
                    self.raiseError(f'Error: can not set inside another set, in line {line}')
                    return
                in_set = True
                if more_than_one():
                    self.raiseError(f'Error: Attempting to set a predicate inside another statement, in line {line}')
                    return
                in_set = True

            elif token.type == 'EXTEND':
                if in_ext:
                    self.raiseError(f'Error: can not extend inside another extend, in line {line}')
                    return
                in_ext = True
                if more_than_one():
                    self.raiseError(f'Error: Attempting to extend a predicate inside another statement, in line {line}')
                    return

            elif token.type == 'USE':
                if in_use:
                    self.raiseError(f'Error: can not use inside another use, in line {line}')
                    return
                in_use = True
                if more_than_one():
                    self.raiseError(f'Error: Attempting to use a package inside another statement, in line {line}')
                    return

            elif token.type == 'PACKAGE':

                if in_pack:
                    self.raiseError(f'Error: can not package inside another package, in line {line}')
                    return
                in_pack = True
                if more_than_one():
                    self.raiseError(f'Error: Attempting to define package inside another statement, in line {line}')
                    return

            elif token.type == 'DECLARE':
                if in_declare:
                    self.raiseError(f'Error: can not declare inside another declaration, in line {line}')
                    return
                in_declare = True
                ready_for_dec = True
                if more_than_one():
                    self.raiseError(f'Error: Attempting to declare titles inside another statement, in line {line}')
                    return

            elif token.type == 'DATASET':
                if in_dataset:
                    self.raiseError(f'Error: can not declare dataset inside another declaration, in line {line}')
                    return
                in_dataset = True
                ready_for_dataset = True
                if more_than_one():
                    self.raiseError(f'Error: Attempting to declare dataset inside another statement, in line {line}')
                    return

            elif token.type == 'DATAHASH':
                if in_datahash:
                    self.raiseError(f'Error: can not declare datahash inside another declaration, in line {line}')
                    return
                in_datahash = True
                ready_for_datahash = True
                if more_than_one():
                    self.raiseError(f'Error: Attempting to declare datahash inside another statement, in line {line}')
                    return

            elif token.type == "INFIX":
                if in_infix:
                    self.raiseError(f'Error: can not declare inside another declaration, in line {line}')
                    return
                in_infix = True
                ready_for_infix = True
                if more_than_one():
                    self.raiseError(f'Error: Attempting to declare titles inside another statement, in line {line}')
                    return

            elif token.type == 'CON':
                if in_con:
                    self.raiseError(f'Error: can not connect inside another connect, in line {line}')
                    return
                in_con = True
                if more_than_one():
                    self.raiseError(f'Error: Attempting to connect a predicate inside another statement, in line {line}')
                    return
                in_con = True

            elif token.type == 'SEMI':

                if in_domain:
                    if not domain_name or new_domain is None:
                        self.raiseError(f"Error: Domain declaration missing, in line {line}")
                        return
                    if not domain_moved_to_const:
                        if not new_domain.insert_range(domain_var_range, domain_range, line):
                            return
                    if not new_domain.complete():
                        self.raiseError(f"Error: In domain {domain_name}, some domain variables missing, in line {line}")
                        return
                    if not domain_moved_to_const:
                        self.raiseError(f"Error: Must specify constraints in domain {domain_name}, in line {line}")
                        return
                    if domain_const != "":
                        if not new_domain.insert_constraint(domain_const, domain_when, line):
                            print(f"This caused an error, '{domain_const}'")
                            return
                    if domain_elim != "":
                        if not new_domain.insert_elimination(domain_elim, domain_when, line):
                            return
                    if domain_moved_to_final:
                        new_domain.insert_final(domain_final)

                    self.domains[new_domain.name] = new_domain

                    # reset domain vars
                    in_domain = False
                    new_domain = None
                    domain_name = ""

                    domain_entered_vars = False
                    domain_variables = ""

                    domain_new_range = False
                    domain_var_range = ""
                    domain_moved_to_search = False
                    domain_range = ""

                    domain_moved_to_const = False
                    domain_const = ""
                    domain_is_const = False
                    domain_elim = ""
                    domain_moved_to_when = False
                    domain_when = ""

                    domain_moved_to_final = False
                    domain_final = ""

                if in_imp:
                    in_imp = False
                    imp_name = ''

                if in_pack:

                    if package_name == "" or not closed_pack_param:
                        self.raiseError(f"Error: Illegal declaration of package, in line {line}.")
                        return

                    if new_package is None:
                        new_package = Package(self, package_name, package_param, package_recursive, package_rand)

                    if package_case != "" or moved_to_cases_pack:
                        if package_then == "":
                            new_package.addBasic(package_case)
                        elif package_then == "NOT":
                            new_package.addNot(package_case)
                        else:
                            new_package.addCase(package_case, package_then)

                    self.packages[new_package.name] = new_package

                    # Package Reset
                    in_pack = False
                    new_package = None
                    package_rand = False
                    package_recursive = False
                    package_name = ''
                    package_param = ''
                    package_case = ''
                    package_then = ''

                    opened_pack_param = False
                    closed_pack_param = False
                    opened_pack_prop = False
                    closed_pack_prop = False
                    opened_pack_prop_second = False
                    closed_pack_prop_second = False
                    moved_to_cases_pack = False
                    moved_to_then_pack = False

                if in_set:

                    if predicate_name == "":
                        self.raiseError(f"Error: Illegal declaration of predicate, in line {line}")
                        return

                    if new_predicate is None:
                        new_predicate = Predicate(self, predicate_name, predicate_recursive, predicate_rand)
                        predicate_case = ""

                    if predicate_case != "" or moved_to_cases_predicate:
                        if predicate_then.strip() == "":
                            new_predicate.addBasic(predicate_case)
                        elif predicate_then == "NOT":
                            new_predicate.addNot(predicate_case)
                        else:
                            new_predicate.addCase(predicate_case, predicate_then)

                    self.predicates[new_predicate.name] = new_predicate

                    # Setting Predicate Reset
                    in_set = False
                    new_predicate = None
                    predicate_name = ''
                    predicate_rand = False
                    predicate_recursive = False
                    predicate_case = ''
                    predicate_then = ''

                    opened_predicate_prop = False
                    opened_predicate_prop_second = False
                    closed_predicate_prop = False
                    closed_predicate_prop_second = False
                    moved_to_cases_predicate = False
                    moved_to_then_predicate = False

                if in_use:
                    use_build_queue[use_predicate_name] = use_package

                    # Use Reset
                    in_use = False
                    use_package = ''
                    use_moved_to_name = False
                    use_predicate_name = ''
                    use_end_name = False

                if in_ext:
                    if ext_case != "":
                        if ext_then == "":
                            ext_predicate.addBasic(ext_case)
                        elif ext_then == "NOT":
                            ext_predicate.addNot(ext_case)
                        else:
                            ext_predicate.addCase(ext_case, ext_then)
                    in_ext = False
                    ext_case = ''
                    ext_then = ''
                    ext_predicate = None
                    ext_predicate_name = ''
                    moved_to_cases_ext = False
                    moved_to_then_ext = False

                if in_declare:
                    if ready_for_dec:
                        self.raiseError(f"Error: Declaration missing, in line {line}")
                        return
                    if title_declared == "":
                        self.raiseError(f"Error: Declaration missing, in line {line}")
                        return
                    self.titles.append(title_declared)
                    in_declare = False
                    ready_for_dec = False
                    title_declared = ''

                if in_dataset:
                    if ready_for_dataset:
                        self.raiseError(f"Error: Dataset declaration missing, in line {line}")
                        return
                    if dataset_declared == "":
                        self.raiseError(f"Error: Dataset declaration missing, in line {line}")
                        return
                    if dataset_declared in self.datahashes or dataset_declared in self.datasets:
                        self.raiseError(f"Error: Name '{dataset_declared}' already in use, in line {line}")
                        return
                    self.datasets[dataset_declared] = (Dataset(dataset_declared))
                    in_dataset = False
                    ready_for_dataset = False
                    dataset_declared = ''

                if in_datahash:
                    if ready_for_datahash:
                        self.raiseError(f"Error: Datahash declaration missing, in line {line}")
                        return
                    if datahash_declared == "":
                        self.raiseError(f"Error: Datahash declaration missing, in line {line}")
                        return
                    if datahash_declared in self.datahashes or datahash_declared in self.datasets:
                        self.raiseError(f"Error: Name '{datahash_declared}' already in use, in line {line}")
                        return
                    self.datahashes[datahash_declared] = (Datahash(self, dataset_declared))
                    in_datahash = False
                    ready_for_datahash = False
                    datahash_declared = ''

                if in_infix:
                    if ready_for_infix:
                        self.raiseError(f"Error: Infix declaration missing, in line {line}")
                        return
                    if infix_declared == "":
                        self.raiseError(f"Error: Infix declaration missing, in line {line}")
                        return
                    self.titles.append(infix_declared)
                    self.infixes.append(infix_declared)
                    in_infix = False
                    ready_for_infix = False
                    infix_declared = ''

                if in_con:

                    if con_name == "":
                        self.raiseError(f"Error: Must supply a connect name, in line {line}")
                        return
                    if not con_moved_to_then:
                        self.raiseError(f"Error: Must set a connect pattern, in line {line}")
                        return

                    if con_output == "":
                        con_case = "?inp,?out"
                    else:
                        con_case = f"?inp,?out,{con_output}"

                    con_then = self.buildThen(con_then)
                    if not con_then:
                        self.raiseError(f"Error: Illegal connect pattern of Predicate '{con_name}', in line {line}")
                        return
                    if con_name not in self.predicates:
                        con_pred = Predicate(self, con_name, False, False)
                        self.predicates[con_name] = con_pred
                    else:
                        con_pred = self.predicates[con_name]

                    con_pred.addCase(con_case, con_then)

                    in_con = False
                    con_name = ''
                    con_moved_to_out = False
                    con_output = ''
                    con_moved_to_then = False
                    con_then = ''

                if in_macro:
                    if macro_moved != 4:
                        self.raiseError(f"Error: too few macro components, in line {line}")
                        return
                    macro_pattern = processParen(macro_pattern)
                    if not macro_pattern and macro_pattern != "":
                        self.raiseError(f"Error: Illegal macro pattern, in line {line}")
                        return
                    if macro_query == "":
                        self.raiseError(f"Error: macro query empty, in line {line}")
                        return
                    if macro_success == "":
                        self.raiseError(f"Error: macro success empty, in line {line}")
                        return
                    if macro_failure == "":
                        self.raiseError(f"Error: macro failure empty, in line {line}")
                        return
                    self.macros[macro_name] = (macro_pattern, macro_query, macro_success, macro_failure)
                    in_macro = False
                    macro_name = ""
                    macro_moved = 0
                    macro_pattern = ""
                    macro_query = ""
                    macro_success = ""
                    macro_failure = ""

            elif in_macro:
                if macro_name == "":
                    macro_name = token.value
                    if token.type != 'NAME':
                        self.raiseError(f"Error: Macro Name '{ext_predicate_name}' illegal, in line {line}")
                        return

                elif macro_moved == 0:
                    if token.type != "EXCLAMATION":
                        self.raiseError(f"Error: must separate macro components by '!', in line {line}")
                        return
                    elif macro_name == "":
                        self.raiseError(f"Error: must declare a macro name, in line {line}")
                        return
                    macro_moved = 1

                elif token.type == "EXCLAMATION":
                    macro_moved += 1

                elif macro_moved == 1:
                    macro_pattern += token.value

                elif macro_moved == 2:
                    macro_query += token.value

                elif macro_moved == 3:
                    macro_success += token.value

                elif macro_moved == 4:
                    macro_failure += token.value

                else:
                    self.raiseError(f"Error: too many macro components, in line {line}")
                    return

            elif in_imp:
                imp_name = token.value
                if imp_name in self.imports:
                    if imp_name == 'Inspect':
                        self.inspect_added = True
                        continue
                    if imp_name == 'Dynamic':
                        self.dynamic_added = True
                        continue
                    if imp_name == 'List':
                        self.list_added = True
                    if imp_name == 'Math':
                        self.math_added = True
                    if imp_name == 'Types':
                        self.types_added = True
                    if imp_name == 'Predicates':
                        self.predicates_added = True
                    if imp_name == 'Save':
                        self.save_added = True
                    if imp_name == 'Strings':
                        self.strings_added = True
                    if imp_name == 'Filestream':
                        self.filestream_added = True
                    if imp_name == 'Reference':
                        self.ref_added = True
                    import_name = self.path + f"\\Imports\\{imp_name}.LCL"
                    import_name_2 = ""
                else:
                    if token.type != "FILENAME":
                        self.raiseError(f"Error: Imports must begin with '@', in line {line}")
                        return
                    import_name = f"{imp_name}.LCL"
                    import_name_2 = self.filepath + "/" + f"{imp_name}.LCL"
                lexer = Lexer.build()
                try:
                    f = open(import_name, "r")
                except FileNotFoundError:
                    try:
                        f = open(import_name_2, "r")
                    except FileNotFoundError:
                        self.raiseError(f"Error: Missing import {import_name}, in line {line}")
                        return
                lexer.input(f.read())
                new_tokens = []
                while True:
                    tok = lexer.token()
                    if not tok:
                        break  # No more input
                    new_tokens.append(tok)

                if len(Lexer.SyntaxErrors) != 0:
                    self.raiseError(Lexer.SyntaxErrors[0])
                    Lexer.SyntaxErrors = []
                    return

                self.read(new_tokens)
                f.close()

            elif in_ext:
                if ext_predicate_name == "":
                    ext_predicate_name = token.value
                    if token.type != 'NAME':
                        self.raiseError(f"Error: Predicate Name '{ext_predicate_name}' illegal, in line {line}")
                        return
                    if ext_predicate_name not in self.predicates:
                        self.raiseError(f"Error: Attempting to extend predicate '{ext_predicate_name}' that has yet to be set.")
                        return
                    ext_predicate = self.predicates[ext_predicate_name]
                elif token.type == 'CASE':
                    if not moved_to_cases_ext:
                        moved_to_cases_ext = True
                        moved_to_then_ext = False
                    if ext_case != "":
                        if ext_then == "":
                            ext_predicate.addBasic(ext_case)
                        elif ext_then == "NOT":
                            ext_predicate.addNot(ext_case)
                        else:
                            ext_predicate.addCase(ext_case, ext_then)

                    ext_case = ''
                    ext_then = ''
                    moved_to_then_ext = False

                elif moved_to_cases_ext:
                    if token.type == 'THEN':
                        moved_to_then_ext = True
                        if ext_case == "":
                            ext_case = " "
                    elif moved_to_then_ext:
                        ext_then += token.value
                    else:
                        ext_case += token.value

                else:
                    self.raiseError(f"Error: Illegal token '{token.value}', in line {line}")
                    return

            elif in_pack:
                if package_name == "":
                    package_name = token.value
                    if token.type != 'NAME':
                        self.raiseError(f"Error: Package Name '{package_name}' illegal, in line {line}")
                        return
                elif token.type == 'LCURLY' and not closed_pack_param and not moved_to_cases_pack:
                    if opened_pack_param and not moved_to_cases_pack:
                        self.raiseError(f"Error: double use of '{'{'}', in line {line}")
                        return
                    opened_pack_param = True
                elif opened_pack_param and not closed_pack_param:
                    if token.type == 'RCURLY':
                        closed_pack_param = True
                    else:
                        package_param += token.value
                elif token.type == 'AS':
                    if opened_pack_prop:
                        self.raiseError(f"Error: can't define properties inside properties, in line {line}")
                        return
                    opened_pack_prop = True
                elif opened_pack_prop and not closed_pack_prop:
                    if token.value not in properties:
                        self.raiseError(f"Error: unknown property '{token.value}', in line {line}")
                    if token.value == 'recursive':
                        package_recursive = True
                    if token.value == 'random':
                        package_rand = True
                    closed_pack_prop = True
                elif closed_pack_prop and token.type == 'COMMA' and not moved_to_cases_pack:
                    if opened_predicate_prop_second:
                        self.raiseError(f"Error: can't define more than two properties, in line {line}")
                        return
                    opened_pack_prop_second = True
                elif opened_pack_prop_second and not closed_pack_prop_second:
                    if token.value not in properties:
                        self.raiseError(f"Error: unknown property '{token.value}', in line {line}")
                    if token.value == 'recursive':
                        package_recursive = True
                    if token.value == 'random':
                        package_rand = True
                    closed_pack_prop_second = True

                elif token.type == 'CASE':
                    if not moved_to_cases_pack:
                        new_package = Package(self, package_name, package_param, package_recursive, package_rand)
                    moved_to_cases_pack = True

                    if package_case != "":
                        if package_then == "":
                            new_package.addBasic(package_case)
                        elif package_then == "NOT":
                            new_package.addNot(package_case)
                        else:
                            new_package.addCase(package_case, package_then)

                    package_case = ''
                    package_then = ''
                    moved_to_then_pack = False

                elif moved_to_cases_pack:
                    if token.type == 'THEN':
                        moved_to_then_pack = True
                        if package_case == "":
                            package_case = " "
                    elif moved_to_then_pack:
                        package_then += token.value
                    else:
                        package_case += token.value

                else:
                    self.raiseError(f"Error: Illegal token '{token.value}', in line {line}")
                    return

            elif in_set:
                if predicate_name == "":
                    predicate_name = token.value
                    if token.type != 'NAME':
                        self.raiseError(f"Error: Predicate Name '{predicate_name}' illegal, in line {line}")
                        return
                elif token.type == 'AS':
                    if opened_predicate_prop:
                        self.raiseError(f"Error: can't define properties inside properties, in line {line}")
                        return
                    opened_predicate_prop = True
                elif opened_predicate_prop and not closed_predicate_prop:
                    if token.value not in properties:
                        self.raiseError(f"Error: unknown property '{token.value}', in line {line}")
                        return
                    if token.value == 'recursive':
                        predicate_recursive = True
                    if token.value == 'random':
                        predicate_rand = True
                    closed_predicate_prop = True
                elif closed_predicate_prop and token.type == 'COMMA' and not moved_to_cases_predicate:
                    if opened_predicate_prop_second:
                        self.raiseError(f"Error: can't define more than two properties, in line {line}")
                        return
                    opened_predicate_prop_second = True
                elif opened_predicate_prop_second and not closed_predicate_prop_second:
                    if token.value not in properties:
                        self.raiseError(f"Error: unknown property '{token.value}', in line {line}")
                        return
                    if token.value == 'recursive':
                        predicate_recursive = True
                    if token.value == 'random':
                        predicate_rand = True
                    closed_predicate_prop_second = True
                elif token.type == 'CASE':
                    if not moved_to_cases_predicate:
                        new_predicate = Predicate(self, predicate_name, predicate_recursive, predicate_rand)
                    moved_to_cases_predicate = True

                    if predicate_case != "":
                        if predicate_then == "":
                            new_predicate.addBasic(predicate_case)
                        elif predicate_then == "NOT":
                            new_predicate.addNot(predicate_case)
                        else:
                            new_predicate.addCase(predicate_case, predicate_then)

                    predicate_case = ''
                    predicate_then = ''
                    moved_to_then_predicate = False

                elif moved_to_cases_predicate:
                    if token.type == 'THEN':
                        moved_to_then_predicate = True
                        if predicate_case == "":
                            predicate_case = " "
                    elif moved_to_then_predicate:
                        predicate_then += token.value
                    else:
                        predicate_case += token.value

                else:
                    self.raiseError(f"Error: Illegal token '{token.value}', in line {line}")
                    return

            elif in_use:
                if token.type == 'AS':
                    use_moved_to_name = True
                elif not use_moved_to_name:
                    use_package += token.value
                elif use_moved_to_name and not use_end_name:
                    use_predicate_name = token.value
                    if token.type != 'NAME':
                        self.raiseError(f"Error: Predicate Name '{use_predicate_name}' illegal, in line {line}")
                        return
                else:
                    self.raiseError(f"Error: Illegal token '{token.value}', in line {line}")
                    return

            elif in_declare:
                if token.type == 'COMMA':
                    if ready_for_dec:
                        self.raiseError(f"Error: Declarations separated by one comma only, in line {line}")
                        return
                    self.titles.append(title_declared)
                    ready_for_dec = True
                else:
                    if token.type != "NAME":
                        self.raiseError(f"Error: Illegal name for declaration: '{token.value}', in line {line}")
                        return
                    if not ready_for_dec:
                        self.raiseError(f"Error: Declarations separated by a comma, in line {line}")
                        return
                    title_declared = token.value
                    ready_for_dec = False

            elif in_dataset:
                if token.type == 'COMMA':
                    if ready_for_dataset:
                        self.raiseError(f"Error: Dataset declarations separated by one comma only, in line {line}")
                        return
                    if dataset_declared in self.datahashes or dataset_declared in self.datasets:
                        self.raiseError(f"Error: Name '{dataset_declared}' already in use, in line {line}")
                        return
                    self.datasets[dataset_declared] = Dataset(dataset_declared)
                    ready_for_dataset = True
                else:
                    if token.type != "NAME":
                        self.raiseError(f"Error: Illegal name for dataset: '{token.value}', in line {line}")
                        return
                    if not ready_for_dataset:
                        self.raiseError(f"Error: Dataset declarations separated by a comma, in line {line}")
                        return
                    dataset_declared = token.value
                    ready_for_dataset = False

            elif in_datahash:
                if token.type == 'COMMA':
                    if ready_for_datahash:
                        self.raiseError(f"Error: Datahash declarations separated by one comma only, in line {line}")
                        return
                    if datahash_declared in self.datahashes or datahash_declared in self.datasets:
                        self.raiseError(f"Error: Name '{datahash_declared}' already in use, in line {line}")
                        return
                    self.datahashes[datahash_declared] = Datahash(self, datahash_declared)
                    ready_for_datahash = True
                else:
                    if token.type != "NAME":
                        self.raiseError(f"Error: Illegal name for datahash: '{token.value}', in line {line}")
                        return
                    if not ready_for_datahash:
                        self.raiseError(f"Error: Datahash declarations separated by a comma, in line {line}")
                        return
                    datahash_declared = token.value
                    ready_for_datahash = False

            elif in_infix:
                if token.type == 'COMMA':
                    if ready_for_infix:
                        self.raiseError(f"Error: Declarations of infixes separated by one comma only, in line {line}")
                        return
                    self.titles.append(infix_declared)
                    self.infixes.append(infix_declared)
                    ready_for_infix = True
                else:
                    if token.type != "OP":
                        self.raiseError(f"Error: Illegal name for infix declaration: '{token.value}', in line {line}")
                        return
                    if not ready_for_infix:
                        self.raiseError(f"Error: Declarations of infixes separated by a comma, in line {line}")
                        return
                    infix_declared = token.value
                    ready_for_infix = False

            elif in_con:
                if con_name == "":
                    if token.type != "NAME":
                        self.raiseError(f"Error: Predicate Name '{token.value}' illegal, in line {line}")
                        return
                    else:
                        con_name = token.value

                elif token.type == 'COLON' and not con_moved_to_then:
                    if con_moved_to_out:
                        self.raiseError(f"Error: Double colon, in line {line}")
                        return
                    if con_name == "":
                        self.raiseError(f"Error: Must choose name before setting output, in line {line}")
                        return
                    else:
                        con_moved_to_out = True

                elif con_moved_to_out and not con_moved_to_then and token.type != "EQ":
                    con_output += token.value

                elif token.type == 'EQ':
                    if con_moved_to_then:
                        self.raiseError(f"Error: Equal inside compound connect, in line {line}")
                        return
                    else:
                        con_moved_to_then = True

                else:
                    if not con_moved_to_then:
                        self.raiseError(f"Error: Illegal token '{token.value}', in line {line}")
                    con_then += token.value

            elif in_domain:
                if domain_name == "":
                    if token.type != "NAME":
                        self.raiseError(f"Error: Domain Name '{token.value}' illegal, in line {line}")
                        return
                    domain_name = token.value
                    new_domain = Domain(self, domain_name)

                elif token.type == "OF":
                    domain_moved_to_search = False
                    domain_new_range = True
                    if not domain_variables:
                        self.raiseError(f"Error: Domain {domain_name} without variables, in line {line}")
                        return

                    if domain_moved_to_const:
                        self.raiseError(f"Error: Domain {domain_name} already defined constraints, in line {line}")
                        return

                    if domain_entered_vars:
                        domain_entered_vars = False
                        if not new_domain.insert_variables(domain_variables, line):
                            return
                        domain_new_range = True

                    else:
                        if not domain_range:
                            self.raiseError(f"Error: In domain {domain_name}, attempting to define a range of new variable "
                                            f"with an empty definition for {domain_var_range}, in line {line}")
                            return
                        if not new_domain.insert_range(domain_var_range, domain_range, line):
                            return
                        domain_var_range = ""
                        domain_range = ""

                elif token.type == "OVER":
                    if domain_entered_vars:
                        self.raiseError(f"Error: Domain variables defines twice, in line {line}")
                        return
                    domain_entered_vars = True

                elif token.type == "WHEN":
                    if not domain_moved_to_const or (not domain_const and not domain_elim):
                        self.raiseError(f"Error: Illegal when statement, in line {line}")
                        return
                    if domain_moved_to_when:
                        self.raiseError(f"Error: When inside When in Domain {domain_name}, in line {line}")
                        return
                    domain_moved_to_when = True

                elif token.type == "CONST":
                    domain_is_const = True
                    if domain_moved_to_const:
                        if domain_const != "":
                            if not new_domain.insert_constraint(domain_const, domain_when, line):
                                return
                        if domain_elim != "":
                            if not new_domain.insert_elimination(domain_elim, domain_when, line):
                                return
                    else:
                        if not new_domain.insert_range(domain_var_range, domain_range, line):
                            return
                        domain_moved_to_const = True
                    domain_const = ""
                    domain_elim = ""
                    domain_moved_to_when = False
                    domain_when = ""

                elif token.type == "ELIM":
                    domain_is_const = False
                    if domain_moved_to_const:
                        if domain_const != "":
                            if not new_domain.insert_constraint(domain_const, domain_when, line):
                                return
                        if domain_elim != "":
                            if not new_domain.insert_elimination(domain_elim, domain_when, line):
                                return
                    else:
                        if not new_domain.insert_range(domain_var_range, domain_range, line):
                            return
                        domain_moved_to_const = True
                    domain_const = ""
                    domain_elim = ""
                    domain_moved_to_when = False
                    domain_when = ""

                elif token.type == "FINAL":
                    domain_moved_to_final = True

                elif domain_moved_to_final:
                    domain_final += token.value

                elif domain_entered_vars and not domain_new_range and not domain_moved_to_const:
                    domain_variables += token.value

                elif token.type == "COLON":
                    if domain_moved_to_const:
                        self.raiseError(f"Error: Illegal colon, in line {line}")
                        return
                    domain_moved_to_search = True

                elif domain_new_range and not domain_moved_to_const and not domain_when:
                    if not domain_moved_to_search:
                        if domain_var_range != "":
                            self.raiseError(f"Error: Single domain variable, in line {line}")
                            return
                        domain_var_range = token.value
                    else:
                        domain_range += token.value

                elif domain_moved_to_const and not domain_moved_to_when:
                    if domain_is_const:
                        domain_const += token.value
                    else:
                        domain_elim += token.value

                elif domain_moved_to_when:
                    domain_when += token.value

                else:
                    self.raiseError(f"Error: Illegal token '{token.value}', in line {line}")
                    return

            else:
                self.raiseError(f"Error: Illegal start of statement '{token.value}', in line {line}")
                return

        if at_least_one():
            self.raiseError(f"Error: Unclosed statement at EOF.")
            return

        if len(use_build_queue) != 0:
            for np in use_build_queue.keys():
                Package.createPredicateFromPackage(self, use_build_queue[np], name=np)

        # print(self.errorLoad)
        # self.showPredicates()
        # self.showPackages()
        # self.showDeclarations()\
        # print(self.datasets, self.datahashes)

    # Prints predicates
    def showPredicates(self):
        """
        Prints all the predicates (useful for debugging)

        :return: None
        """
        for predicate in self.predicates.values():
            print(f"Predicate {predicate.name}: ")
            for basic in predicate.basic:
                print(f"Basic Match {basic}")
            for falsehood in predicate.nope:
                print(f"Falsehood {falsehood}")
            for i in range(predicate.count):
                print(f"Case {predicate.cases[i]} then {predicate.then[i]}")
            print()

    # Prints Packages
    def showPackages(self):
        """
        Prints all the packages (useful for debugging)

        :return: None
        """
        for package in self.packages.values():
            print(f"Package {package.name} with input {package.p_pat}: ")
            for basic in package.basic:
                print(f"Basic Match {basic}")
            for falsehood in package.nope:
                print(f"Falsehood {falsehood}")
            for i in range(package.count):
                print(f"Case {package.cases[i]} then {package.then[i]}")
            print()

    # Prints declarations
    def showDeclarations(self):
        """
        Prints all the titles and infixes (useful for debugging)

        :return: None
        """
        print(f"Titles: {self.titles}")
        print(f"Infixes: {self.infixes}")

    # Macros
    def macroSimplified(self, pat, depth, simplify_arrow=False):
        """
        Simplifies macro expressions.

        :param simplify_arrow: bool
        :param depth: Counter
        :param pat: str
        :return: str
        """
        if not pat.strip():
            return ""
        final = []
        for comp in splitWithoutParen(pat):
            t = match_type(comp)
            if ">" in comp:
                if simplify_arrow:
                    a, _, b = comp.partition(">")
                    final.append(f"{self.macroSimplified(a, depth)}>{self.macroSimplified(b, depth)}")
                else:
                    final.append(comp)
            elif t == "var" or t == "constant":
                final.append(comp)
            elif t == "list":
                final.append("[" + self.macroSimplified(comp[1:-1], depth) + "]")
            elif t == "head":
                head, tail = splitWithoutParen(comp[1:-1], "*")
                head = self.macroSimplified(head, depth)
                tail = self.macroSimplified(tail, depth)
                final.append(f"[{head}*{tail}]")
            elif t == "pack":
                pass
            else:  # t == "title"
                title, _, sub_comp = comp.partition("(")
                sub_comp = sub_comp[:-1]
                tup = self.macros.get(title, None)
                if tup:
                    macro_pat, macro_query, macro_success, macro_failure = tup
                    m = MatchDictionary.match(self, sub_comp, macro_pat)
                    if m:
                        search_for = smart_replace(macro_query, m[0])
                        try:
                            sol_gen = self.mixed_query(search_for, 0, depth, unP=True)
                            solution = next(sol_gen)
                            while type(solution) == str:
                                solution = next(sol_gen)
                            this_macro_success = smart_replace(macro_success, m[0])
                            final.append(
                                self.macroSimplified(smart_replace(this_macro_success, solution), depth)
                            )
                        except StopIteration:
                            this_macro_failure = smart_replace(macro_failure, m[0])
                            final.append(
                                self.macroSimplified(this_macro_failure, depth)
                            )
                    else:
                        return None
                else:
                    sub_comp = self.macroSimplified(sub_comp, depth)
                    final.append(f"{title}({sub_comp})")

        return ",".join(final)

    # For inputting queries
    def mixed_query(self, query, type_query, recursion_limit, unP=False):
        """
        Searches for queries. Creates a query, searches for it, keeps track of already sent solutions and process the final solution from
        dictionary form to string form.

        :param query: str
        :param type_query: int (0-regular, 1-assertive)
        :param recursion_limit: int
        :param unP: boolean (unprocessed solutions)
        :return: None
        """

        if not unP and not self.save_added:
            self.references = {}
            self.memory = []

            for file in self.files.values():
                file.close()
            self.files = {}

        original_recursion_limit = recursion_limit
        self.newline = False
        MatchDictionary.reset()
        Q = Query.create(self, query)
        if not Q:
            return
        sent_solutions = []
        if type(recursion_limit) is not Counter:
            recursion_limit = Counter(recursion_limit)
        for solution in Q.search(recursion_limit):
            if solution == "Request":
                yield "Request"
                continue
            if solution == "Print":
                yield "Print"
                continue

            # print(f"Final Solution {solution}")

            if type_query == 1:
                flag = False
                trial_query = Query.create(self, smart_replace(query, solution))
                for _ in trial_query.search(recursion_limit):
                    flag = True
                    break
                if not flag:
                    continue

            if solution in sent_solutions:
                continue
            sent_solutions.append(solution)
            if unP:
                yield solution
            else:
                processed_solution = processSolutionDict(solution)
                yield processed_solution
                recursion_limit.count = original_recursion_limit

        # print(self.memory, "\n", self.references)


if __name__ == '__main__':
    print(Interpreter.buildThen("(A+B)&(C+D)|(G+H+V)&K"))
