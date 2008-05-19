import unittest
from trimble.prolog.predicate import KnowledgeBase
from trimble.prolog.predicate import RuleBasedPredicate
from trimble.prolog.predicate import VariableFactory, UniqueVariableFactory, AtomFactory
from trimble.prolog.foil import TrainingSet, find_gainful_and_determinate_literals, construct_clause_recursive, foil, find_partial_ordering_of_terms, determine_param_orderings
from trimble.prolog.algorithm import fol_bc_ask
from trimble.prolog.term import Atom

class FamilyMemberFactory:
  
  def __getattr__(self, name):
    return FamilyMember(name)


class FamilyMember(Atom):
  
  def __init__(self, name):
    Atom.__init__(self, name)
  
  def set_ordering(self, ordering):
    self._ordering = ordering
    def compare(x,y):
      return cmp(self._ordering.index(x), self._ordering.index(y))
    FamilyMember.__cmp__ = compare
    
  set_ordering = classmethod(set_ordering)


class FamilyTreeTestCase(unittest.TestCase):
  
  def loadFamilyTree1(self):
    """
    Frank -------- Rebecca             George -------- Jannet
           |     |                             |     |
          Abe   Alan ------ Joan  Jill ------ Bob    Tim ---- Tammy
                        |             |                   |
                       Sean -------- Jan       Tipsy --- Tom
                               |                      |
                              Jane ---- Ian         Thomas --- Debrah
                                    |                       |
                                   Ann                     Billy
    """
    v, a = self.v, self.a
    ordering = [a.frank, a.rebecca, a.george, a.jannet, a.abe, a.alan, a.joan, a.jill, a.bob, a.tim, a.tammy, a.sean, a.jan, a.tipsy, a.tom, a.jane, a.ian, a.thomas, a.debrah, a.ann, a.billy]
    FamilyMember.set_ordering(ordering)
    self.father.rules = []
    self.father.param_orderings = None
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
    self.mother.rules = []
    self.mother.param_orderings = None
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
    for predicate in [self.mother, self.father]:
      try:
        predicate.param_orderings = determine_param_orderings(predicate)
      except:
        pass
  
  def setUp(self):
    self.v, self.a = VariableFactory(), FamilyMemberFactory()
    self.kb = KnowledgeBase()
    v, a = self.v, self.a
    self.father = RuleBasedPredicate('father', (FamilyMember, FamilyMember))
    self.mother = RuleBasedPredicate('mother', (FamilyMember, FamilyMember))
    self.kb.add_all([self.mother, self.father])
  
  def testFindRecursiveRules(self):
    from trimble.prolog.predicate import Rule, MutableRule
    from trimble.prolog.foil import will_halt
    v, a = self.v, self.a
    self.loadFamilyTree1()
    mother = self.mother
    predicate = RuleBasedPredicate('ancestor', (FamilyMember, FamilyMember))
    predicate.rules.append( Rule( predicate, (v.X, v.Y), (mother(v.X, v.Y),) ) )
    current_rule = MutableRule( predicate, (v.X, v.Y), (mother(v.Z, v.Y),) )
    predicate.rules.append(current_rule)
    recursive_literal = predicate(v.X, v.Z)
    ordering = find_partial_ordering_of_terms(current_rule)
    self.assertTrue(will_halt(predicate, recursive_literal, [v.X, v.Y], ordering))
  
  def testAncestor(self):
    v, a = self.v, self.a
    self.loadFamilyTree1()
    ancestor = RuleBasedPredicate('ancestor', (FamilyMember, FamilyMember))
    self.kb.add(ancestor)
    positive_tuples = [[a.jane, a.ann],
                                [a.tim, a.tom],
                                [a.tipsy, a.billy],
                                [a.jannet, a.billy],
                                [a.joan, a.jane],
                                [a.rebecca, a.ann],
                                [a.frank, a.jane],
                                [a.jan, a.ann],
                                [a.jill, a.ann]]
    negative_tuples = [[a.tim, a.ann],
                                [a.ann, a.billy],
                                [a.jane, a.frank],
                                [a.tom, a.debrah],
                                [a.tim, a.tammy],
                                [a.tom, a.george],
                                [a.jane, a.joan]]
    foil(ancestor, positive_tuples, negative_tuples, self.kb, ordering=None)
    self.assertFollows(ancestor(a.bob, a.jane))
    self.assertNotFollows(ancestor(a.bob, a.ian))
    self.kb.remove(ancestor)
    
  def testGrandparent(self):
    import sys
    v, a = self.v, self.a
    self.loadFamilyTree1()
    grandfather = RuleBasedPredicate('grandfather', (FamilyMember, FamilyMember))
    grandfather.arity = 2
    self.kb.add(grandfather)
    positive_tuples = [[a.frank, a.sean],
                                [a.tom, a.billy],
                                [a.george, a.jan],
                                [a.bob, a.jane],
                                [a.sean, a.ann],
                                [a.frank, a.sean]]
    negative_tuples = [[a.jannet, a.tim], 
                                [a.jane, a.alan],
                                [a.rebecca, a.sean],
                                [a.jan, a.ann]]
    foil(grandfather, positive_tuples, negative_tuples, self.kb, ordering=None)
    self.assertFollows(grandfather(a.george, a.tom))
    self.assertFollows(grandfather(a.alan, a.jane))
    self.assertNotFollows(grandfather(a.tipsy, a.billy))
    self.assertNotFollows(grandfather(a.bob, a.ian))
    self.kb.remove(grandfather)

  def assertFollows(self, arg0, arg1=None):
    msg, term = None, None
    if isinstance(arg0, str):
      msg = arg0
      term = arg1
    else:
      term = arg0
    for x in fol_bc_ask([term], {}):
      return
    if msg:
      self.fail(msg)
    else:
      self.fail()
      
  def assertNotFollows(self, arg0, arg1=None):
    msg, term = None, None
    if isinstance(arg0, str):
      msg = arg0
      term = arg1
    else:
      term = arg0
    for x in fol_bc_ask([term], {}):
      if msg:
        self.fail(msg)
      else:
        self.fail()
        