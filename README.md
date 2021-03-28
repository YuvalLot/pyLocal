# PyLocal

### Goal
The goal of this project is to create a new programming language that is of the logical pardaigm.
Logical languages is largely based around formal logic and pattern matching. This langugae, called Local (or logic case langugae) is makes use of AI algorithms (particularly string matching, backchaining, constraint propogation) to solve Queries - these are questions asked by the programmer that are meant to be solved using the rules that the programmer has inputted by the programmer prior to the Query searching. For this project I have made and perfected a method of smart pattern matching between strings. 

### Installation
To install one could either download the source file, or the exe. The downloaded files require a few python libraries. 
A much more extensive explanation is [available](https://docs.google.com/document/d/1kgv_ApvLOi7FfVBAVtID-wjRNqBVUOVn-WBu5yKOiQg/view#) (in hebrew).

### Atoms
Atoms are the basic building blocks of the language. Almost anything can be an atom:
* steve
* Steve45
* 365
* The_Sun
* The-Moon
* Apples_and_Oranges
* _____---000
* "hello world"
Notice that numbers and strings are considered atoms, as they are constants that do not change.
### Unknowns (variables)
In the logical paradigm, variables do not represent, as they do in the procedural paradigm, changing objects. Rather they have more in common with unknowns from mathmetics. This is because a variable can take many values, but only some values will satisfy a paradigm. Consider the variable **x** in the equation _x+5=7_. As an independant variable, x can surely take any value. but in this particular relationship (equation), x has one satisfactory value. Variables are denoted by a question mark and then an identifier. E.g
* ?d
* ?rest
* ?hello_world
* ?1
* ?___

### Comments
Comments are denoted by #. Multiline comments are contained within (\* \*).

### Pattern Matching
Pattern matching is the process that matches two sequences of objects (Variables, Atoms, Lists,...)
Pattern A | Pattern B | Match
----------|-----------|---------
?x, ?y | ?a, ?b | ?x = ?a, ?y = ?b
1, 2, 3 | ?a, ?b, ?c | 1 = ?a, 2 = ?b, ?c = 3
?a | ?b, ?c | No Match

### Predicates
Predictaes are to logical programming, as functions are to Procedural. Predicates are, in essence, properties or relations that certian objects have with one another. For example, being of the color yellow might be a predicate, a father-son relationship might be a predictae, and anything else that could potentially describe a feature of an object or relation between things.

A predicate case is the way predicates are defined. A predictae case includes a pattern to match, and a further search to make (if wanted). For example, if we wanted to know if _?x_ and _?y_ are married, we might say the pattern needs matching is _(?x, ?y)_ and the further search might be searching if _?x_ and _?y_ had a wedding. This would be written as follows:
```
set Married
  case (?x, ?y) then Had_Wedding(?x, ?y);
```
Notice the _set_ keyword declares a new predictae, _case_ declares a pattern to match, _then_ declares a further search, and a semicolon is necessary to close a predictae. Cases without further searches, are known as facts (or basic matches). These are matches that will always hold. For example, we might add to our _Married_ predicate:
```
set Married
  case George, Adam
  case (?x, ?y) then Had_Wedding(?x, ?y);
```
Cases can be enclosed in paranthese, or not. Terminal cases tell the solver to stop the search. They are denoted by the _NOT_ keyword, for example:
```
set Yellow
  case Moon then NOT
  case Sun;
```
The _extend_ keyword can be used to extend an existing predicate (instead of the _set_ keyword, which overrides an existing predicate).

It is possible to use variables to store predicate names (after all they are just simple atoms when they are not applies to a pattern).

### Recurisve and Random
It is possible to have a predicate be recursive, random or both. Recursive means that once a match was found(__not__ a solution in a match) the searcg will be finished. Random will mean the matches will be searched in a random order (unlike regular predictaes which are searched by order of input, with terminal first, fact second, and regular rules last). These properties are assigned to predicates with the use of the _as_ keyword as follows
```
set P as random, recursive
  ...;
set Q as recursive
  ...;
```

### Queries
In the console, a query can be asked. For example, the query _Father(Abrahm, Isaac)_ is a query asking "Is Abraha, the father of Isaac?". A more general query might read _Father(Abraham, ?x)_, which is asking "Who is the son of Abraham?". The even more general query _Father(?x, ?y)_ is asking "What are the pairs of fathers and sons?". 

Some Queries do not have definitive solutions. For example, in the equation _x - x = 0_, every possible value of x will satisfy the given equation. Similarly in Local, some queries which have indefinitive solution will be denoted by \_, or \_{i} for indefinitve solutions that are repeated. 

Assertions can be added to queries, to assert that the solutions found are indeed solutions. This is useful in the case that terminal cases are not used as stopping points, but rather falsehoods. 

the _Print_ keyword is a builtin predicate that just prints to the screen a string, and returns true. _NL_ (or "\n") denotes a new line. A print automatically prints a new line at the end. This can be avoided with the use of an extra comma at the end of the Predicate pattern. For example _Print(3, 4, 6)_ would print "3 4 6" and a new line, but _Print(3, 4, 6, )_ will not print a new line.

### Logic
Logic gates are extremely useful in local.
#### &
The _and_ gate will perform predictaes sequentially. Only if both searches are solved successfully will there be a final solution.
#### |
The _or_ gate will return a solution if one of the two searches are solved.
#### $
The _lazy or_ gate will search the first query. If a solution is found, it will not bother to look for the second search. If not, it will.
#### ~
The _filter_ gate will __not__ generate solutions. It uses failure as negation, a common practice in logical programming. If the query fails, it will keep searching. It almost always follows a _and_ gate, The first __generating__ solutions and the second __filtering__ them. The use of _filter_ as a Not Gate is not unheard of, but it is only useful when all pieces of information are used.
##### The use of multiple logical gates
The precedence order of logical gates as follows: And, Or, Lazy Or, Filter. The use of parantheses can combat the order. 

### Lists
Lists are collections of data. Similar to functional programming languages, lists allow a two writing styles: _full_ and _cons_. a Full list will specify every single element in the list. Such as:
* [1, 2, 3]
* [Apple, Orange]
* [[], []]
* []

A Consed List will only show the "head" and the "tail" of a list, seperated by aמ asterisk, inside square brackets. E.g.
* [1 * [1,2,3,4]]
* [?x * ?xs]

### Titles
Titles are ways to communicate a special meaning behind a set of objects. For example, the title 3tuple might represent a tuple of size three. It is customary (but not necessary) to declare titles as follows:
```
declare 3tuple, 4tuple, Branch, T;
```
The use of titles is not bounded by anything, therefore 3tuple could be used to store 10,000 objects. If you want to indicate the proper use of a title, it is recommended to write a type predicate, for example:
```
set 3Tuple
  case 3tuple(?x, ?y, ?z);
```

### Imports
There is a selection of libraries ([In Hebrew](https://docs.google.com/document/d/1kgv_ApvLOi7FfVBAVtID-wjRNqBVUOVn-WBu5yKOiQg/edit#)). In addition, one can import their own files with the use of _import_:
```
import Math; # Math library
import @local_file; # local rules
```

### Packages
Packages are "preidctae generators". They act as second-order and above logical components. For example:
```
import Math;
package divisibleBy{?c}
  case ?x then Mod(?x, ?c, 0);
```
Essentially, _?c_ represents a package variabke, where _?x_ represents a predicate variable. The use of packages:
```
divisibleBy{3}(6) # True
divisibleBy{10}(15) # False (no solution)
```

### Sequences
Sequences are lists with lazy evaluation. They can be calculated through the use of packages. For example:
```
package From{?x}
  case ?x, From(?xp1) then Add(?x, 1, ?xp1);
```
is a sequence of all numbers from _?x_ and onwards. This can be used in the query _From{3}(?x, ?a) & ?a(?y, ?b) & ?b(?z, ?d)_, and solved as:
```
?x <- 3
?a <- From{4}
?y <- 4
?b <- From{5}
?z <- 5
?d <- From{6}
```

### Infixes
Infixes are a type of title that always use as an infix. and infix must begin with ^, other than that, there are no limitations on infixes. An example of a program that makes use of infixes:
```
import Math;
infix ^+, ^-;
set Eval
  case (?x ^+ ?y), ?e then Eval(?x, ?e1) & Eval(?y, ?e2) & Add(?e1, ?e2, ?e);
  case (?x ^- ?y), ?e then Eval(?x, ?e1) & Eval(?y, ?e2) & Sub(?e1, ?e2, ?e);
  case ?x, ?x then Add(0, ?x, ?_); # assert it is a number, we can add to it.
  
# Try query "Eavl((3^+4)^-6, ?e)"
```
Notice precendece of infixes is by order of declaration. Infixes __must__ be declared, unlike title, although in reality infixes are just translated to titles, i.e., _3^+4_ will be parsed to _^+(3, 4)_.

### Connect Clauses
Connect clauses are syntax sugar for sequential predictaing. For exmaple these two are the same:
```
connect A = B + C;
# same as
set A
  case (?inp, ?out) then B(?inp, ?temp) & C(?temp, ?out);
```
The token _:_ can be used to include variables in connect clauses, for example:
```
connect A : [?x, ?y] = B : ?x + C : ?y;
# same as
set A
  case (?inp, ?out, [?x, ?y]) then B(?inp, ?temp, ?x) & C(?temp, ?out, ?y);
```
Another application of connect clauses, that only works if the _List_ library is included, is the _\_C_ predicate. For Example:
```
connect A = [1, 2, 3] + C;
```
will strip a list input to A of the components 1, 2, 3 and the look for C. Connection can include logical gates, which reset the variables to start with _?inp_ again and finish with _?out_. One can also include regular operations enclosed within curly brackets. For example:
```
connect Word : ?z = As : ?x + Bs : ?y + {Add(?x, ?y, ?z)};
```
will count the As in the list, the Bs in the list (after the As are stripped) and add the count as the result of _Word_.

### NLP
This is a simple example of natural langugae processing using Local:
```
import List;
declare s, np, vp, d, n, v;
(* s - sentence
np - noun phrase
vp - verb phrase
d - determiner
n - noun
v - verb *)

connect Sentence:s(?np,?vp) = NounPhrase:?np + VerbPhrase:?vp;
connect NounPhrase:np(?d, ?n) = Det:?d + Noun:?n;
connect VerbPhrase:vp(?v, ?np) = Verb:?v + NounPhrase:?np;

connect Det : d(the) = [the];
connect Det : d(a) = [a];
connect Noun : n(cat) = [cat];
connect Noun : n(bat) = [bat];
connect Verb : v(eats) = [eats];
```
One could query "Sentence([the, bat, eats, a, cat], [], ?x)". The result will be a parsed sentence:
```
?x <- s(np(d(the),n(bat)),vp(v(eats),np(d(a),n(cat))))
```
denoting the parts of speech included in the sentence.

### Domain Search
An efficient way to search for SAT (constraint satisfactory problems) is using a domain predictae. It has three parts: Variable declarations, range declaration and constraint declaration. Contraints are either things that we want to be true, using the keyword _const_, or things we do not want, using the keyword _elim_. For example, a 2x2 Soduko solver:

```
import List;

domain Soduko
  # Variable declaration
  over ?a, ?b, ?c, ?d
       ?e, ?f, ?g, ?h
       ?i, ?j, ?k, ?l
  # Range searches using In from List library.
  of ?a : In(?a, [1,2,3,4])
  of ?b : In(?b, [1,2,3,4])
  ...
  of ?l : In(?l : [1,2,3,4])
  
  # constraints
  elim In(?a, [?b, ?c, ?d])
  elim In(?b, [?a, ?c, ?d])
  elim In(?c, [?a, ?b, ?d])
  ...
  elim In(?l, [?i, j, ?k]);
```

### More Example
Directory [NewRules](https://github.com/YuvalLot/PyLocal/tree/main/NewRules) Holds some examples of code in the Local.
