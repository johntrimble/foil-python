import logging
from trimlogic.term import *

logger = logging.getLogger()

def create_python_boolean_predicate(boolean_function, name):
  
  class PythonBooleanPredicate(RuleBasedPredicate):
    
    def __init__(self):
      RuleBasedPredicate.__init__(self, name)
      
    def _resolve(self, terms):
      try:
        if boolean_function(*terms):
          yield ({}, [], set())
      except:
        pass
      
      
  return PythonBooleanPredicate()


class KnowledgeBase:
  
  def __init__(self):
    self._map = {}
  
  def __getitem__(self, key):
    if self._map.has_key(key):
      raise "Predicate with name '" + predicate.name + "' already exists."
    return self._map[key]
  
  def remove(self, predicate):
    del self._map[predicate.name]
  
  def add(self, predicate):
    self._map[predicate.name] = predicate

  def add_all(self, l):
    map(self.add, l)

  def __iter__(self):
    return self._map.itervalues()


class Predicate:
  
  def __init__(self, arity = 1):
    self.arity = arity
    self.param_types = None
    self.param_orderings = None
    
  def contains(self):
    pass
  
  def _resolve(self, terms):
    pass
  
  def __call__(self, *terms):
    return pred(self, *terms)
  
  
class RuleBasedPredicate(Predicate):
  
  def __init__(self, name = None, types=None):
    Predicate.__init__(self)
    self.rules = []
    self.name = name
    if types:
      self.param_types = tuple(types)
    if types == None:
      self.arity = None
    else:
      self.arity = len(types)
    
  def _resolve(self, terms):
    from trimlogic.algorithm import unify
    logging.debug(str(self) + "._resolve( " + str(terms) + " ) ")
    for rule in self.rules:
      rule = rule.instantiate()
      logging.debug("considering rule: " + str(rule))
      Head, Body, variables = rule.terms, rule.body, rule.variables
      mgu = unify(terms, Head, {})
      if mgu != None: 
        logging.debug("substitutions: " + str(mgu))
        yield (mgu, list(Body), variables)
      
  def add_rule(self, Head=None, Body=None):
    if self.arity == None: self.arity = len(Head)
    if Body == None: self.rules.append(Fact(self, Head))
    else: self.rules.append(Rule(self, Head, Body))
    
  def __str__(self):
    if self.name != None: return self.name
    else: return object.__str__(self)
    
  def __repr__(self): return str(self)
  
  
class CutPredicate(RuleBasedPredicate, Pred):
  """
  This predicate always succeeds yielding no variable bindings, no new goals, and
  no new variables.
  """
  def __init__(self):
    self.name, self.predicate, self.terms = "!", self, ()
    self.variables = None
    self.arity = 0
  def _resolve(self, terms):
    yield ({}, [], set([]))
  def __str__(self):
    return str(self.name)
  def __repr__(self):
    return str(self)

class FailPredicate(RuleBasedPredicate, Pred):
  def __init__(self):
    RuleBasedPredicate.__init__(self, "fail")
    self.predicate, self.terms = self, ()
    self.arity = 0
    self.variables = None
    
class NegationAsFailure(RuleBasedPredicate):
  def __init__(self):
    """
    neg(Goal) :- Goal,!,fail.
    neg(Goal).
    """
    RuleBasedPredicate.__init__(self, 'neg')
    Goal = Var("Goal")
    self.add_rule( Head=( Goal ),
                  Rule=( Goal, cut, fail ) )
  
class ListPredicate(RuleBasedPredicate):
  def __call__(self, *terms):
    return ListPred(self, *terms)

class IsPredicate(Predicate):
  def __init__(self):
    Predicate.__init__(self)
    self.name = "is"
    self.arity = 2
  def _resolve(self, terms):
    x = terms[0]
    f = terms[1]
    if isinstance(f, Function):
      result = f.function(*f.terms)
      yield ({ x : result }, [], [])
    elif isinstance(x, int):
      pass

class Rule:
  
  def __init__(self, predicate, terms, body):
    self.predicate = predicate
    self.terms = tuple(terms)
    self.body = tuple(body)
    self._variables = None
  
  def get_variables(self):
    if self._variables == None:
      variables = []
      find_variables(self.terms, variables)
      find_variables(self.body, variables)
      self._variables = set(variables)
    return self._variables
  
  def instantiate(self):
    instance_var_map = {}
    for var in self.variables: instance_var_map[var] = Var.get_unique(var)
    new_terms = []
    for term in self.terms:
      if isinstance(term, Term): new_terms.append(term.apply_bindings(instance_var_map))
      else: new_terms.append(term)
    new_body = []
    for term in self.body:
      if isinstance(term, Term): new_body.append(term.apply_bindings(instance_var_map))
      else: new_body.append(term)
    return Rule(self.predicate, new_terms, new_body)
  
  def is_recursive(self):
    for literal in self.body:
      try:
        if literal.predicate == self.predicate:
          return True
      except e, AttributeError:
        pass # literal doesn't have a predicate, but thats okay.
    return False
  
  def __str__(self):
    return str(self.predicate) + str(self.terms) + " :- " + ", ".join(map(str, self.body)) + "."
  
  variables = property(fget=get_variables)


class MutableRule(Rule):

  def __init__(self, predicate, terms, body):
    self.predicate = predicate
    self.terms = terms
    self.body = body

  def get_variables(self):
    variables = []
    find_variables(self.terms, variables)
    find_variables(self.body, variables)
    return set(variables)
  
  def get_immutable_instance(self):
    return Rule(self.predicate, self.terms, self.body)
  
  variables = property(fget=get_variables)
  immutable_instance = property(fget=get_immutable_instance)


class Fact(Rule):
  def __init__(self, predicate, terms):
    Rule.__init__(self, predicate, terms, ())