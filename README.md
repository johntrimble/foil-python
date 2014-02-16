# Python FOIL
This is a Python implementation of FOIL, First Order Inductive Learner, described in J.R. Quinlan's paper [Learning Logical Definitions from Relations](http://link.springer.com/article/10.1023%2FA%3A1022699322624).   In addition, this includes implementations of unification, resolution, and a number of Prolog's standard predicates.

My main goal in writing this was merely to experiment with machine learning via inductive logic, and reproducing J.R. Quinlan's results seemed like a good place to start. There isn't a fancy UI or interactive prompt, but you can look at the test cases to see how to use the library. This really isn't intended for reuse, or as an example of clean idiomatic Python code, it's just an academic exercise, so keep that in mind.

## What is FOIL?
For an in-depth description, see the paper cited above. Basically, FOIL can learn the rule, as a set of horn clauses, that defines some relation given a set of examples in the relation and a set of examples not in the relation. For example, suppose you had the following facts:

```prolog
father(frank, abe).
father(frank, alan).
father(alan, sean).
father(sean, jane).
father(george, bob).
father(george, tim).
father(bob, jan).
father(tim, tom).
father(tom, thomas).
father(ian, ann).
father(thomas, billy).

mother(rebecca, alan).
mother(rebecca, abe).
mother(joan, sean).
mother(jane, ann).
mother(jannet, tim).
mother(jannet, bob).
mother(tammy, tom).
mother(tipsy, thomas).
mother(debrah, billy).
mother(jill, jan).
mother(jan, jane).
```

Now, suppose you didn't know the rule for the `ancestor` relation, but did have some positive examples of the relation (e.g. Tim is an ancestor of Tom, Jill is an ancestor of Ann, etc.) and some negtaive examples of the relation (e.g. Ann is not an ancestor of Billy, Tom is not an ancestor of George, etc.). From those examples and the above facts, FOIL can generate a rule for the `ancestor` relation such as the following:

```prolog
ancestor(X, Y) :- father(X, Y).
ancestor(X, Y) :- mother(X, Y).
ancestor(X, Y) :- father(Z, Y), ancestor(X, Z).
ancestor(X, Y) :- mother(Z, Y), ancestor(X, Z).
```

## Test Cases
### Family Tree
This test case demonstrates learning the `grandparent` and `ancestor` relations. Execute the following, from the project root:

```
cd src
python trimlogic/test/FamilyTreeTestCase.py 
```

You should see output like the following:

```
Rules for ancestor :
ancestor(PARAM_0, PARAM_1) :- father(PARAM_0, PARAM_1).
ancestor(PARAM_0, PARAM_1) :- mother(PARAM_0, PARAM_1).
ancestor(PARAM_0, PARAM_1) :- father(VAR_13, PARAM_1), ancestor(PARAM_0, VAR_13).
ancestor(PARAM_0, PARAM_1) :- mother(VAR_36, PARAM_1), ancestor(PARAM_0, VAR_36).
..
Rules for grandfather :
grandfather(PARAM_0, PARAM_1) :- father(VAR_4, PARAM_1), father(PARAM_0, VAR_4).
grandfather(PARAM_0, PARAM_1) :- mother(VAR_21, PARAM_1), father(PARAM_0, VAR_21).
.
----------------------------------------------------------------------
Ran 3 tests in 8.578s

OK

```

### List
This test case demonstrates learning the `member` relation for lists. Execute the following from the project root:

```
cd src
python trimlogic/test/FamilyTreeTestCase.py 
```

You should see output like the following:

```
Rules for member :
member(PARAM_0, PARAM_1) :- components(PARAM_1, PARAM_0, VAR_4).
member(PARAM_0, PARAM_1) :- components(PARAM_1, VAR_12, VAR_13), member(PARAM_0, VAR_13).
.
----------------------------------------------------------------------
Ran 1 test in 51.804s

OK
```

