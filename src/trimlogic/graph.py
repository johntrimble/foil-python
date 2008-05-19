from trimlogic.algorithm import fol_bc_ask
from trimlogic.term import VariableFactory
from trimlogic.predicate import *
from trimlogic.stdlib import *

def consult(query):
  print str(query)
  for answer in fol_bc_ask(query, {}): print "Answer: " + str(answer)

v = VariableFactory()
edge_list = ( (0,1), (1,2), (0,3), (3,2), (3,4), (4,5), (4,6), (7,6), (6,8), (7,8) )
linkedto = RuleBasedPredicate('linked-to')
map(lambda x: linkedto.add_rule( Head = x ), edge_list)

canreach = RuleBasedPredicate('can-reach')
canreach.add_rule( Head=( v.X, v.Y ),
                  Body=( linkedto(v.X, v.Y), ) )
canreach.add_rule( Head=( v.X, v.Y ),
                  Body=( linkedto(v.X, v.Z), canreach(v.Z, v.Y) ) )

consult( [linkedto(1,2)] )
consult( [linkedto(2,1)] )
consult( [canreach(0,v.X)] )
