def plist(l, Tail=None):
  if Tail == None: 
    Tail = []
  if l == []:
    return Tail
  return dot( l[0], plist(l[1:], Tail=Tail) )

def __define_list_predicates():
  import operator
  from trimlogic.term import VariableFactory, Term
  from trimlogic.predicate import RuleBasedPredicate, ListPredicate
  global dot, car, cdr, cons, append, reverse, components
  
  v = VariableFactory()
  dot = ListPredicate('.')
  
  car = RuleBasedPredicate('car')
  car.add_rule( Head=( dot(v.H, v.T), v.H ) )
  
  cdr = RuleBasedPredicate('cdr')
  cdr.add_rule( Head=( dot(v.H, v.T), v.T ) )
  
  cons = RuleBasedPredicate('cons')
  cons.add_rule( Head=( v.H, dot(v.H1, v.T), dot(v.H, dot(v.H1, v.T)) ) )
  cons.add_rule( Head=( v.H, [], dot(v.H, []) ) )

  components = RuleBasedPredicate('components', (dot, Term, Term))
  components.add_rule( Head=( v.X, v.H, v.T ), Body=( car(v.X, v.H), cdr(v.X, v.T ) ) )
  components.param_orderings = {(0, 2):operator.gt}
  
  append = RuleBasedPredicate('append')
  append.add_rule( Head=( [], v.L, v.L ) )
  append.add_rule( Head=( dot(v.X, v.A), v.B, dot(v.X, v.C) ), 
                  Body=( append(v.A, v.B, v.C), ) )
  
  reverse = RuleBasedPredicate('reverse')
  reverse.add_rule( Head=( [], [] ) )
  reverse.add_rule( Head=( dot(v.H, v.T), v.Rev ), 
                   Body=( reverse(v.T, v.Trev), append(v.Trev, plist([v.H]), v.Rev) ) )
  
def __define_arithmetic_predicates():
  from trimlogic.predicate import IsPredicate
  global est
  est = IsPredicate()
  
def __define_type_predicates():
  from trimlogic.predicate import RuleBasedPredicate, create_python_boolean_predicate
  global is_atom, is_integer, is_number, is_compound, is_list, is_variable, is_atomic
  is_atom = create_python_boolean_predicate(lambda x: not isinstance(x, Term) and not isinstance(x, int) and isinstance(x, str) , 'is_atom')
  is_integer = create_python_boolean_predicate(lambda x: isinstance(x, int), 'is_integer')
  class IsNumberPredicate(RuleBasedPredicate):
    def __init__(self):
      RuleBasedPredicate.__init__(self, 'is_number')
    def _resolve(self, terms):
      for x in is_integer._resolve(terms):
        yield x
      
def __define_algorithmetic_predicates():
  from trimlogic.term import VariableFactory
  from trimlogic.predicate import CutPredicate, FailPredicate, RuleBasedPredicate
  global fail, cut, neg, eql
  v = VariableFactory()
  cut = CutPredicate()
  fail = FailPredicate()
  neg = RuleBasedPredicate('neg')
  neg.add_rule( Head=( v.Goal, ),
               Body=( v.Goal, cut, fail ) )
  neg.add_rule( Head=( v.Goal, ) )
  eql = RuleBasedPredicate('eql')
  eql.add_rule( Head=( v.X, v.X ) )

__define_type_predicates()
__define_algorithmetic_predicates()
__define_arithmetic_predicates()
__define_list_predicates()
