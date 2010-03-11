# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Markus Korn <thekorn@gmx.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os.path
import gettext
gettext.install("zeitgeist", unicode=1)

runpath = os.path.dirname(__file__)

NEEDS_CHILD_RESOLUTION = set()

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
		
		
def isCamelCase(text):
	return text and text[0].isupper() and " " not in text
	
class Symbol(str):
	
	def __new__(cls, name, parent=None, uri=None, display_name=None, doc=None):
		if not isCamelCase(name):
			raise ValueError("Naming convention requires symbol name to be CamelCase, got '%s'" %name)
		return super(Symbol, cls).__new__(Symbol, uri or name)
		
	def __init__(self, name, parent=None, uri=None, display_name=None, doc=None):
		self.__children = dict()
		self.__parent = parent or set()
		assert isinstance(self.__parent, set), name
		self.__name = name
		self.__uri = uri
		self.__display_name = display_name
		self.__doc = doc
		self._resolve_children(False)
		
	def _resolve_children(self, must_finish=True):
		if self.__parent is None:
			return
		for parent in self.__parent.copy():
			if not isinstance(parent, (str, unicode)):
				continue
			parent_obj = globals().get(parent)
			if parent_obj is None:
				parent_obj = globals().get(parent.split("#")[-1])
			if isinstance(parent_obj, self.__class__):
				parent_obj._add_child(self)
				self.__parent.remove(parent)
				self.__parent.add(parent_obj)
		finished = all(map(lambda x: isinstance(x, self.__class__), self.__parent))
		if not finished:
			if must_finish:
				raise RuntimeError("Cannot resolve all parent symbols")
			else:
				NEEDS_CHILD_RESOLUTION.add(self)

	def __repr__(self):
		return "<%s %r>" %(self.__parent, self.uri)
		
	def __getitem__(self, name):
		""" Get a symbol by its URI. """
		if isinstance(name, int):
			# lookup by index
			return super(Symbol, self).__getitem__(name)
		symbol = [s for s in self.__children.values() if s.uri == uri]
		if symbol:
			return symbol[0]
		raise KeyError("Could not find symbol for URI: %s" % uri)
		
	def __getattr__(self, name):
		children = dict((s.name, s) for s in self.get_all_children())
		try:
			return children[name]
		except KeyError:
			if not isCamelCase(name):
				# Symbols must be CamelCase
				raise AttributeError("%s has no attribute '%s'" % (
					self.__name__, name))
			print "Unrecognized %s: %s" % (self.__name__, name)
			# symbol is auto-added as child of this symbol
			s = Symbol(name, parent=set([self,]))
			return s

	@property
	def uri(self):
		return self.__uri or self.name

	@property
	def display_name(self):
		return self.__display_name or ""

	@property
	def name(self):
		return self.__name
	__name__ = name
	
	def __dir__(self):
		return self.__children.keys()

	@property
	def doc(self):
		return self.__doc or ""

	@property
	def __doc__(self):
		return "%s\n\n	%s. ``(Display name: '%s')``" %(self.uri, self.doc.rstrip("."), self.display_name)
		
	def _add_child(self, symbol):
		if not isinstance(symbol, self.__class__):
			raise TypeError("Child-Symbols must be of type '%s', got '%s'" %(self.__class__.__name__, type(symbol)))
		if symbol.name in self.__children:
			raise ValueError(
				("There is already a Symbol called '%s', "
				 "cannot register a symbol with the same name") %symbol.name)
		self.__children[symbol.name] = symbol
		
	def get_children(self):
		return self.__children.values()
		
	def iter_all_children(self):
		yield self
		for child in self.__children.itervalues():
			for sub_child in child.iter_all_children():
				yield sub_child
		
	def get_all_children(self):
		return set(self.iter_all_children())
		
	def get_parent(self):
		return self.__parent
		
	def iter_all_parent(self):
		yield self
		if self.__parent is not None:
			for parent in self.__parent.iter_all_parent():
				yield parent
		
	def get_all_parent(self):
		return set(self.iter_all_parent())
		

class enum_factory(object):
	"""factory for enums"""
	counter = 0
	
	def __init__(self, doc):
		self.__doc__ = doc
		self._id = enum_factory.counter
		enum_factory.counter += 1
		

class EnumValue(int):
	"""class which behaves like an int, but has an additional docstring"""
	def __new__(cls, value, doc=""):
		obj = super(EnumValue, cls).__new__(EnumValue, value)
		obj.__doc__ = "%s. ``(Integer value: %i)``" %(doc, obj)
		return obj
		
		
class EnumMeta(type):
	"""Metaclass to register enums in correct order and assign interger
	values to them
	"""
	def __new__(cls, name, bases, attributes):
		enums = filter(
			lambda x: isinstance(x[1], enum_factory), attributes.iteritems()
		)
		enums = sorted(enums, key=lambda x: x[1]._id)
		for n, (key, value) in enumerate(enums):
			attributes[key] = EnumValue(n, value.__doc__)
		return super(EnumMeta, cls).__new__(cls, name, bases, attributes)
		
		
class StorageState(object):
	"""
	Enumeration class defining the possible values for the storage state
	of an event subject.
	
	The StorageState enumeration can be used to control whether or not matched
	events must have their subjects available to the user. Fx. not including
	deleted files, files on unplugged USB drives, files available only when
	a network is available etc.
	"""
	__metaclass__ = EnumMeta
	
	NotAvailable = enum_factory(("The storage medium of the events "
		"subjects must not be available to the user"))
	Available = enum_factory(("The storage medium of all event subjects "
		"must be immediately available to the user"))
	Any = enum_factory("The event subjects may or may not be available")


class ResultType(object):
	"""
	An enumeration class used to define how query results should be returned
	from the Zeitgeist engine.
	"""
	__metaclass__ = EnumMeta
	
	MostRecentEvents = enum_factory("All events with the most recent events first")
	LeastRecentEvents = enum_factory("All events with the oldest ones first")
	MostRecentSubjects = enum_factory(("One event for each subject only, "
		"ordered with the most recent events first"))
	LeastRecentSubjects = enum_factory(("One event for each subject only, "
		"ordered with oldest events first"))
	MostPopularSubjects = enum_factory(("One event for each subject only, "
		"ordered by the popularity of the subject"))
	LeastPopularSubjects = enum_factory(("One event for each subject only, "
		"ordered ascendently by popularity"))
	MostPopularActor = enum_factory(("The last event of each different actor,"
		"ordered by the popularity of the actor"))
	LeastPopularActor = enum_factory(("The last event of each different actor,"
		"ordered ascendently by the popularity of the actor"))
	MostRecentActor = enum_factory(("The last event of each different actor"))
	LeastRecentActor = enum_factory(("The first event of each different actor"))

Interpretation = SubjectInterpretation = Symbol("Interpretation", doc="TBD")
Manifestation = SubjectManifestation = Symbol("Manifestation", doc="TBD")

if IS_LOCAL:
	execfile(os.path.join(runpath, "../extra/ontology/zeitgeist.py"))
else:
	raise NotImplementedError
	# it should be similar to
	execfile("/path/of/zeo.trig.py")
	
for symbol in NEEDS_CHILD_RESOLUTION:
	symbol._resolve_children()

if __name__ == "__main__":
	# testing
	print dir(EventManifestation)
	print EventManifestation.UserActivity
	
	print DataContainer
	print DataContainer.Filesystem
	print DataContainer.Filesystem.__doc__
	
	print " OR ".join(DataContainer.get_all_children())
	print " OR ".join(DataContainer.Filesystem.get_all_children())
	
	print DataContainer.Boo
	
	#~ Symbol("BOO", DataContainer) #must fail with ValueError
	#~ Symbol("Boo", DataContainer) #must fail with ValueError
	Symbol("Foo", set([DataContainer,]))
	print DataContainer.Foo
	
	#~ DataContainer._add_child("booo") #must fail with TypeError
	
	print Interpretation
	#~ print Interpretation.get_all_children()
	import pprint
	pprint.pprint(Interpretation.Software.get_all_children())
	
