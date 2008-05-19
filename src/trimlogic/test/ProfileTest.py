from trimlogic.predicate import KnowledgeBase
from trimlogic.predicate import RuleBasedPredicate
from trimlogic.predicate import VariableFactory, UniqueVariableFactory
from trimlogic.foil import TrainingSet, find_gainful_and_determinate_literals, construct_clause_recursive, foil
from trimlogic.algorithm import fol_bc_ask

def runTest():
  v = VariableFactory()
  kb = KnowledgeBase()
  father = RuleBasedPredicate('father')
  map(father.add_rule, [('steven', 'john'), 
                            ('steven', 'chris'), 
                            ('john_elder', 'steven'), 
                            ('olin', 'gayle'),
                            ('less', 'sean'), 
                            ('olin', 'george'),
                            ('george', 'april'),
                            ('steven', 'wes'),
                            ('wes', 'jake'),
                            ('robins_father', 'robin')])
  mother = RuleBasedPredicate('mother')
  map(mother.add_rule, [('gayle', 'john'), 
                            ('gayle', 'chris'),
                            ('gayle', 'wes'),
                            ('gayle', 'sean'),
                            ('rachel', 'gayle'), 
                            ('rachel', 'george'),
                            ('robin', 'jake')])
  parent = RuleBasedPredicate('parent')
  parent.add_rule(Head=(v.X, v.Y), Body=(mother(v.X, v.Y),))
  parent.add_rule(Head=(v.X, v.Y), Body=(father(v.X, v.Y),))
  grandparent = RuleBasedPredicate('grandparent')
  grandparent.arity = 2
  grandfather = RuleBasedPredicate('grandfather')
  grandfather.arity = 2 
  kb.add_all([grandfather, mother, father])
  training_set = TrainingSet(grandfather, [v.X, v.Y], 
                             [['olin', 'chris'],
                              ['olin', 'john'],
                              ['john_elder', 'chris'],
                              ['john_elder', 'john',],
                              ['john_elder', 'wes'],
                              ['steven', 'jake']], 
                             [['gayle', 'sean'], 
                              ['steven', 'gayle'],
                              ['steven', 'sean'],
                              ['steven', 'george'],
                              ['steven', 'john'],
                              ['steven', 'wes'],
                              ['steven', 'chris'],
                              ['steven', 'john_elder'],
                              ['gayle','john'],
                              ['john', 'gayle'],
                              ['john', 'jake'],
                              ['john', 'john_elder'],
                              ['olin', 'jake']])
  foil(grandfather, training_set, kb)
  print "*** rules ***"
  for rule in grandfather.rules:
    print str(rule)
  
import profile
profile.run('runTest()', 'foil.prof')
import pstats
p = pstats.Stats('foil.prof')
p.sort_stats('time').print_stats(20)
