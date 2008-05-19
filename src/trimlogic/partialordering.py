import operator

class Node:
  
  def __init__(self, values):
    self.values = values
    self.edge_list = set()
    self.inverse_edge_list = set()
    
  def add_target(self, node):
    self.edge_list.add(node)
    node.inverse_edge_list.add(self)
    
  def remove_target(self, node):
    self.edge_list.remove(node)
    node.inverse_edge_list.remove(self)
  
  def has_target(self, node):
    return self.edge_list.contains(node)
  
  def clear(self):
    self.values = None
    self.edge_list = None
    self.inverse_edge_list = None
    
  def __hash__(self):
    return sum(map(hash, self.values))
  
  def __repr__(self):
    s = "(" + str(self.values) + ", {"
    if self.edge_list:
      for node in self.edge_list:
        s += str(node.values) + ", "
    s += "})"
    return s


class DirectedGraph(object):
  
  def __init__(self):
    self.object_node_map = {}
    self.nodes = set([])
  
  def enumerate_nodes(self):
    for node in self.object_node_map.values:
      yield node
  
  def remove_node(self, node):
    self.nodes.remove(node)
    for value in node.values:
      if self.object_node_map[value] == Node:
        del self.object_node_map[value]
    for targeting_node in node.inverse_edge_list:
      targeting_node.edge_list.remove(node)
    for targeted_node in node.edge_list:
      targeted_node.inverse_edge_list.remove(node)
    node.clear()
  
  def remove(self, a):
    self.remove_node(self._get_or_create_node(a))
  
  def merge(self, a, b):
    node1 = self._get_or_create_node(a)
    node2 = self._get_or_create_node(b)
    if node1 != node2:
      new_node = Node(node1.values + node2.values)
      for old_node in [node1, node2]:
        # Adjust value to node mapping so that values for old_node now point to new_node.
        for value in old_node.values:
          self.object_node_map[value] = new_node
        # make all nodes targeting old_node now target new_node.
        for targeting_node in old_node.inverse_edge_list:
          targeting_node.edge_list.add(new_node)
        # make all targets of old_node the targets of new_node.
        for target in old_node.edge_list():
          new_node.add_target(target)
        # clear out the references held by old_node to make the GC happy.
        self.remove_node(old_node)
      return new_node
    
  def insert_edge(self, a, b):
    node1 = self._get_or_create_node(a)
    node2 = self._get_or_create_node(b)
    node1.add_target(node2)
    return (node1, node2)
  
  def _get_or_create_node(self, a):
    if not self.object_node_map.has_key(a):
      node = Node([a])
      self.object_node_map[a] = node
      self.nodes.add(node)
    return self.object_node_map[a]
  
  def __del__(self):
    """
    Removes cyclic references between nodes and then calls the object.__del__()
    method to finish garbage collection.
    """
    for node in self.nodes:
      node.clear()
      

def _topological_sort(graph):
  ordering = []
  while graph.nodes:
    removable_nodes = filter(lambda x: len(x.inverse_edge_list) == 0, graph.nodes)
    if not(removable_nodes):
      raise "not an acyclic graph"
    while removable_nodes:
      node = removable_nodes.pop()
      ordering.extend(node.values)
      graph.remove_node(node)
  return ordering


class PartialOrdering:
  
  def __init__(self, graph):
    self.graph = graph
    
  def lt(self, a, b):
    stack = []
    stack.append(self.graph.object_node_map[a])
    while stack:
      node = stack.pop()
      if b in node.values:
        return True
      stack.extend(node.edge_list)
    return False
    
  def gt(self, a, b):
    stack = []
    stack.append(self.graph.object_node_map[a])
    while stack:
      node = stack.pop()
      if b in node.values:
        return True
      stack.extend(node.inverse_edge_list)
    return False
  
  def eq(self, a, b):
    return self.graph.object_node_map[a] == self.graph.object_node_map[b]
  
  def __contains__(self, a):
    return self.graph.object_node_map.has_key(a)


def create_partial_comparator(constraints):
  graph = _build_graph(constraints)
  return PartialOrdering(graph)
  
def _build_graph(constraints):
  graph = DirectedGraph()
  for (op, x, y) in constraints:
    if op == operator.gt:
      graph.insert_edge(y,x)
    elif op == operator.lt:
      graph.insert_edge(x,y)
    elif op == operator.eq and x != y:
      graph.merge(x, y)
  return graph
  
def find_ordering(constraints):
  graph = _build_graph(constraints)
  ordering = _topological_sort(graph)
  return ordering

_TEST = False
if _TEST:
  lt = operator.lt
  print str(find_ordering([(lt, 'x', 'y'),
                           (lt, 'z', 'y'),
                           (lt, 'x', 'z'),
                           ]))
