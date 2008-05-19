import unittest
import logging
from trimble.prolog.predicate import KnowledgeBase
from trimble.prolog.predicate import RuleBasedPredicate
from trimble.prolog.predicate import VariableFactory, UniqueVariableFactory
from trimble.prolog.predicate import AtomFactory
from trimble.prolog.foil import TrainingSet, construct_clause_recursive
from trimble.prolog.foil import find_gainful_and_determinate_literals, foil
from trimble.prolog.foil import find_partial_ordering_of_terms
from trimble.prolog.foil import determine_param_orderings
from trimble.prolog.algorithm import fol_bc_ask
from trimble.prolog.term import Atom, Term
from trimble.prolog.stdlib import components, dot, plist

class ListTestCase(unittest.TestCase):
  
  def setUp(self):
    logging.getLogger("foil_construct_clause").setLevel(logging.DEBUG)
    logging.getLogger("foil_determine_ordering").setLevel(logging.DEBUG)
    logging.getLogger("foil_new_literal").setLevel(logging.DEBUG)
    logging.getLogger("predicate_rules_postprocessing_compact").setLevel(logging.DEBUG)
    logging.getLogger("foil_profiling").setLevel(logging.DEBUG)
  
  def estMemberPredicate(self):
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
    print "%s rules: " % member
    for r in member.rules: print str(r)
    
  def testAppendPredicate(self):
    print ""
    v, a = VariableFactory(), AtomFactory()
    kb = KnowledgeBase()
    kb.add(components)
    append = RuleBasedPredicate("append", (Term, Term, Term))
    kb.add(append)
    positive_tuples = ((plist([1,2]), plist([1,2,3,4]), plist([1,2,1,2,3,4])),
                       (plist([1,2,3,4,5,6,7]), plist([5,8]), plist([1,2,3,4,5,6,7,5,8])),
                       (plist([1,1,1,1,1,1,1]), plist([3,7,4]), plist([1,1,1,1,1,1,1,3,7,4])),
                       (plist([4,3,2,1]), plist([]), plist([4,3,2,1])),
                       (plist([]), plist([7,8,9]), plist([7,8,9])),
                       (plist([]), plist([]), plist([])))
    negative_tuples = ((plist([1,2]), plist([1,2]), plist([1,2])),
                       (plist([1,2,3,4]), plist([5,6,7,8]), plist([9,8,10])),
                       (3, 7, 9),
                       (3, 7, plist([])),
                       (plist([]), 7, 8),
                       (plist([]), plist([]), 8),
                       (plist([]), 8, plist([])))
    foil(append, positive_tuples, negative_tuples, kb, ordering=None)
    print "%s rules: " % append
    for r in append.rules: print str(r)
    