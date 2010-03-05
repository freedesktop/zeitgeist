import os.path
import gettext
gettext.install("zeitgeist", unicode=1)

runpath = os.path.dirname(__file__)

if not os.path.isfile(os.path.join(runpath, '_config.py.in')):
	# we are in a global installation
	# this means we have already parsed zeo.trig into a python file
	# all we need is to load this python file now
	IS_LOCAL = False
else:
	# we are using zeitgeist `from the branch` in development mode
	# in this mode we would like to use the recent version of our
	# ontology. This is why we parse the ontology to a temporary file
	# and load it from there
	IS_LOCAL = True
	
	
class EnumValue(int):
	"""class which behaves like an int, but has an additional docstring"""
	def __new__(cls, value, doc=""):
		obj = super(EnumValue, cls).__new__(EnumValue, value)
		obj.__doc__ = "%s. ``(Integer value: %i)``" %(doc, obj)
		return obj


class Enum(object):
	
	def __init__(self, docstring):
		self.__doc__ = str(docstring)
		self.__enums = {}
		
	def __getattr__(self, name):
		try:
			return self.__enums[name]
		except KeyError:
			raise AttributeError
			
	def register(self, value, name, docstring):
		ids = map(int, self.__enums.values())
		if value in ids or name in self.__enums:
			raise ValueError
		self.__enums[name] = EnumValue(value, docstring)

	
class Symbol(str):
	
	"""Immutable string-like object representing a Symbol
	Zeitgeist uses Symbols when defining Manifestations and 
	Interpretations.
	"""
	
	def __new__(cls, symbol_type, name, uri=None, display_name=None, doc=None):
		obj = super(Symbol, cls).__new__(Symbol, uri or name)
		obj.__type = symbol_type
		obj.__name = name
		obj.__uri = uri
		obj.__display_name = display_name
		obj.__doc = doc
		return obj
	
	def __repr__(self):
		return "<%s %r>" %(self.__type, self.uri)
	
	@property
	def uri(self):
		return self.__uri or self.name
	
	@property
	def display_name(self):
		return self.__display_name or ""
	
	@property
	def name(self):
		return self.__name
	
	@property
	def doc(self):
		return self.__doc or ""
		
	@property
	def __doc__(self):
		return "%s\n\n	%s. ``(Display name: '%s')``" %(self.uri, self.doc.rstrip("."), self.display_name)


class SymbolCollection(object):
	
	def __init__(self, name, doc=""):
		self.__name__ = name
		self.__doc__ = str(doc)
		self.__symbols = {}
	
	def register(self, name, uri, display_name, doc):
		if name in self.__symbols:
			raise ValueError("Cannot register symbol %r, a definition for "
				"this symbol already exists" % name)
		if not name.isupper():
			raise ValueError("Cannot register %r, name must be uppercase" %name)
		self.__symbols[name] = Symbol(self.__name__, name, uri, display_name, doc)
	
	def __len__(self):
		return len(self.__symbols)
	
	def __getattr__(self, name):
		if not name in self.__symbols:
			if not name.isupper():
				# Symbols must be upper-case
				raise AttributeError("%s has no attribute '%s'" % (
					self.__name__, name))
			print "Unrecognized %s: %s" % (self.__name__, name)
			self.__symbols[name] = Symbol(self.__name__, name)
		return self.__symbols[name]
	
	def __getitem__(self, uri):
		""" Get a symbol by its URI. """
		symbol = [s for s in self.__symbols.values() if s.uri == uri]
		if symbol:
			return symbol[0]
		raise KeyError("Could not find symbol for URI: %s" % uri)
	
	def __iter__(self):
		return self.__symbols.itervalues()
	
	def __dir__(self):
		return self.__symbols.keys()


def register_symbol(collection, name, uri, displayname, docstring):
	collection.register(name, uri, displayname, docstring)
	
def register_enum(enum, value, name, docstring):
	enum.register(value, name, docstring)
	
if IS_LOCAL:
	from tempfile import NamedTemporaryFile
	from subprocess import Popen, PIPE
	fd = NamedTemporaryFile()
	extraddir = os.path.join(runpath, "../extra")
	converter_script = os.path.join(extraddir, "trig2py")
	ontology_trig = os.path.join(extraddir, "ontology/zeo.trig")
	p = Popen([converter_script, ontology_trig], stderr=PIPE, stdout=PIPE)
	if p.wait():
		raise RuntimeError("broken ontology at '%s'" %ontology_trig)
	fd.write(p.stdout.read())
	fd.flush()
	fd.seek(0)
	execfile(fd.name)
	fd.close()
else:
	raise NotImplementedError
	# it should be similar to 
	execfile("/path/of/zeo.trig.py")

if __name__ == "__main__":
	# testing
	print dir(EventManifestation)
	print EventManifestation.USER_ACTIVITY
	
	print StorageState
	print StorageState.Any
	print StorageState.Any.__doc__
