import logging
import trimlogic.predicate
from collections import deque
from trimlogic.stdlib import cut
from trimlogic.term import *
from trimlogic.util import *
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.debug("started logging")

def log_unify(unify_func):
  def _unify(s1, s2, bindings=None):
    logger.debug("unify( " + str(s1) + ", " + str(s2) + " ) :: " + str(bindings))
    mgu = unify_func(s1, s2, bindings)
    if mgu != None: logger.debug("unified " + str(s1) + " and " + str(s2) + "  with " + str(mgu))
    else: logger.debug("failed to unify " + str(s1) + " and " + str(s2))
    return mgu
  return _unify

def compose(f, g, composition=None):
  if composition == None: composition = {}
  f_composition_not_same_instance = not composition is f
  for key in f.keys():
    if isinstance(f[key], Term):
      composition[key] = f[key].apply_bindings(g)
    elif f_composition_not_same_instance:
      composition[key] = f[key]
  composition.update(g)
  return composition

def unify(s1, s2, bindings=None):
  """
  Term, Term -> Map
  Implementation Notes:
  This is a basic implementation of the most general unifier algorithm presented
  in Artificial Intelligence: A Modern Approach 2nd Edition by Stuart J. Russel 
  and Peter Norvig.
  """
  logger = logging.getLogger('unify')
  logger.debug("start unify(%s, %s, %s)" % (s1, s2, bindings))
  if bindings == None:
    bindings = {}
  if isinstance(s1, list):
    s1 = tuple(s1)
  if isinstance(s2, list):
    s2 = tuple(s2)
  return _unify(s1, s2, bindings)

def _unify_var(var, x, bindings):
  if bindings.has_key(var):
    return _unify(bindings[var], x, bindings)
  try:
    if bindings.has_key(x):
      return _unify(var, bindings[x], bindings)
  except TypeError:
    pass
  return compose(bindings, {var : x}, bindings)  

def apply_bindings_seq(seq, bindings):
  l = []
  for x in seq:
    try:
      l.append(x.apply_bindings(bindings))
    except:
      l.append(x)
  return tuple(l)
    
def _unify(s1, s2, bindings):
  s1_is_tuple, s2_is_tuple = isinstance(s1, tuple), isinstance(s2, tuple)
  s1_and_s2_tuple = s1_is_tuple and s2_is_tuple
  # base cases
  if s1 == s2: 
    return bindings
  # recursive cases
  elif isinstance(s1, Var): 
    return _unify_var(s1, s2, bindings)
  elif isinstance(s2, Var): 
    return _unify_var(s2, s1, bindings)
  elif isinstance(s1, Pred) and isinstance(s2, Pred):
    P, P_terms = s1.predicate, s1.terms
    F, F_terms = s2.predicate, s2.terms
    if P == F:
      return _unify(P_terms, F_terms, bindings) 
  elif s1_and_s2_tuple and len(s1) == len(s2):
    new_bindings = _unify(s1[0], s2[0], bindings)
    if new_bindings:
      return _unify(apply_bindings_seq(s1[1:], new_bindings), apply_bindings_seq(s2[1:], new_bindings), new_bindings)
  else:
    return None
    
#unify = log_unify(unify)

def fol_bc_ask(goals, substitutions):
  """
  Attempts to satisfy a given set of goals, if one or more of the goals contains unbound variables,
  this algorithm will find every binding for every variable so that the goals are satisfied. The 
  solutions are given as a sequence of variable mappings that satisfy the goals. If there is no 
  mapping that will satisfy the goals then the generator yields no results.
  """
  logger.debug("fol_bc_ask( " + str(goals) + " ) :: " + str(substitutions))
  if len(goals) == 0:
    yield substitutions
    return
  goal = goals[0].apply_bindings(substitutions)
  logger.debug("goal after substitution: " + str(goal))
  for mgu,new_goals,variables in goal.predicate._resolve(goal.terms):
    for child_answers in fol_bc_ask(new_goals + goals[1:], compose(substitutions, mgu)):
      if child_answers == None: 
        logger.debug("received None for answers")
        yield None
        return
      for var in variables:
        try: 
          del child_answers[var]
          logger.debug("Removed answer for %s" % var)
        except: pass
      logger.debug("yielding %s" % child_answers)
      yield child_answers
  if goal.predicate == cut:
    logger.debug("Cut encountered, stopping back tracking")
    yield None
    