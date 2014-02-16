import math, logging, sys, itertools, operator, time
from trimlogic.term import UniqueVariableFactory, VariableFactory, Var
from trimlogic.term import Atom, Pred
from trimlogic.algorithm import fol_bc_ask
from trimlogic.counting import choose, permute
from trimlogic.predicate import Rule, MutableRule
from trimlogic.partialordering import find_ordering
from trimlogic.partialordering import create_partial_comparator
logger = logging.getLogger(__name__)

##############################################################################
# Constants.
##############################################################################
NEW_VARIABLE_GAIN_BIAS = 0.001
MINIMUM_LITERAL_GAIN_TO_ADD = 0.80

##############################################################################
# Data strutures for storing and managing positive and negative examples.
##############################################################################
class ExampleTree:
  """
  This class represents a single base example and its extensions. This allows
  for greater compaction of the example data. The class also provides 
  functionality to produce the actual extensions of the base example through
  the extend method.
  """
  class Node:
    
    def __init__(self, variables, values, parent=None):
      self.parent = parent
      self.values = values
      self.variables = variables
      self.children = []
      
    def __str__(self):
      return ("<Node value=%s child_count=%s>" 
              % (self.values,len(self.children)))
    
    def __repr__(self): return str(self)
    
  def __init__(self, variables, values):
    assert len(variables) == len(values)
    self.root = ExampleTree.Node(variables, values)
    self.variables = variables
    self.size = len(variables)
    self.levels = 1
    self._count_list = [1]
  
  def extend(self, goals, variables):
    """
    Extends the current example by using the fol_bc_ask algorithm to determine
    values for the new variables.
    
    @param goals: The goals by which the extension of the example is to be 
        calculated.
    @type goals: A list of Term objects.
    @param variables: The new variables in the extension.
    @type variables: A list of Var objects.
    @return: The number of examples created from extending.
    """
    logger.debug("extend( " + str(goals) + ", " + str(variables) + " )")
    extension_count = 0
    examples_count = 0
    for node, bindings in self.enumerate_nodes_bindings():
      extended = False
      logger.debug("calling " + str(fol_bc_ask) + " with '" + str(goals) 
                    + "' '" + str(bindings) + "'")
      for answer in fol_bc_ask(goals, bindings):
        if answer != None:
          examples_count += 1
          extended = True
          value = []
          for var in variables:
            value.append(answer[var])
          node.children.append(ExampleTree.Node(variables, value, node))
      if extended:
        extension_count += 1
    self.levels += 1
    self._count_list.append(examples_count)
    logger.debug("Performed " + str(extension_count) + " extensions.")
    return extension_count
  
  def enumerate_nodes_bindings(self, i=None, node=None, bindings=None):
    if i == None: i = self.levels - 1
    if node == None: node = self.root
    if bindings == None: bindings = {}
    logger.debug("enumerate_nodes_bindings( " + str(i) + ", " + str(node) + ", " + str(bindings) + " )")
    for var,const in zip(node.variables, node.values):
      assert not bindings.has_key(var)
      bindings[var] = const
    logger.debug("Bindings '" + str(bindings) + "'.")
    if i == 0:
      yield node, bindings
      return
    k = i - 1
    for child in node.children:
      for x in self.enumerate_nodes_bindings(k, child, bindings):
        yield x
      for var in child.variables:
        del bindings[var]
  
  def enumerate_examples(self, level=None, node=None):
    if level == None: level = self.levels - 1
    if node == None: node = self.root
    logger.debug("enumerate_examples( " + str(level) + ", " 
                  + str(node) + " )")
    if level == 0:
      yield node.values
      return
    k = level - 1
    for child in node.children:
      for l in self.enumerate_examples(k, child):
        yield node.values + l
      
  def __iter__(self):
    return self.enumerate_examples()
  
  def cut_levels(self, i):
    self._cut_levels(i, self.root)
    
  def _cut_levels(self, i, node):
    if i == 1:
      for child in node.children:
        self.unlink_subtree(child)
      return
    k = i - 1
    for child in node.children:
      self._cut_levels(k, child)
  
  def rollback(self):
    logger.debug("rollback( )")
    self.cut_levels(self.levels-1)
    self.levels -= 1
    self._count_list.pop()
    
  def reset(self):
    while self.levels > 1:
      self.rollback()
  
  def unlink_subtree(self, node):
    s = [node]
    while s:
      n = s.pop()
      n.parent.children.remove(n)
      n.parent = None
      s.extend(n.children)
  
  def __len__(self):
    return self._count_list[self.levels-1]
  
  def __str__(self):
    s = ""
    for example in self.enumerate_examples():
      s += str(example)
      s += "\n"
    return s


class ExampleCollection:
  
  def __init__(self, predicate, formals, examples):
    self.predicate = predicate
    self._examples = []
    for example in examples:
      self._examples.append(ExampleTree(formals, example))
    self.variables = formals
  
  def __len__(self):
    return sum(map(len, self._examples))
  
  def __iter__(self):
    return itertools.chain(*self._examples)
  
  def rollback(self):
    for tree in self._examples:
      tree.rollback()
  
  def extend(self, goals, variables):
    return sum(map(lambda t: t.extend(goals, variables), self._examples))
  
  def reset(self):
    map(lambda x: x.reset(), self._examples)
    
  def prune_covered(self):
    logger.debug("Examples to consider for pruning: ")
    logger.debug(str(self._examples))
    for ex in self._examples[:]:
      prune = False
      logger.debug("Calling fol_bc_ask(" + str(self.predicate(*ex.root.values)) + ", {})")
      for answer in fol_bc_ask([self.predicate(*ex.root.values)], {}):
        logger.debug("fol_bc_ask(" + str(self.predicate(*ex.root.values)) 
                     + ", {}) -> " + str(answer))
        if answer != None and answer != False:
          self._examples.remove(ex)
          prune = True
          logger.debug("Pruned '%s'." % ex)
        break
      if not prune: logger.debug("Did not prune '%s'." % ex)
        
  def __repr__(self):
    s = ""
    for e in self._examples:
      s += str(e)
    return s
  
  def __str__(self):
    return self.__repr__()
      
  
class TrainingSet:
  
  def __init__(self, predicate, formals, positive_examples, negative_examples):
    self.positive_examples = self._insureExampleCollection(predicate, 
                                                           formals, 
                                                           positive_examples)
    self.negative_examples = self._insureExampleCollection(predicate, 
                                                           formals, 
                                                           negative_examples)
    self._variables = [formals]
    self._extensions = 0
    
  def get_variables(self):
    vars = []
    for l in self._variables:
      vars.extend(l)
    return vars
  
  def _insureExampleCollection(self, predicate, formals, examples):
    if isinstance(examples, ExampleCollection):
      return examples
    else:
      return ExampleCollection(predicate, formals, examples)
  
  def rollback(self):
    assert self._extensions > 0
    self._extensions -= 1
    self.positive_examples.rollback()
    self.negative_examples.rollback()
    self._variables.pop()
  
  def reset(self):
    self._extensions = 0
    self._variables = self._variables[:1]
    self.positive_examples.reset()
    self.negative_examples.reset()
    
  def has_variable(self, variable):
    for variables in self._variables:
      if variable in variables:
        return True
    return False
  
  def extend(self, goals, variables):
    self._extensions += 1
    self._variables.append(variables)
    return (self.positive_examples.extend(goals, variables), 
            self.negative_examples.extend(goals, variables))
  
  def get_information_measure(self):
    return -math.log(float(len(self.positive_examples) + 1) 
                     / float(len(self.negative_examples) 
                             + len(self.positive_examples) + 1), 2)
    
  def get_maximum_possible_gain(self):
    return len(self.positive_examples)*self.get_information_measure()
    
  def __str__(self):
    s = ""
    for example in itertools.chain(self.pos_examples, self.neg_examples):
      s += str(example)
    return s
  
  variables = property(fget=get_variables)


##############################################################################
# Functions for building a clause.
##############################################################################
def construct_clause_recursive(predicate, rule, training_set, bk, 
                               variable_factory=None, ordering=None, depth=0):
  assert isinstance(rule, Rule)
  assert isinstance(training_set, TrainingSet)
  logger.debug("Starting construct_clause_recursive(...).")
  logger.debug("Training set contains %s positive examples and %s negative " 
    "examples." % (len(training_set.positive_examples), 
                   len(training_set.negative_examples)))
  ordering = find_partial_ordering_of_terms(rule)
  if variable_factory == None: variable_factory = UniqueVariableFactory()
  head, body = rule.terms, rule.body
  if len(training_set.negative_examples) > 0:
    logger.debug("Clause so far %s :- %s." % (head, body))
    new_literals, determinate_literals = (
        find_gainful_and_determinate_literals(predicate, 
                                              rule, 
                                              training_set, 
                                              bk, 
                                              variable_factory, 
                                              ordering))
    logger.debug("New literals: " + str(new_literals))
    gain = new_literals[0][0]
    gain_ratio = gain / training_set.get_maximum_possible_gain()
    logger.debug("Gain ratio %s." % str(gain_ratio))
    depth += 1
    if( gain_ratio < MINIMUM_LITERAL_GAIN_TO_ADD 
        and len(determinate_literals) > 0 ):
      for literal, new_variables in determinate_literals:
        for var in new_variables: var.depth = depth
        body.append(literal)
        training_set.extend(body, new_variables)
      logger.debug("Determinate literals added.")
      if construct_clause_recursive(predicate, 
                                    rule, 
                                    training_set, 
                                    bk, 
                                    ordering=ordering, 
                                    variable_factory=variable_factory,
                                    depth=depth):
        return True
      else:
        logger.debug("Adding determinates of no use, back tracking.")
        for i in xrange(len(determinate_literals)): 
          training_set.rollback()
          body.pop()
    if gain < 0.001:
      logger.debug("Returning False because gain of %s < 0.001." % gain)
      return False
    logger.debug("Gainful literals to try: %s" % new_literals)
    for gain, literal, new_variables in new_literals:
      for var in new_variables: var.depth = depth
      body.append(literal)
      training_set.extend(body, new_variables)
      logger.debug("Trying solution: " + str((gain, literal, new_variables)))
      if construct_clause_recursive(predicate, 
                                    rule, 
                                    training_set, 
                                    bk, 
                                    ordering=ordering, 
                                    variable_factory=variable_factory, 
                                    depth=depth):
        return True
      logger.debug("Trying next solution.")
      training_set.rollback()
      body.pop()
    return False
  elif len(training_set.negative_examples) == 0:
    rule.body = tuple(rule.body)
    if rule.is_recursive():
      pass
    predicate.rules.remove(rule)
    predicate.rules.append(rule.immutable_instance)
    logger.debug("Found a rule %s." % predicate.rules[len(predicate.rules)-1])
    training_set.reset()
    training_set.positive_examples.prune_covered()
    return True
  raise "Fell through!"
  
def variablization(predicate, vars, variable_factory):
  if len(vars) == 0 or vars[len(vars)-1].depth < 4:
    for i in xrange(1, predicate.arity+1):
      for old_vars in choose(vars, i):
        new_vars = variable_factory.next_variable_sequence(
                                             predicate.arity-i, 
                                             predicate.name[0].upper() 
                                             + predicate.name[1:] + '_')
        for seq in permute(new_vars + old_vars):
          yield predicate(*seq), new_vars
  else:
    for old_vars in choose(vars, predicate.arity):
      for seq in permute(old_vars):
        yield predicate(*seq), []

def insert_literal((gain, literal, new_variables), literals, length):
  if len(literals) == 0:
    literals.append((gain, literal, new_variables))
  else:
    for i in xrange(len(literals)):
      if gain > literals[i][0]:
        literals.insert(i, (gain, literal, new_variables))
        break
  if len(literals) > length:
    literals.pop()
    

##############################################################################
# Functions for determining the soundness of recursive literals.
##############################################################################
def determine_param_orderings(predicate):
  logger.debug("Determining ordering for: " + str(predicate))
  
  def establish_relationship(value_pair, index_pair, op, cmp_map):
    x,y = value_pair
    i,k = index_pair
    if not(cmp_map.has_key((i,k)) and cmp_map[(i,k)] == None):
      if op(x,y):
        if cmp_map.has_key((i,k)): 
          if op != cmp_map[(i,k)]:
            cmp_map[(i,k)] = None
        else:
          cmp_map[(i,k)] = op
      elif cmp_map.has_key((i,k)) and op == cmp_map[(i,k)]:
        cmp_map[(i,k)] = None
      logger.debug(str(cmp_map))
  # end establish_relationship
      
  v = UniqueVariableFactory()
  type_map = {}
  types = predicate.param_types
  for i, type in zip(range(0, len(types)), types):
    if not type_map.has_key(type):
      type_map[type] = []
    type_map[type].append(i)
  pairs = []
  for type in type_map.keys():
    for x in choose(type_map[type], 2):
      pairs.append(list(x))
  cmp_map = {}
  variables = v.next_variable_sequence(predicate.arity)
  logger.debug("Calling: fol_bc_ask( %s )" % predicate(*variables))
  for answer in fol_bc_ask([predicate(*variables)], {}):
    logger.debug("Answer: " + str(answer))
    for pair in pairs:
      i,k = pair
      x,y = answer[variables[i]], answer[variables[k]]
      logger.debug("Comparing %s and %s." % (x, y))
      try:
        for op in [operator.lt, operator.gt, operator.eq]:
          establish_relationship((x,y), (i,k), op, cmp_map)
      except:
        pass
  return cmp_map

def create_unique_variable_sequence(prefix, length):
  return map(lambda x: Var(prefix + length), range(0, length))

def find_partial_ordering_of_terms(rule):
  logger.debug("Finding ordering for rule '%s'." % rule)
  constraints = []
  for literal in rule.body:
    if isinstance(literal, Pred):
      predicate = literal.predicate
      if predicate.param_orderings:
        for key in predicate.param_orderings.keys():
          x = literal.terms[key[0]]
          y = literal.terms[key[1]]
          constraints.append((predicate.param_orderings[key], x, y))
  logger.debug("Found constraints: " + str(constraints))
  return create_partial_comparator(constraints)
      
def will_halt(predicate, recursive_literal, variables, ordering=None):
  will_halt = False
  head_terms = variables[:predicate.arity]
  recr_terms = recursive_literal.terms
  logger.debug("Determining if %s > %s." % (predicate(*head_terms), 
                                            recursive_literal))
  for i in xrange(predicate.arity):
    if head_terms[i] == recr_terms[i]:
      continue
    if not recr_terms[i] in ordering:
      logger.debug("Term '%s' not in ordering." % recr_terms[i])
      will_halt = False
      break
    if  not head_terms[i] in ordering:
      logger.debug("Term '%s' not in ordering." % head_terms[i])
      will_halt = False
      break
    if ordering.eq(head_terms[i], recr_terms[i]):
      continue
    if ordering.gt(head_terms[i], recr_terms[i]):
      will_halt = True
      break
    elif ordering.lt(head_terms[i], recr_terms[i]):
      will_halt = False
      break 
  if will_halt:
    logger.debug("Found that %s > %s." % (predicate(*head_terms), 
                                          recursive_literal))
  return will_halt

def gen_variablization_space(predicate, 
                             path_finding_func,
                             variables,
                             variable_factory,
                             parameters=None, 
                             new_variable_positions=None):
  if parameters == None:
    parameters = variable_factory.next_variable_sequence(predicate.arity)
    new_variable_positions = range(len(parameters))
    for i in xrange(len(parameters)):
      new_var = parameters[i]
      pos = new_variable_positions[i]
      del new_variable_positions[i]
      for old_var in variables:
        parameters[i] = old_var
        for x in gen_variablization_space(predicate,
                                               path_finding_func,
                                               variables,
                                               variable_factory,
                                               parameters,
                                               new_variable_positions):
          yield x
      new_variable_positions.insert(i, pos)
      parameters[i] = new_var
  else:
    new_variables = []
    for k in new_variable_positions:
        new_variables.append(parameters[k])
    literal = predicate(*parameters)
    yield (literal, new_variables)
    if path_finding_func(literal, new_variables):
      for i in xrange(len(new_variable_positions)):
        pos = new_variable_positions[i]
        del new_variable_positions[i]
        new_var = parameters[pos]
        for old_var in variables:
          parameters[pos] = old_var
          for x in gen_variablization_space(predicate,
                                                 path_finding_func,
                                                 variables,
                                                 variable_factory,
                                                 parameters,
                                                 new_variable_positions):
            yield x
        new_variable_positions.insert(i, pos)
        parameters[pos] = new_var

def find_gainful_and_determinate_literals(predicate, 
                                          rule, 
                                          training_set, 
                                          bk, 
                                          variable_factory, 
                                          ordering=None, 
                                          clause=None, 
                                          determinate_literals=None, 
                                          new_literals=None, 
                                          grab_size=1):
  logger.debug("Finding a new literal.")
  logger.debug("Rules so far:")
  for rule in predicate.rules:
    logger.debug(str(rule))
  head, body = rule.terms, rule.body
  if determinate_literals == None: determinate_literals = []
  if new_literals == None: new_literals = []
  variables = training_set.variables
  current_depth = 0
  best_literal = None
  best_gain = -10000
  best_new_variables = None
  old_info_value = training_set.get_information_measure()
  for next_predicate in bk:
      continue_search = True
      def path_finding_func(literal, new_variables):
        return continue_search
      for literal, new_variables in gen_variablization_space(next_predicate,
                                                             path_finding_func,
                                                             variables, 
                                                             variable_factory):
        continue_search = True
        if predicate == next_predicate:
          if not will_halt(predicate, 
                           literal, 
                           training_set.variables, 
                           ordering):
            logger.debug("Adding '%s' may lead to infinit recursion." 
                         % literal)
            continue
          else:
            logger.debug("Adding '%s' will not lead to infinit recursion." 
                         % literal)
        body.append(literal)
        old_len_pos = len(training_set.positive_examples)
        old_len_neg = len(training_set.negative_examples)
        s_pos, s_neg = training_set.extend(body, new_variables)
        s = s_pos + s_neg
        new_info_value = training_set.get_information_measure()
        gain = foil_gain(s, old_info_value, new_info_value)
        if new_variables > 0: gain += NEW_VARIABLE_GAIN_BIAS
        if (len(training_set.positive_examples) > 0 
            and len(training_set.negative_examples) == 0):
          """
          Return 'literal' as the best literal as it excludes all negative 
          examples but includes at least 1 positive example. We do this 
          primarily to reduce the complexity of individual rules as well as 
          prevent excessive branching.
          """
          training_set.rollback()
          body.pop()
          logging.debug("Found literal '%s' which completes subset of "
                        "relation, choosing as best literal." % literal)
          return ([(gain, literal, new_variables)], [])
        if (s_pos == old_len_pos == len(training_set.positive_examples) 
            and s_neg <= old_len_neg 
            and s_neg == len(training_set.negative_examples) 
            and len(new_variables) > 0):
          determinate_vars = variable_factory.next_variable_sequence(
                                                           len(new_variables))
          remap_bindings = {}
          for nvar,dvar in zip(new_variables, determinate_vars):
            remap_bindings[nvar] = dvar
          determinate_literals.append((literal.apply_bindings(remap_bindings),
                                       determinate_vars))
        logger.debug("Considering literal '%s' with gain of %s which yields"
                     " %s positive and %s negative extensions."  % (literal, 
                                                                    gain, 
                                                                    s_pos, 
                                                                    s_neg))
        if len(training_set.positive_examples) > 0:
          insert_literal((gain, literal, new_variables), 
                         new_literals, grab_size)
        training_set.rollback()
        body.pop()
        if s * old_info_value < best_gain:
           continue_search = False
  logger.debug("Best literal found '%s'." % best_literal)
  logger.debug("Determinate literals found '%s'." % determinate_literals)
  return (new_literals, determinate_literals)

def foil_gain(s, old_information_value, new_information_value):
  return s * ( old_information_value - new_information_value )

##############################################################################
# Functions for cleaning learned perdicate rules.
##############################################################################
def determine_covered(predicate, tuple):
  for x in fol_bc_ask([predicate(*tuple)], {}):
    return True
  return False
    
def determine_tuples_covered(predicate, tuples):
  tuples = [x for x in tuples if determine_covered(predicate, x)]
  return tuples

def determine_tuples_covered_same_or_better(predicate, 
                                            positive_tuples, 
                                            negative_tuples, 
                                            positive_subset=None, 
                                            negative_subset=None):
  if positive_subset == None: positive_subset = positive_tuples
  if negative_subset == None: negative_subset = negative_tuples
  covered_pos = determine_tuples_covered(predicate, positive_tuples)
  covered_neg = determine_tuples_covered(predicate, negative_tuples)
  if( reduce(lambda x,y: x and y, 
            map(lambda x: x in covered_pos, positive_subset), True) 
            and reduce(lambda x,y: x and y, 
                       map(lambda x: x in negative_subset, covered_neg), 
                       True) ):
    return True
  return False

def will_rule_halt(predicate, rule):
  body_temp = []
  for term in rule.body:
    if hasattr(term, 'predicate') and term.predicate == predicate:
      ordering = find_partial_ordering_of_terms(
                                          Rule(predicate, rule.terms, body_temp))
      if not will_halt(predicate, term, rule.terms, ordering):
        return False
      body_temp.append(term)
    else:
      body_temp.append(term)
  return True

def predicate_rules_postprocessing_compact(predicate,
                                           positive_tuples,
                                           negative_tuples):
  """
  Removes redundant rules and terms from a predicate. This is an approximation
  algorithm since the optimal result is undecidable.
  
  @param predicate: The predicate whose rules are to be compacted.
  @type predicate: Predicate
  @param positive_tuples: Tuples covered by the predicate. These are used to
      insure that compaction does not affect the coverage of the predicate.
  @param negative_tuples: Tuples not covered by the predicate. These are used
      it insure that compaction does not affect the coverage of the predicate.
  """
  logger.debug("Start " + predicate_rules_postprocessing_compact.func_name)
  rules = predicate.rules
  predicate.rules = []
  for rule in rules:
    new_rule = rule
    predicate.rules.append(rule)
    covered_positive_tuples, covered_negative_tuples = (
        map(lambda x: determine_tuples_covered(predicate, x), 
            [positive_tuples, negative_tuples]))
    predicate.rules.pop()
    for i in xrange(1, len(rule.body)):
      found_rule = False
      for sub_rule_body in choose(rule.body, len(rule.body) - i):
        sub_rule = Rule(predicate, rule.terms, sub_rule_body)
        if not will_rule_halt(predicate, sub_rule):
          continue
        predicate.rules.append(sub_rule)
        better_rule = determine_tuples_covered_same_or_better(predicate, 
                                                    positive_tuples, 
                                                    negative_tuples, 
                                                    covered_positive_tuples, 
                                                    covered_negative_tuples)
        predicate.rules.pop()
        if better_rule:
          new_rule = sub_rule
          found_rule = True
          break
      if not found_rule:
        break
    predicate.rules.append(new_rule)
    rule_removed = True
    while rule_removed:
      rule_removed = False
      for i in xrange(len(predicate.rules)):
        rule = predicate.rules[i]
        del predicate.rules[i]
        if determine_tuples_covered_same_or_better(predicate, 
                                                   positive_tuples, 
                                                   negative_tuples):
          rule_removed = True
          break
        else:
          predicate.rules.insert(i, rule)    
  logger.debug("End " + predicate_rules_postprocessing_compact.func_name)
          
def predicate_rules_postprocessing(predicate, 
                                   positive_tuples, 
                                   negative_tuples):
  s = time.clock()
  predicate_rules_postprocessing_compact(predicate,
                                         positive_tuples,
                                         negative_tuples)
  f = time.clock()
  logger.debug(predicate_rules_postprocessing_compact.func_name 
                      + " completed in %s seconds." % (f-s))

##############################################################################
# Main entry point for the FOIL algorithm.
##############################################################################          
def foil(predicate, positive_tuples, negative_tuples, bk, ordering=None):
  s = time.clock()
  foil_main(predicate, positive_tuples, negative_tuples, bk, ordering)
  f = time.clock()
  logger.debug(foil_main.func_name 
                      + " completed in %s seconds." % (f-s))
  predicate_rules_postprocessing(predicate, positive_tuples, negative_tuples)
    
def foil_main(predicate, positive_tuples, negative_tuples, bk, ordering=None):
  arity = predicate.arity
  clauses = set([])
  variable_factory = UniqueVariableFactory()
  params = variable_factory.next_variable_sequence(predicate.arity, 
                                                   prefix="PARAM_")
  training_set = TrainingSet(predicate, 
                             params, 
                             positive_tuples, 
                             negative_tuples)
  while len(training_set.positive_examples) > 0:
    head = tuple(training_set.variables)
    for x in head: x.depth = 0
    body = []
    rule = MutableRule(predicate, head, body)
    predicate.rules.append(rule)
    construct_clause_recursive(predicate, 
                               rule, 
                               training_set, 
                               bk, 
                               variable_factory=variable_factory, 
                               ordering=ordering)
