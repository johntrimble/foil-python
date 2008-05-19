import unittest
from trimble.prolog.predicate import KnowledgeBase
from trimble.prolog.predicate import RuleBasedPredicate, Rule
from trimble.prolog.predicate import VariableFactory, UniqueVariableFactory, AtomFactory
from trimble.prolog.foil import TrainingSet, find_gainful_and_determinate_literals, construct_clause_recursive, foil
from trimble.prolog.algorithm import fol_bc_ask

from itertools import *

class ResolutionTestCase(unittest.TestCase):
  
  def setUp(self):
    self.v, self.a = VariableFactory(), AtomFactory()
    self.kb = KnowledgeBase()
    v, a = self.v, self.a
    self.father = RuleBasedPredicate('father')
    map(self.father.add_rule, [(a.frank, a.abe),
                               (a.frank, a.alan),
                               (a.alan, a.sean),
                               (a.sean, a.jane),
                               (a.george, a.bob),
                               (a.george, a.tim),
                               (a.bob, a.jan),
                               (a.tim, a.tom),
                               (a.tom, a.thomas),
                               (a.ian, a.ann),
                               (a.thomas, a.billy)])
    self.mother = RuleBasedPredicate('mother')
    map(self.mother.add_rule, [(a.rebecca, a.alan),
                               (a.rebecca, a.abe),
                               (a.joan, a.sean),
                               (a.jane, a.ann),
                               (a.jannet, a.tim),
                               (a.jannet, a.bob),
                               (a.tammy, a.tom),
                               (a.tipsy, a.thomas),
                               (a.debrah, a.billy),
                               (a.jill, a.jan),
                               (a.jan, a.jane)])
    self.kb.add_all([self.mother, self.father])
    self.ordering = {}
    ordered_constants = [a.frank, a.rebecca, a.george, a.jannet, a.abe, a.alan, a.joan, a.jill, a.bob, a.tim, a.tammy, a.sean, a.jan, a.tipsy, a.tom, a.jane, a.ian, a.thomas, a.debrah, a.ann, a.billy]
    for e,i in zip(ordered_constants, xrange(len(ordered_constants))):
      self.ordering[e] = i
  
  def testInfiniteRecursion(self):
    """
    grandfather(X, Y) :- father(VAR_0, Y), mother(VAR_1, Y), father(X, VAR_0)
    grandfather(X, Y) :- father(VAR_3, X), father(VAR_4, Y), mother(VAR_5, X), mother(VAR_6, Y), grandfather(X, VAR_3)
    """
    v, a = self.v, self.a
    self.grandfather = RuleBasedPredicate('grandfather')
    father, mother, grandfather = self.father, self.mother, self.grandfather
    self.grandfather.rules.append( Rule(grandfather, (v.X, v.Y), (father(v.VAR_0, v.Y), mother(v.VAR_1, v.Y), father(v.X, v.VAR_0))) )
    self.grandfather.rules.append( Rule(grandfather, (v.X, v.Y), (father(v.VAR_3, v.X), father(v.VAR_4, v.Y), mother(v.VAR_5, v.X), mother(v.VAR_6, v.Y), grandfather(v.X, v.VAR_3))) )
    for x in self.ordering.keys():
      for y in self.ordering.keys():
        print "fol_bc_ask( " + str(grandfather(x, y)) + " ) --> " + str(fol_bc_ask([grandfather(x, y)], {}))
    
  def estDoubleRule(self):
    """
    The FOIL implementation sometimes generates the same rule twice. This test 
    is to see if the cause resides with the fol_bc_ask or FOIL implementations.
    
    The duplicated ruleset for the ancestor relation:
    ancestor( (X, Y) ) :- (father(X, Y),)
    ancestor( (X, Y) ) :- (mother(X, Y),)
    ancestor( (X, Y) ) :- (father(Father_5, Y), ancestor(X, Father_5))
    ancestor( (X, Y) ) :- (father(Father_7, Y), father(VAR_7, Y), mother(VAR_8, Y), ancestor(X, VAR_8))
    *ancestor( (X, Y) ) :- (father(Father_12, Y), father(VAR_11, Y), mother(VAR_12, Y), ancestor(X, VAR_12))
    """
    v, a = self.v, self.a
    self.ancestor = RuleBasedPredicate('ancestor')
    father, mother, ancestor = self.father, self.mother, self.ancestor
    for body in [(father(v.X, v.Y),),
          (mother(v.X, v.Y),),
          (father(v.Father_5, v.Y), ancestor(v.X, v.Father_5)),
          (father(v.Father_7, v.Y), father(v.VAR_7, v.Y), mother(v.VAR_8, v.Y), ancestor(v.X, v.VAR_8))]:
      ancestor.add_rule(Head=(v.X, v.Y), Body=body)
    for b,c in ([a.rebecca, a.ann], [a.jan, a.ann], [a.jill, a.ann]):
      found = False
      for answer in fol_bc_ask([ancestor(b, c)], {}):
        if answer != None and answer != False:
          found = True
      if not found:
        self.fail()
    