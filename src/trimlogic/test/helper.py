import unittest
from trimlogic.algorithm import fol_bc_ask

PRINT_RULES = True

class FoilTestCase(unittest.TestCase):
  def print_rules(self, predicate):
    if PRINT_RULES:
      print ""
      print "Rules for", predicate, ":"
      for rule in predicate.rules:
        print str(rule)
    
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
