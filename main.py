import os, sys
import inspect
from re import compile as rx
from pprint import pprint

'''
Plan for Python API -> Intermediate API: [pseudo_python/api_translator.py]
  * Generate a "default map" of Python API functions to the Intermediate API.
  * Augment (in code) the default map when it is insufficient or incorrect.
  * Generate JSON for the new augmented map. [Maybe it would be better to generate code instead of JSON?]

Plan for Intermediate API -> Other Languages' APIs: [pseudo/api_translators/<lang>_translator.py]
  * Use sugar.js's mappings

Base the Intermediate API on Python to make it easier.



'''




ARG_TOK_RE = rx(r'\[,|,|\[|\]|[a-zA-Z0-9_=*\-\'\"]+|\S')

class Type:
  def __init__(self, klass):
    self.name = klass.__name__
    self.klass = klass
    self.methods = dir(klass)
    self.methods_map = {
      name: self.get_method(name)
      for name in self.methods
    }
  
  def parse_doc(self, name, doc):
    # There is a slightly more annotated python stdlib at: https://github.com/python/mypy/blob/master/lib-python/3.2
    # typing.get_type_hints
    def parse_args(toks):
      optional = 0
      for i, tok in enumerate(toks):
        if tok == '[,':
          optional += 1
          continue
        if tok == '[':
          optional += 1
          continue
        if tok == ']':
          optional -= 1
          continue
        if tok == ',':
          continue
        
        if '=' in tok:
          yield {
            'name': tok[:tok.find('=')],
            'optional': True,
            'kind': 'normal',
            'default': tok[tok.find('=')+1:],
          }
        else:
          kind = 'normal'
          if tok.startswith('**'):
            tok = tok[2:]
            kind = 'kwargs'
          elif tok.startswith('*'):
            tok = tok[1:]
            kind = 'args'
          
          yield {
            'name': tok,
            'optional': optional > 0,
            'kind': kind,
            'default': None,
          }
    
    FAIL = {
      'args': [],
      'returns': None,
    }
    if not doc: return FAIL
    lines = (l.strip() for l in doc.splitlines(False))
    lines = [l for l in lines if l]
    
    for line in lines:
      if '->' in line:
        if '--' in line:
          line = line[:line.rfind('--')]
        if '.' in line:
          line = line[line.find('.')+1:]
        left, _, right = line.rpartition('->')
        left = left.strip()
        right = right.strip()
        # print(' ', left, '->', right)
        
        # Strip off the name
        if left.startswith(name):
          left = left[len(name):]
        if left.startswith('(') and left.endswith(')'):
          left = left[1:-1]
        
        left = ARG_TOK_RE.findall(left)
        return {
          'prototype': line,
          'args': list(parse_args(left)),
          'returns': right,
        }
    return FAIL
  
  def get_method(self, name):
    obj = getattr(self.klass, name)
    doc = obj.__doc__
    
    info = {
      'name': name,
      'doc': doc,
    }
    info.update(self.parse_doc(name, doc))
    return info
    
    
  def show(self):
    print("~~ %s ~~" % self.name)
    for name in self.methods:
      info = self.methods_map[name]
      args = info.get('args')
      if args:
        print('%s#%s' % (self.name, info['prototype']))
      else:
        left = '%s#%s' % (self.name, name)
        doc = info['doc']
        if not doc:
          doc = ""
        doc = doc.replace("\n", " ")
        
        MARGIN = 50
        if len(left) < MARGIN:
          left += " " * (MARGIN - len(left))
        print(left + doc)
        # print("\n")

def main():
  root = __builtins__
  names = dir(__builtins__)
  
  blacklist = {
    'classmethod',
    'enumerate',
    'filter',
    'map',
    'property',
    'range',
    'reversed',
    'staticmethod',
    'type',
    'zip',
    'super',
    'memoryview',
  }
  
  # names = ['str', ]
  for name in names:
    obj = getattr(root, name)
    if not inspect.isclass(obj): continue
    if issubclass(obj, BaseException): continue # ignore exceptions
    if name.startswith('_'): continue # ignore privates
    if name in blacklist: continue
    
    t = Type(getattr(root, name))
    t.show()
    
    
  
if __name__ == '__main__':
  main()