import unittest
import logging
from trimlogic.test.helper import FoilTestCase
from trimlogic.predicate import KnowledgeBase
from trimlogic.predicate import RuleBasedPredicate
from trimlogic.predicate import VariableFactory, UniqueVariableFactory
from trimlogic.predicate import AtomFactory
from trimlogic.foil import TrainingSet, construct_clause_recursive
from trimlogic.foil import find_gainful_and_determinate_literals, foil
from trimlogic.foil import find_partial_ordering_of_terms
from trimlogic.foil import determine_param_orderings
from trimlogic.algorithm import fol_bc_ask
from trimlogic.term import Atom, Term
from trimlogic.stdlib import components, dot, plist

class ListTestCase(FoilTestCase):
  
  def setUp(self):
    logging.getLogger("foil_construct_clause").setLevel(logging.DEBUG)
    logging.getLogger("foil_determine_ordering").setLevel(logging.DEBUG)
    logging.getLogger("foil_new_literal").setLevel(logging.DEBUG)
    logging.getLogger("predicate_rules_postprocessing_compact").setLevel(logging.DEBUG)
    logging.getLogger("foil_profiling").setLevel(logging.DEBUG)
  
  def testMemberPredicate(self):
    print ""
    v, a = VariableFactory(), AtomFactory()
    kb = KnowledgeBase()
    kb.add(components)
    member = RuleBasedPredicate("member", (Term, dot))
    kb.add(member)
    positive_tuples = ((1, plist([1,2,3,4])),
                       (4, plist([1,2,3,4])),
                       (5, plist([5,4,3,2])),
                       (2, plist([1,2,3,4])),
                       (3, plist([1,2,3,4])))
    negative_tuples = ((1, plist([2,3,4,5])),
                       (2, plist([1,3,4,5])),
                       (3, plist([1,2,4,5])),
                       (4, plist([1,2,3,5])),
                       (5, plist([1,2,3,4])),
                       (plist([1,2]), plist([1,2,3,4])))
    foil(member, positive_tuples, negative_tuples, kb, ordering=None)
    self.assertFollows(member(11, plist([2,3,5,7,11,13])))
    self.assertNotFollows(member(12, plist([2,3,5,7,11,13])))
    self.print_rules(member)

if __name__ == "__main__":
    unittest.main()