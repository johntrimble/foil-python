import unittest
from trimlogic.counting import choose

class ChooseTestCase(unittest.TestCase):
  def testBasic00(self):
    for l in choose([0,1],2):
      print str(l)