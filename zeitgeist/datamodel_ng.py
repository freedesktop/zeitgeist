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
