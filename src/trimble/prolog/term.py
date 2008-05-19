def find_variables(terms, variables=None):
  l = None
  if not(isinstance(terms, list) or isinstance(terms, tuple)):
    l = [terms]
  elif isinstance(terms,tuple):
    l = list(terms)
  else:
    l = terms
  if variables == None:
    variables = []
  for term in l:
    if isinstance(term, Pred):
      if term.variables == None:
        term.variables = set(find_variables(term.terms))
      variables.extend(term.variables)
    elif isinstance(term, Var):
      variables.append(term)
    elif isinstance(term, list) or isinstance(term, tuple):
      l.extend(term)
  return variables

class Term:
  
  def apply_bindings(self, bindings):
    return self


class Pred(Term):
  
  def __init__(self, predicate, *terms):
    self.predicate, self.terms = predicate, terms
    self.variables = None
    
  def __repr__(self):
    return str(self)
  
  def __str__(self):
    if len(self.terms) > 0: return str(self.predicate) + "(" + str(reduce(lambda x,y: str(x) + ", " + str(y), self.terms)) + ")"
    else: return str(self.predicate)
    
  def __hash__(self):
    return hash(self.predicate.name) + len(self.terms)
  
  def apply_bindings(self, bindings):
    new_terms = []
    for term in self.terms:
      if isinstance(term, Term): new_terms.append(term.apply_bindings(bindings))
      else: new_terms.append(term)
    return self.predicate(*new_terms)
    
    
class ListPred(Pred):
  
  def __generate_str(self, l):
    if [] == l: 
      return ""
    if isinstance(l, Var): return "|" + str(l)
    if not hasattr(l, 'terms'): return "." + str(l)
    H, T = l.terms
    s = str(H)
    st = self.__generate_str(T)
    if st != "": s += ", " + st
    return s
  
  def __str__(self):
    return "plist([" + self.__generate_str(self) + "])"
  
  def __eq__(self, other):
    return isinstance(other, ListPred) and self.terms[0] == other.terms[0] and self.terms[1] == other.terms[1]
  

class Function(Term):
  
  def __init__(self, function, *terms):
    self.function = function
    self.terms = terms
    
  def apply_bindings(self, bindings):
    new_terms = []
    for term in self.terms:
      if isinstance(term, Term): new_terms.append(term.apply_bindings(bindings))
      else: new_terms.append(term)
    return Function(self.function, *new_terms)
  
  
class Atom(Term):
  
  def __init__(self, name):
    self.name = name
    self._hash = hash(self.name)
    
  def __str__(self):
    return self.name
  
  def __repr__(self):
    return str(self)
  
  def __eq__(self, other):
    return isinstance(other, Atom) and self.name == other.name
    
  def __hash__(self):
    return self._hash
  
  def apply_bindings(self, bindings):
    if bindings.has_key(self): return bindings[self]
    else: return self
    
  
class Var(Term):
  
  unique_count = 0
  
  def __init__(self, name):
    self.name = name
    self._hash_value = hash(self.name)
    self.scope = None
    
  def __str__(self):
    return str(self.name)
  
  def __repr__(self):
    return str(self)
  
  def __eq__(self, other):
    return isinstance(other, Var) and self.name == other.name
  
  def __hash__(self):
    return self._hash_value
  
  def apply_bindings(self, bindings):
    if bindings.has_key(self): return bindings[self]
    else: return self
    
  def get_unique(var):
    Var.unique_count += 1
    return Var('@_' + str(Var.unique_count) + '_' + var.name)
  
  get_unique = staticmethod(get_unique)
  
  
class VariableFactory:
  
  def __getattr__(self, name):
    return Var(name)
  
  
class AtomFactory:
  
  def __getattr__(self, name):
    return Atom(name)


class UniqueVariableFactory:
  
  instance_count = 0
  
  def __init__(self):
    self.variable_map = {}
    
  def _next_count(self, prefix):
    try:
      self.variable_map[prefix] += 1
    except:
      self.variable_map[prefix] = 0
    return str(self.variable_map[prefix])
  
  def next_variable(self, prefix = "VAR_"):
    count = self._next_count(prefix)
    var = Var(prefix + str(count))
    return var
  
  def next_variable_sequence(self, length, prefix="VAR_"):
    return map(lambda x: self.next_variable(prefix), range(length))
  
  def reset(self):
    self.variable_map = {}
  
def pred(predicate, *terms):
  return Pred(predicate, *terms)

def func(function, *terms):
  return Function(function, *terms)
