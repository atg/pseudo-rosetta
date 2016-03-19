import os
import json
from re import compile as rx
from pprint import pprint

def parse_symbol_line(line):
  obj = {
    'translations': [],
  }
  
  if '#' in line:
    klass, _, method = line.partition('#')
    obj.update({
      'kind': 'instance_method',
      'class': klass,
      'method': method,
    })
    return obj
  
  print(line)
  assert False

def parse_translation_line(line):
  if 'needs shim' in line:
    return {
      'kind': 'shim_needed',
    }
  
  assert ':' in line
  lang, _, line = line.partition(':')
  line = line.strip()
  
  if '#' in line:
    klass, _, method = line.partition('#')
    return {
      'kind': 'instance_method',
      'class': klass,
      'method': method,
      'lang': lang,
    }
  
  if line == '???':
    return {
      'kind': '???',
    }
  
  print(line)
  assert False

def parse_lines(lines):
  for line in lines:
    before = line
    after = line.lstrip()
    n_indent = len(before) - len(after)
    
    line = COMMENT_RE.sub('', after)
    line = line.strip()
    
    if not line:
      continue
    
    yield (n_indent // 2, line)

COMMENT_RE = rx(r'\s*//.+')
def main():
  nodes = []
  translations = os.listdir('translations')
  for subpath in translations:
    if subpath.startswith('.'): continue
    
    name, ext = os.path.splitext(subpath)
    if ext != '.txt': continue
    
    lines = None
    with open(os.path.join('translations', subpath), 'r') as f:
      lines = list(parse_lines(f))
    
    symbols = []
    for n, line in lines:
      if n == 0:
        symbols.append(parse_symbol_line(line))
      elif n == 1:
        symbols[-1]['translations'] = parse_translation_line(line)
      else:
        assert False
    
    nodes.append({
      'key': name,
      'symbols': symbols,
    })
  
  # print(json.dumps(nodes, sort_keys=True, indent=4, separators=(',', ': ')))
  
  
  ## Part 2
  # Determine which methods we haven't translated yet
  
  # Some methods are not meant to be translated
  blacklisted_methods = set('''
    __class__
    __dir__
    __doc__
    __hash__
    
    __rand__
    __ror__
    __rsub__
    __rxor__
    __subclasshook__
    __reduce__
    __reduce_ex__
    
    __delattr__
    __getattribute__
    __setattr__
    
    __format__
    __iadd__
    __isub__
    __imul__
    __idiv__
    __iand__
    __ior__
    __ixor__
    
    __rmul__
    
    __new__
    __sizeof__
    
    __eq__
    __ne__
    __lt__
    __le__
    __gt__
    __ge__
    
    __all__
    __builtins__
    __cached__
    __file__
    __loader__
    __name__
    __package__
    __spec__
    
  '''.split())
  
  # Map from class names (e.g. set, dict, list) to the Python objects
  klasses = [ set, dict, list ]
  klass_map = { obj.__name__: obj for obj in klasses }
  klass_method_map = { obj.__name__: set(dir(obj())) - blacklisted_methods for obj in klasses }
  
  import random
  import time
  modules = [ random, time ]
  module_item_map = { obj.__name__: set(dir(obj)) - blacklisted_methods for obj in modules }
  module_item_map = { k: { x for x in vs if not x.startswith('_') } for k, vs in module_item_map.items() }
  # pprint(module_item_map)
  # return
  
  symbol_method_map = {}
  
  # pprint(klass_method_map)
  # return
  
  for node in nodes:
    for symbol in node['symbols']:
      if symbol['kind'] != 'instance_method': continue
      
      class_name = symbol['class']
      if class_name not in symbol_method_map:
        symbol_method_map[class_name] = set()
      
      symbol_method_map[class_name].add(symbol['method'])
  
  tried_classes = set()
  for node in nodes:
    for symbol in node['symbols']:
      klass_name = symbol['class']
      klass = klass_map[klass_name]
      
      if klass_name in tried_classes: continue
      tried_classes.add(klass_name)
      
      instance_methods = klass_method_map[klass_name]
      our_instance_methods = symbol_method_map[klass_name]
      
      illegal_methods = our_instance_methods - instance_methods
      if len(illegal_methods) > 0:
        print("Found illegal methods!", illegal_methods)
        assert len(illegal_methods) == 0
      
      leftover_instance_methods = instance_methods - our_instance_methods
      print("Missing methods for '%s'" % klass_name)
      pprint(leftover_instance_methods)
      print('')
      

if __name__ == '__main__':
  # Set cwd to script directory
  os.chdir(os.path.dirname(os.path.abspath(__file__)))
  main()