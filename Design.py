"""

Design

includes the Console (using tkinter), and connects various pieces of the program, to finally create a UI for uploading rules and
searching for queries.

"""

import threading
from tkinter import *
import sys
from tkinter import filedialog
from win32api import GetSystemMetrics
import Lexer
import Interpreter
from util import *
from time import sleep


class Console:
    """
    Console class uses tkinter elements, and connects them to the Interpreter Class.
    Console also includes a way for the user to upload rules efficiently, as well as search for queries and find the results.
    Moreover, Console can print and get input from the user.
    """

    def __init__(self, version, time_limit, recursion_limit, imports):
        """
        Creates an empty console design using tkinter.

        :param version: the current version of the console
        :param time_limit: the time limit in searches
        :param recursion_limit: the recursion limit in the language
        :param imports: a list of possible libraries to import.
        """
        self.version = version
        self.time_limit = time_limit
        self.recursion_limit = recursion_limit

        # Build Lexer and Interpreter
        self.lexer = Lexer.build()
        self.interpreter = Interpreter.Interpreter(self.time_limit, imports)

        # For Queries
        self.asked_for_more, self.found_more = False, False
        self.requested_input, self.got_input = False, False

        # Get the width and the height of the Page
        width = GetSystemMetrics(0)
        height = GetSystemMetrics(1)

        # define TK
        self.root = Tk()
        self.root.geometry(f"1500x750+{width // 2 - 750}+{height // 2 - 750 // 2}")

        # Handle Arrow Press
        self.root.bind('<Down>', self.downPress)
        self.root.bind('<Up>', self.upPress)

        # define image for tkinter
        p1 = PhotoImage(file= sys.path[0] + '\\Images\\LCL.png')

        # Setting icon of master window
        self.root.iconphoto(False, p1)
        self.root.title("Local")

        # define the main frame
        self.mainFrame = Frame(self.root, highlightbackground="black", highlightthickness=1)
        self.mainFrame.grid(row=0, column=0, padx=(10), pady=(10), sticky=W + E + S + N)

        # configure the grid
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.mainFrame.columnconfigure(1, weight=1)
        self.mainFrame.rowconfigure(1, weight=100)
        self.mainFrame.rowconfigure(2, weight=1)

        # set a variable for the query text and console text
        self.queryText = StringVar()
        self.consoleText = '\n' * 100 + f'Local Version {self.version} Loaded...\n\n'

        # A variable to save the generator in between the first and later results
        self.solutions = None
        self.pastQueries = ['', '']
        self.currentIndex = 1
        self.searching = False

        # Frame for console, and console definition
        self.textFrame = Frame(self.mainFrame, width=10000, height=27000)
        self.textFrame.grid(row=0, column=0, rowspan=2, columnspan=3, sticky=N + S + W + E)
        self.console = Text(self.textFrame, height=1650, width=500, padx=4, pady=4, wrap=WORD, font=("Courier", 12),
                            borderwidth=4, relief="groove")
        self.console.insert(END, self.consoleText)
        self.console.config(state=DISABLED)
        self.console.pack()
        self.scrolling = Scrollbar(self.textFrame)
        self.scrolling.pack(side=RIGHT, fill=Y)
        self.scrolling.config(command=self.console.yview)
        self.console.config(yscrollcommand=self.scrolling.set)
        self.console.see(END)

        # Query button and text
        self.directionsQuery = Label(self.mainFrame, text="Enter Query Here:", font=("Helvetica", 14, "bold"))
        self.directionsQuery.grid(row=3, column=0, padx=(10), pady=(10, 15), sticky=W)
        self.query = Entry(self.mainFrame, font=("Courier", 14), textvariable=self.queryText)
        self.query.grid(row=3, column=1, padx=(10), pady=(10, 20), sticky=S + W + E)
        self.root.bind("<Return>", self.moreSolutions)
        self.sendQuery = Button(self.mainFrame, text='Send Query', command=self.queryReceived, font=("Helvetica", 14))
        self.sendQuery.grid(row=3, column=2, padx=(10), pady=(10, 20), stick=W)

        # upload query
        self.upload = Button(self.mainFrame, text='Upload Rules', command=self.UploadAction, height=4, width=24,
                             font=("Helvetica", 10, "bold"))
        self.upload.grid(row=0, column=0, padx=(10), pady=(10))

        # delete button
        self.delete = Button(self.mainFrame, text='Delete All Rules', command=self.DeleteRules, height=4, width=24,
                             font=("Helvetica", 10, "bold"))
        self.delete.grid(row=0, column=1, padx=(10), pady=(10), sticky='W')

        self.clear = Button(self.mainFrame, text='Clear Console', command=self.ClearConsole, height=4, width=24,
                             font=("Helvetica", 10, "bold"))
        self.clear.grid(row=0, column=2, padx=(10), pady=(10), sticky='E')

        self.sendMessage("", False)

    # Clearing Console
    def ClearConsole(self):
        self.console.config(state=NORMAL)
        self.console.delete(1.0, END)
        self.console.insert(END, 100*"\n")
        self.console.config(state=DISABLED)

    # inserting queries
    def insert(self, q):
        """
        Insert a new query to the list of past queries

        :param q: str
        :return: None
        """
        self.pastQueries = self.pastQueries[:-1] + [q] + [self.pastQueries[-1]]
        self.currentIndex = len(self.pastQueries) - 1

    # Add text to console
    def sendMessage(self, text, new_line=True):
        """
        Adds to console text, and text wanted.
        Allows the deletion of new-line created after last message sent.

        :param text: str
        :param new_line: bool (optainl)
        :return:
        """

        if not new_line:
            self.console.config(state=NORMAL)
            old_text = (self.console.get(1.0, END))
            old_text = old_text[:-1]
            self.console.delete(1.0, END)
            self.console.insert(END, old_text)
            self.console.insert(END, text)
            self.console.config(state=DISABLED)
            self.console.see(END)
            return

        self.console.config(state=NORMAL)
        self.console.insert(END, "\n")
        self.console.insert(END, text)
        self.console.config(state=DISABLED)
        self.console.see(END)

    # Clear the interpreter
    def DeleteRules(self, event=None):
        """
        Delete all rules (by re-initiating the interpreter object)

        :param event: Any
        :return: None
        """
        self.interpreter.deleted = True
        for domain in self.interpreter.domains.values():
            domain.shut_down()
        self.interpreter.__init__(self.interpreter.time_limit, self.interpreter.imports, self.interpreter.path, update_delete=False)
        self.sendMessage("\nAll Rules Deleted\n")
        self.solutions = None

    # For pressing down (navigating between past queries)
    def downPress(self, e=None):
        """
        Navigates between past queries using the down key.

        :param e: Any
        :return: None
        """
        if self.currentIndex == len(self.pastQueries)-1:
            self.queryText.set('')
            return

        self.currentIndex += 1
        self.queryText.set(self.pastQueries[self.currentIndex])
        self.query.icursor(len(self.pastQueries[self.currentIndex]))

    # For pressing up (navigating between queries)
    def upPress(self, e=None):
        """
        Navigates between past queries using the up key.

        :param e: Any
        :return: None
        """

        if self.currentIndex == 0:
            self.queryText.set(self.pastQueries[0])
            return

        self.currentIndex -= 1
        self.queryText.set(self.pastQueries[self.currentIndex])
        self.query.icursor(len(self.pastQueries[self.currentIndex]))

    # Sends messages and errors from interpreter
    def viewErrorsAndMessages(self):
        """
        Prints all errors and messages on the console.

        :return: (boolean, boolean) - representing whether any errors and messages were sent
        """

        errored, messaged = False, False
        if len(self.interpreter.errorLoad) != 0:
            errored = True
            self.solutions = None
            for error in self.interpreter.errorLoad:
                self.sendMessage(f"{error}")
        if len(self.interpreter.messageLoad) != 0:
            messaged = True
            for mes in self.interpreter.messageLoad:
                if self.interpreter.newline:
                    self.sendMessage(f" {mes}", False)
                else:
                    self.sendMessage(f"{mes}")
        self.interpreter.clearErrors()
        return errored, messaged

    # Upload a file with rules
    def UploadAction(self, event=None, arg=None):
        """
        Uploading a file of rules.

        :param event: Any
        :param arg: a filename.
        :return: None
        """
        self.interpreter.deleted = False
        if self.searching:
            return
        if arg is not None:
            filename = arg
        else:
            filename = filedialog.askopenfilename()
            if filename == "":
                return
            print('Selected:', filename)
        try:
            z = open(filename, 'r')
        except FileNotFoundError:
            self.sendMessage("Error: File Not Found")
            return
        self.interpreter.setFilePath("/".join(filename.split("/")[:-1]))
        data = z.read()
        z.close()
        self.lexer.input(data)
        tokens = []

        while True:
            tok = self.lexer.token()
            if not tok:
                break  # No more input
            tokens.append(tok)

        if len(Lexer.SyntaxErrors) != 0:
            for e in Lexer.SyntaxErrors:
                self.sendMessage(e)
            Lexer.SyntaxErrors = []
            return

        try:
            def reader():
                self.interpreter.read(tokens)
                if len(self.interpreter.errorLoad) == 0:
                    self.sendMessage(f"File {filename} has been uploaded.\n")
                else:
                    self.viewErrorsAndMessages()
                self.searching = False
                if "on-start" in self.interpreter.predicates_names:
                    print("hello")
                    self.queryReceived(given="on-start()")
            self.searching = True
            threading.Thread(target=reader).start()
        except Exception as e:
            ed, md = self.viewErrorsAndMessages()
            if not ed:
                self.sendMessage(f"Unknown Error: {e}")

        self.lexer = Lexer.build()

    # showing solutions
    def show_solution(self, not_indp):
        """
        Called as a thread - searching for solutions and printing if found a solution.

        :param not_indp: boolean (whether the input was independent)
        :return: None
        """
        try:
            sol = next_solution(self.solutions, self.time_limit)
            ed, _ = self.viewErrorsAndMessages()
            if ed:
                self.solutions = None
                self.searching = False
                return
            if sol == "Request":
                self.requested_input = True
                self.directionsQuery['text'] = "Enter Input:"
                self.sendQuery['text'] = 'Send Input'
                while not self.got_input:
                    pass
                self.directionsQuery['text'] = 'Enter Query Here:'
                self.sendQuery['text'] = "Send Query"
                self.got_input = False
                self.show_solution(not_indp)
                return
            elif sol == "Print":
                self.show_solution(not_indp)
                return  # TT(or(p, q))
            elif sol == 0 or sol == 3:
                pass
            elif sol == 1:
                self.interpreter.raiseError('Error: Timeout Error')
            elif sol == 2:
                self.interpreter.raiseError('Error: Unknown Error')
            elif sol == {}:
                self.sendMessage('True.\n')
                self.solutions = None
                self.searching = False
                return
            else:
                self.sendMessage(sol)
                self.sendMessage('\nFind More Solutions? (Press Enter)\n')
                self.searching = False
                return
        except Exception as e:
            if type(e) not in [ValueError, RecursionError]:
                raise e
            ed, _ = self.viewErrorsAndMessages()
            if not ed:
                self.sendMessage('Error: Unknown Error')
            self.solutions = None
            self.searching = False
            return

        ed, _ = self.viewErrorsAndMessages()
        if ed:
            self.solutions = None
            self.searching = False
            return

        if not_indp:
            self.sendMessage('False (as far as known)\n')
            self.solutions = None
            self.searching = False
            return

        self.sendMessage(f'No{ {False:"", True:" More"}[self.asked_for_more] } Solutions Found.\n')
        self.solutions = None
        self.searching = False

    # Functions for query: receiving a query, and enter presses for more answers
    def queryReceived(self, event=None, given=None):
        """
        Query received, (asking a query). Also used for user input.

        :param event: Any
        :param given: str
        :return: None
        """

        if self.requested_input:
            inp = self.queryText.get()
            if inp == "":
                return
            self.queryText.set('')
            self.interpreter.received_input = inp
            self.requested_input = False
            self.got_input = True
            return

        if given:
            text_query = given
            type_query = 0

        else:
            if self.searching:
                return
            q = self.queryText.get()
            if q == '':
                return
            self.asked_for_more = False
            self.insert(q)
            self.sendMessage(f"{q} ... searching\n")
            self.queryText.set('')
            processedQuery = processQuery(q)
            if not processedQuery:
                self.sendMessage('Illegal Query')
                return
            type_query, text_query = processedQuery
            text_query = processParen(text_query)
            if not text_query:
                self.sendMessage("Illegal Query, parentheses do not match")
                return

        self.solutions = self.interpreter.mixed_query(text_query, type_query, self.recursion_limit)
        self.searching = True

        try:
            threading.Thread(target=self.show_solution, args=(not independent(text_query), )).start()
        except threading.ThreadError:
            self.sendMessage('Error: Thread Error.')
            self.solutions = None
            self.searching = False

    # More solutions
    def moreSolutions(self, event=None):
        """
        For when enter is pressed - representing a search for more possible solutions.
        If query input is not empty searhces for new query. Also used for user input.

        :param event: Any
        :return: None
        """

        ed, _ = self.viewErrorsAndMessages()
        if self.queryText.get().strip() != '':
            self.queryReceived()
            return
        if self.searching or ed or self.solutions is None:
            return
        else:
            self.asked_for_more = True
            try:
                threading.Thread(target=self.show_solution, args=(False, )).start()
            except threading.ThreadError:
                self.sendMessage('Error: Thread Error.')
                self.solutions = None
                self.searching = None

    # run the code
    def run(self):
        """
        Runs the console (tkinter main loop).

        :return: None
        """
        self.root.mainloop()
