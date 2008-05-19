import logging
logging.basicConfig(level=logging.INFO)

import unittest

from trimlogic.term import *
from trimlogic.predicate import *
from trimlogic.algorithm import *
from trimlogic.stdlib import *

class PrologTestCase(unittest.TestCase):
  def assertHaveSameElements(self, expected, given):
    self.assertEquals(len(expected), len(given))
    for (e1, e2) in zip(expected, given):
      self.assertEquals(e1, e2)
      
class AlgPredicatesTestCase(PrologTestCase):
  def testCutNeg(self):
    v = VariableFactory()
    a = RuleBasedPredicate('a')
    b = RuleBasedPredicate('b')
    c = RuleBasedPredicate('c')
    a.add_rule( Head=( v.X, v.Y ),
               Body=( b(v.X), cut, c(v.Y) ) )
    b.add_rule( Head=( 1, ) )
    b.add_rule( Head=( 2, ) )
    b.add_rule( Head=( 3, ) )
    c.add_rule( Head=( 1, ) )
    c.add_rule( Head=( 2, ) )
    c.add_rule( Head=( 3, ) )
    self.assertHaveSameElements( ({v.Q : 1, v.R : 1},
                                  {v.Q : 1, v.R : 2},
                                  {v.Q : 1, v.R : 3},
                                  None), 
                                  list(fol_bc_ask([a(v.Q, v.R)], {})) )
    self.assertHaveSameElements( (None,), list(fol_bc_ask([neg(b(1))], {})) )
    self.assertHaveSameElements( ({},), list(fol_bc_ask([neg(b(4))], {})) )
  def testEql(self):
    v = VariableFactory()
    self.assertHaveSameElements( ({},),
                                  list(fol_bc_ask([eql(1,1)], {})) )
    self.assertHaveSameElements( (),
                                  list(fol_bc_ask([eql(1,2)], {})) )
    self.assertHaveSameElements( ({v.X : 1},),
                                  list(fol_bc_ask([eql(1,v.X)], {})) )
    
class ListTestCase(PrologTestCase):
  def testBasicPredicates(self):
    v = VariableFactory()
    self.assertHaveSameElements( ({v.X : 1},),
                                 list(fol_bc_ask([car(plist([1, 2, 3, 4]), v.X)], {})) )
    self.assertHaveSameElements( ({v.X : plist([2, 3, 4])},),
                                 list(fol_bc_ask([cdr(plist([1, 2, 3, 4]), v.X)], {})) )
    self.assertHaveSameElements( ({v.X : plist([1, 2])},),
                                 list(fol_bc_ask([cons(1, plist([2]), v.X)], {})) )
    self.assertHaveSameElements( ({v.X : plist([1, 2, 3, 4])},),
                                 list(fol_bc_ask([append(plist([1, 2]), plist([3, 4]), v.X)], {})) )   
  def testReversePredicate(self):
    v = VariableFactory()
    self.assertHaveSameElements( ({v.X : plist([3, 2, 1])},),
                                 list(fol_bc_ask([reverse(plist([1, 2, 3]), v.X)], {})) )
    
class TypePredicatesTestCase(PrologTestCase):
  def testNumberPredicates(self):
    v = VariableFactory()
    self.assertHaveSameElements( ({},),
                                 list(fol_bc_ask([is_integer(1)], {})) )
    self.assertHaveSameElements( (), 
                                 list(fol_bc_ask([is_integer("not an integer")], {})) )
    
def testOOP():
  father = RuleBasedPredicate('father')
  father.add_rule(Head=('steven', 'john'))
  father.add_rule(Head=('olin', 'gayle'))
  
  mother = RuleBasedPredicate('mother')
  mother.add_rule(Head=('gayle', 'john'))
  
  parent = RuleBasedPredicate('parent')
  X, Y, Z = Var('X'), Var('Y'), Var('Z')
  parent.add_rule(Head=(X, Y), Body=(pred(mother, X, Y),))
  parent.add_rule(Head=(X, Y), Body=(pred(father, X, Y),))
  logging.debug("running algorithm")
  for answer in fol_bc_ask([parent(Z, 'john')], {}): print "Answer: " + str(answer)
  logging.debug("done")

def testReverseList():
  """
  reverse([],[]). % the empty list is its own reverse. Base for induction. 
  reverse([H|T], Rev) :- reverse(T, Trev), append(Trev, [H], Rev).
  """
  X = Var("X")
  for query in ([reverse(plist([1,2]), X)],):
    print query 
    for answer in fol_bc_ask(query, {}): print "Answer: " + str(answer)
  
def testOOP01():
  for answer in fol_bc_ask([est(Var('X'), func(int.__add__, 1, 2))], {}): print str(answer)  
  
if __name__ == '__main__':
  unittest.main()
