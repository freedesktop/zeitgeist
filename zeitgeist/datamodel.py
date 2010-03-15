# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
# Copyright © 2009 Markus Korn <thekorn@gmx.de>
# Copyright © 2009 Seif Lotfy <seif@lotfy.com>
# Copyright © 2009-2010 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
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
import time
import sys
gettext.install("zeitgeist", unicode=1)

__all__ = [
	'Interpretation',
	'SubjectInterpretation',
	'Manifestation',
	'SubjectManifestation',
	'ResultType',
	'StorageState',
	'TimeRange',
	'DataSource',
	'Event',
	'Subject',
	'NULL_EVENT',
]

# next() function is python >= 2.6
try:
	next = next
except NameError:
	# workaround this for older python versions
	_default_next = object()
	def next(iterator, default=_default_next):
		try:
			return iterator.next()
		except StopIteration:
			if default is not _default_next:
				return default
			raise

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
	
def get_timestamp_for_now():
	"""
	Return the current time in milliseconds since the Unix Epoch.
	"""
	return int(time.time() * 1000)
		

class enum_factory(object):
	"""factory for enums"""
	counter = 0
	
	def __init__(self, doc):
		self.__doc__ = doc
		self._id = enum_factory.counter
		enum_factory.counter += 1
		
		
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
	
def get_name_or_str(obj):
	try:
		return str(obj.name)
	except AttributeError:
		return str(obj)
	
class Symbol(str):
	
	def __new__(cls, name, parent=None, uri=None, display_name=None, doc=None):
		if not isCamelCase(name):
			raise ValueError("Naming convention requires symbol name to be CamelCase, got '%s'" %name)
		return super(Symbol, cls).__new__(Symbol, uri or name)
		
	def __init__(self, name, parent=None, uri=None, display_name=None, doc=None):
		self.__children = dict()
		self.__parents = parent or set()
		assert isinstance(self.__parents, set), name
		self.__name = name
		self.__uri = uri
		self.__display_name = display_name
		self.__doc = doc
		self._resolve_children(False)
		
	def _resolve_children(self, must_finish=True):
		if not self.__parents:
			return
		for parent in self.__parents.copy():
			parent_obj = None
			if isinstance(parent, self.__class__):
				if self in parent.get_children():
					# symbol is already as child of parent symbol
					continue
				parent_obj = parent
			elif not isinstance(parent, (str, unicode)):
				continue
			if parent_obj is None:
				# if parent_obj is still None try to explicitly lookup
				# the symbol by its uri, look in both possible symbol
				# collections
				try:
					parent_obj = Manifestation[parent]
				except KeyError:
					try:
						parent_obj = Interpretation[parent]
					except KeyError:
						# looks like there is not way to find this symbol
						parent_obj = None
			if isinstance(parent_obj, self.__class__):
				parent_obj._add_child(self)
				self.__parents.remove(parent)
				self.__parents.add(parent_obj)
		
		missing_symbols = filter(lambda x: not isinstance(x, self.__class__), self.__parents)
		if missing_symbols:
			if must_finish:
				raise RuntimeError("Unable to resolve symbols: %s"
				                   % ", ".join(missing_symbols))
			else:
				NEEDS_CHILD_RESOLUTION.add(self)

	def __repr__(self):
		return "<%s '%s'>" %(", ".join(get_name_or_str(i) for i in self.get_all_parents()), self.uri)
		
	def __getitem__(self, name):
		""" Get a symbol by its URI. """
		if isinstance(name, int):
			# lookup by index
			return super(Symbol, self).__getitem__(name)
		# look in immediate children first
		symbols = (s for s in self.get_children() if s.uri == name)
		symbol = next(symbols, False)
		if symbol:
			assert not next(symbols, False), "There is more than one symbol with uri='%s'" %name
			return symbol
		# if we still have no luck we try to look in all children
		symbols = (s for s in self.iter_all_children() if s.uri == name)
		symbol = next(symbols, False)
		if symbol:
			assert not next(symbols, False), "There is more than one symbol with uri='%s'" %name
			return symbol
		raise KeyError("Could not find symbol for URI: %s" % name)
		
	def __getattr__(self, name):
		children = dict((s.name, s) for s in self.get_all_children() if s is not self)
		try:
			return children[name]
		except KeyError:
			if not isCamelCase(name):
				# Symbols must be CamelCase
				raise AttributeError("%s has no attribute '%s'" % (
					self.__name__, name))
			print >> sys.stderr, "Unrecognized %s: %s" % (self.__name__, name)
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
		"""
		Returns a list of immediate child symbols
		"""
		return frozenset(self.__children.itervalues())
		
	def iter_all_children(self):
		"""
		Returns a generator that recursively iterates over all children
		of this symbol
		"""
		yield self
		for child in self.__children.itervalues():
			for sub_child in child.iter_all_children():
				yield sub_child
		
	def get_all_children(self):
		"""
		Return a read-only set containing all children of this symbol
		"""
		return frozenset(self.iter_all_children())
		
	def get_parents(self):
		"""
		Returns a list of immediate parent symbols
		"""
		return frozenset(self.__parents)
		
	def iter_all_parents(self):
		"""
		Returns a generator that recursively iterates over all parents
		of this symbol
		"""
		yield self
		for parent_symbol in self.__parents:
			for parent in parent_symbol.iter_all_parents():
				yield parent
		
	def get_all_parents(self):
		"""
		Return a read-only set containing all parents of this symbol
		"""
		return frozenset(self.iter_all_parents())
		
		
class TimeRange(list):
	"""
	A class that represents a time range with a beginning and an end.
	The timestamps used are integers representing milliseconds since the
	Epoch.
	
	By design this class will be automatically transformed to the DBus
	type (xx).
	"""
	# Maximal value of our timestamps
	_max_stamp = 2**63 - 1
	
	def __init__ (self, begin, end):
		super(TimeRange, self).__init__((int(begin), int(end)))
	
	def __eq__ (self, other):
		return self.begin == other.begin and self.end == other.end
	
	def __str__ (self):
		return "(%s, %s)" % (self.begin, self.end)
	
	def get_begin(self):
		return self[0]
	
	def set_begin(self, begin):
		self[0] = begin
	begin = property(get_begin, set_begin,
	doc="The begining timestamp of this time range")
	
	def get_end(self):
		return self[1]
	
	def set_end(self, end):
		self[1] = end
	end = property(get_end, set_end,
	doc="The end timestamp of this time range")
	
	@classmethod
	def until_now(cls):
		"""
		Return a :class:`TimeRange` from 0 to the instant of invocation
		"""
		return cls(0, int(time.time() * 1000))
	
	@classmethod
	def from_now(cls):
		"""
		Return a :class:`TimeRange` from the instant of invocation to
		the end of time
		"""
		return cls(int(time.time() * 1000), cls._max_stamp)
	
	@classmethod
	def from_seconds_ago(cls, sec):
		"""
		Return a :class:`TimeRange` ranging from "sec" seconds before
		the instant of invocation to the same.
		"""
		now = int(time.time() * 1000)
		return cls(now - (sec * 1000), now)
	
	@classmethod
	def always(cls):
		"""
		Return a :class:`TimeRange` from the furtest past to the most
		distant future
		"""
		return cls(-cls._max_stamp, cls._max_stamp)
		
	def intersect(self, time_range):
		"""
		Return a new :class:`TimeRange` that is the intersection of the
		two time range intervals. If the intersection is empty this
		method returns :const:`None`.
		"""
		# Behold the boolean madness!
		result = TimeRange(0,0)
		if self.begin < time_range.begin:
			if self.end < time_range.begin:
				return None
			else:
				result.begin = time_range.begin
		else:
			if self.begin > time_range.end:
				return None
			else:
				result.begin = self.begin
		
		if self.end < time_range.end:
			if self.end < time_range.begin:
				return None
			else:
				 result.end = self.end
		else:
			if self.begin > time_range.end:
				return None
			else:
				result.end = time_range.end
		
		return result
		
		
class RelevantResultType(object):
	"""
	An enumeration class used to define how query results should be returned
	from the Zeitgeist engine.
	"""
	__metaclass__ = EnumMeta
	
	Recent = enum_factory("All uris with the most recent uri first")
	Related = enum_factory("All uris with the most related one first")
	
	
class Subject(list):
	"""
	Represents a subject of an :class:`Event`. This class is both used to
	represent actual subjects, but also create subject templates to match
	other subjects against.
	
	Applications should normally use the method :meth:`new_for_values` to
	create new subjects.
	"""
	Fields = (Uri,
		Interpretation,
		Manifestation,
		Origin,
		Mimetype,
		Text,
		Storage) = range(7)
	
	def __init__(self, data=None):
		super(Subject, self).__init__([""]*len(Subject.Fields))
		if data:
			if len(data) != len(Subject.Fields):
				raise ValueError(
					"Invalid subject data length %s, expected %s"
					% (len(data), len(Subject.Fields)))
			super(Subject, self).__init__(data)
		else:
			super(Subject, self).__init__([""]*len(Subject.Fields))
		
	def __repr__(self):
		return "%s(%s)" %(
			self.__class__.__name__, super(Subject, self).__repr__()
		)
	
	@staticmethod
	def new_for_values (**values):
		"""
		Create a new Subject instance and set its properties according
		to the keyword arguments passed to this method.
		
		:param uri: The URI of the subject. Eg. *file:///tmp/ratpie.txt*
		:param interpretation: The interpretation type of the subject, given either as a string URI or as a :class:`Interpretation` instance
		:param manifestation: The manifestation type of the subject, given either as a string URI or as a :class:`Manifestation` instance
		:param origin: The URI of the location where subject resides or can be said to originate from
		:param mimetype: The mimetype of the subject encoded as a string, if applicable. Eg. *text/plain*.
		:param text: Free form textual annotation of the subject.
		:param storage: String identifier for the storage medium of the subject. This should be the UUID of the volume or the string "net" for resources requiring a network interface, and the string "deleted" for subjects that are deleted.
		"""
		self = Subject()
		for key, value in values.iteritems():
			setattr(self, key, value)
		return self
		
	def get_uri(self):
		return self[Subject.Uri]
		
	def set_uri(self, value):
		self[Subject.Uri] = value
	uri = property(get_uri, set_uri,
	doc="Read/write property with the URI of the subject encoded as a string")
		
	def get_interpretation(self):
		return self[Subject.Interpretation]
		
	def set_interpretation(self, value):
		self[Subject.Interpretation] = value
	interpretation = property(get_interpretation, set_interpretation,
	doc="Read/write property defining the :class:`interpretation type <Interpretation>` of the subject") 
		
	def get_manifestation(self):
		return self[Subject.Manifestation]
		
	def set_manifestation(self, value):
		self[Subject.Manifestation] = value
	manifestation = property(get_manifestation, set_manifestation,
	doc="Read/write property defining the :class:`manifestation type <Manifestation>` of the subject")
		
	def get_origin(self):
		return self[Subject.Origin]
		
	def set_origin(self, value):
		self[Subject.Origin] = value
	origin = property(get_origin, set_origin,
	doc="Read/write property with the URI of the location where the subject resides or where it can be said to originate from")
		
	def get_mimetype(self):
		return self[Subject.Mimetype]
		
	def set_mimetype(self, value):
		self[Subject.Mimetype] = value
	mimetype = property(get_mimetype, set_mimetype,
	doc="Read/write property containing the mimetype of the subject (encoded as a string) if applicable")
	
	def get_text(self):
		return self[Subject.Text]
		
	def set_text(self, value):
		self[Subject.Text] = value
	text = property(get_text, set_text,
	doc="Read/write property with a free form textual annotation of the subject")
		
	def get_storage(self):
		return self[Subject.Storage]
		
	def set_storage(self, value):
		self[Subject.Storage] = value
	storage = property(get_storage, set_storage,
	doc="Read/write property with a string id of the storage medium where the subject is stored. Fx. the UUID of the disk partition or just the string 'net' for items requiring network interface to be available")
	
	def matches_template (self, subject_template):
		"""
		Return True if this Subject matches *subject_template*. Empty
		fields in the template are treated as wildcards.
		
		See also :meth:`Event.matches_template`
		"""
		for m in Subject.Fields:
			if subject_template[m] and subject_template[m] != self[m] :
				return False
		return True

class Event(list):
	"""
	Core data structure in the Zeitgeist framework. It is an optimized and
	convenient representation of an event.
	
	This class is designed so that you can pass it directly over
	DBus using the Python DBus bindings. It will automagically be
	marshalled with the signature a(asaasay). See also the section
	on the :ref:`event serialization format <event_serialization_format>`.
	
	This class does integer based lookups everywhere and can wrap any
	conformant data structure without the need for marshalling back and
	forth between DBus wire format. These two properties makes it highly
	efficient and is recommended for use everywhere.
	"""
	Fields = (Id,
		Timestamp,
		Interpretation,
		Manifestation,
		Actor) = range(5)
	
	def __init__(self, struct = None):
		"""
		If 'struct' is set it must be a list containing the event
		metadata in the first position, and optionally the list of
		subjects in the second position, and again optionally the event
		payload in the third position.
		
		Unless the event metadata contains a timestamp the event will
		have its timestamp set to "now". Ie. the instant of invocation.
		
		The event metadata (struct[0]) will be used as is, and must
		contain the event data on the positions defined by the
		Event.Fields enumeration.
		
		Likewise each member of the subjects (struct[1]) must be an
		array with subject metadata defined in the positions as laid
		out by the Subject.Fields enumeration.
		
		On the third position (struct[2]) the struct may contain the
		event payload, which can be an arbitrary binary blob. The payload
		will be transfered over DBus with the 'ay' signature (as an
		array of bytes).
		"""
		super(Event, self).__init__()
		if struct:
			if len(struct) == 1:
				self.append(struct[0])
				self.append([])
				self.append("")
			elif len(struct) == 2:
				self.append(struct[0])
				self.append(map(Subject, struct[1]))
				self.append("")
			elif len(struct) == 3:
				self.append(struct[0])
				self.append(map(Subject, struct[1]))
				self.append(struct[2])
			else:
				raise ValueError("Invalid struct length %s" % len(struct))
		else:
			self.extend(([""]* len(Event.Fields), [], ""))
		
		# If we have no timestamp just set it to now
		if not self[0][Event.Timestamp]:
			self[0][Event.Timestamp] = str(get_timestamp_for_now())
		
	@classmethod
	def new_for_data(cls, event_data):
		"""
		Create a new Event setting event_data as the backing array
		behind the event metadata. The contents of the array must
		contain the event metadata at the positions defined by the
		Event.Fields enumeration.
		"""
		self = cls()
		if len(event_data) != len(cls.Fields):
			raise ValueError("event_data must have %s members, found %s" % \
				(len(cls.Fields), len(event_data)))
		self[0] = event_data
		return self
		
	@classmethod
	def new_for_struct(cls, struct):
		"""Returns a new Event instance or None if `struct` is a `NULL_EVENT`"""
		if struct == NULL_EVENT:
			return None
		return cls(struct)
	
	@classmethod
	def new_for_values(cls, **values):
		"""
		Create a new Event instance from a collection of keyword
		arguments.
		
		 
		:param timestamp: Event timestamp in milliseconds since the Unix Epoch 
		:param interpretaion: The Interpretation type of the event
		:param manifestation: Manifestation type of the event
		:param actor: The actor (application) that triggered the event
		:param subjects: A list of :class:`Subject` instances
		
		Instead of setting the *subjects* argument one may use a more
		convenient approach for events that have exactly one Subject.
		Namely by using the *subject_** keys - mapping directly to their
		counterparts in :meth:`Subject.new_for_values`:
		
		:param subject_uri:
		:param subject_interpretation:
		:param subject_manifestation:
		:param subject_origin:
		:param subject_mimetype:
		:param subject_text:
		:param subject_storage:
		 
		
		"""
		self = cls()
		self.timestamp = values.get("timestamp", self.timestamp)
		self.interpretation = values.get("interpretation", "")
		self.manifestation = values.get("manifestation", "")
		self.actor = values.get("actor", "")
		self.subjects = values.get("subjects", self.subjects)
		
		if self._dict_contains_subject_keys(values):
			if "subjects" in values:
				raise ValueError("Subject keys, subject_*, specified together with full subject list")
			subj = Subject()
			subj.uri = values.get("subject_uri", "")
			subj.interpretation = values.get("subject_interpretation", "")
			subj.manifestation = values.get("subject_manifestation", "")
			subj.origin = values.get("subject_origin", "")
			subj.mimetype = values.get("subject_mimetype", "")
			subj.text = values.get("subject_text", "")
			subj.storage = values.get("subject_storage", "")
			self.subjects = [subj]
		
		return self
	
	@staticmethod
	def _dict_contains_subject_keys (dikt):
		if "subject_uri" in dikt : return True
		elif "subject_interpretation" in dikt : return True
		elif "subject_manifestation" in dikt : return True
		elif "subject_origin" in dikt : return True
		elif "subject_mimetype" in dikt : return True
		elif "subject_text" in dikt : return True
		elif "subject_storage" in dikt : return True
		return False
	
	def __repr__(self):
		return "%s(%s)" %(
			self.__class__.__name__, super(Event, self).__repr__()
		)
	
	def append_subject(self, subject=None):
		"""
		Append a new empty Subject and return a reference to it
		"""
		if not subject:
			subject = Subject()
		self.subjects.append(subject)
		return subject
	
	def get_subjects(self):
		return self[1]	
	
	def set_subjects(self, subjects):
		self[1] = subjects
	subjects = property(get_subjects, set_subjects,
	doc="Read/write property with a list of :class:`Subjects <Subject>`")
		
	def get_id(self):
		val = self[0][Event.Id]
		return int(val) if val else 0
	id = property(get_id,
	doc="Read only property containing the the event id if the event has one")
	
	def get_timestamp(self):
		return self[0][Event.Timestamp]
	
	def set_timestamp(self, value):
		self[0][Event.Timestamp] = str(value)
	timestamp = property(get_timestamp, set_timestamp,
	doc="Read/write property with the event timestamp defined as milliseconds since the Epoch. By default it is set to the moment of instance creation")
	
	def get_interpretation(self):
		return self[0][Event.Interpretation]
	
	def set_interpretation(self, value):
		self[0][Event.Interpretation] = value
	interpretation = property(get_interpretation, set_interpretation,
	doc="Read/write property defining the interpretation type of the event") 
	
	def get_manifestation(self):
		return self[0][Event.Manifestation]
	
	def set_manifestation(self, value):
		self[0][Event.Manifestation] = value
	manifestation = property(get_manifestation, set_manifestation,
	doc="Read/write property defining the manifestation type of the event")
	
	def get_actor(self):
		return self[0][Event.Actor]
	
	def set_actor(self, value):
		self[0][Event.Actor] = value
	actor = property(get_actor, set_actor,
	doc="Read/write property defining the application or entity responsible for emitting the event. For applications the format of this field is base filename of the corresponding .desktop file with an `app://` URI scheme. For example `/usr/share/applications/firefox.desktop` is encoded as `app://firefox.desktop`")
	
	def get_payload(self):
		return self[2]
	
	def set_payload(self, value):
		self[2] = value
	payload = property(get_payload, set_payload,
	doc="Free form attachment for the event. Transfered over DBus as an array of bytes")
	
	def matches_template(self, event_template):
		"""
		Return True if this event matches *event_template*. The
		matching is done where unset fields in the template is
		interpreted as wild cards. If the template has more than one
		subject, this event matches if at least one of the subjects
		on this event matches any single one of the subjects on the
		template.
		
		Basically this method mimics the matching behaviour
		found in the :meth:`FindEventIds` method on the Zeitgeist engine.
		"""
		# We use direct member access to speed things up a bit
		# First match the raw event data
		data = self[0]
		tdata = event_template[0]
		for m in Event.Fields:
			if m == Event.Timestamp : continue
			if tdata[m] and tdata[m] != data[m] : return False
		
		# If template has no subjects we have a match
		if len(event_template[1]) == 0 : return True
		
		# Now we check the subjects
		for tsubj in event_template[1]:
			for subj in self[1]:		
				if not subj.matches_template(tsubj) : continue				
				# We have a matching subject, all good!
				return True
		
		# Template has subjects, but we never found a match
		return False
	
	def matches_event (self, event):
		"""
		Interpret *self* as the template an match *event* against it.
		This method is the dual method of :meth:`matches_template`.
		"""
		return event.matches_template(self)
	
	def in_time_range (self, time_range):
		"""
		Check if the event timestamp lies within a :class:`TimeRange`
		"""
		t = int(self.timestamp) # The timestamp may be stored as a string
		return (t >= time_range.begin) and (t <= time_range.end)

class DataSource(list):
	""" Optimized and convenient data structure representing a datasource.
	
	This class is designed so that you can pass it directly over
	DBus using the Python DBus bindings. It will automagically be
	marshalled with the signature a(asaasay). See also the section
	on the :ref:`event serialization format <event_serialization_format>`.
	
	This class does integer based lookups everywhere and can wrap any
	conformant data structure without the need for marshalling back and
	forth between DBus wire format. These two properties makes it highly
	efficient and is recommended for use everywhere.
	"""
	Fields = (UniqueId,
		Name,
		Description,
		EventTemplates,
		Running,
		LastSeen,
		Enabled) = range(7)
	
	def __init__(self, unique_id, name, description, templates, running=True,
		last_seen=None, enabled=True):
		"""
		Create a new DataSource object using the given parameters.
		
		If you want to instantiate this class from a dbus.Struct, you can
		use: DataSource(*data_source), where data_source is the dbus.Struct.
		"""
		super(DataSource, self).__init__()
		self.append(unique_id)
		self.append(name)
		self.append(description)
		self.append(templates)
		self.append(running)
		self.append(last_seen if last_seen else get_timestamp_for_now())
		self.append(enabled)
	
	def __eq__(self, source):
		return self[self.UniqueId] == source[self.UniqueId]
	
	def __repr__(self):
		return "%s: %s (%s)" % (self.__class__.__name__, self[self.UniqueId],
			self[self.Name])

NULL_EVENT = ([], [], [])
"""Minimal Event representation, a tuple containing three empty lists.
This `NULL_EVENT` is used by the API to indicate a queried but not
available (not found or blocked) Event.
"""
		
		
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


INTERPRETATION_DOC = \
"""In general terms the *interpretation* of an event or subject is an abstract
description of *"what happened"* or *"what is this"*.

Each interpretation type is uniquely identified by a URI. This class provides
a list of hard coded URI constants for programming convenience. In addition;
each interpretation instance in this class has a *display_name* property, which
is an internationalized string meant for end user display.

The interpretation types listed here are all subclasses of *str* and may be
used anywhere a string would be used.

Interpretations form a hierarchical type tree. So that fx. Audio, Video, and
Image all are sub types of Media. These types again have their own sub types,
like fx. Image has children Icon, Photo, and VectorImage (among others).

Templates match on all sub types, so that a query on subjects with
interpretation Media also match subjects with interpretations
Audio, Photo, and all other sub types of Media.
"""

MANIFESTATION_DOC = \
"""The manifestation type of an event or subject is an abstract classification
of *"how did this happen"* or *"how does this item exist"*.

Each manifestation type is uniquely identified by a URI. This class provides
a list of hard coded URI constants for programming convenience. In addition;
each interpretation instance in this class has a *display_name* property, which
is an internationalized string meant for end user display.

The manifestation types listed here are all subclasses of *str* and may be
used anywhere a string would be used.

Manifestations form a hierarchical type tree. So that fx. ArchiveItem,
Attachment, and RemoteDataObject all are sub types of FileDataObject.
These types can again have their own sub types.

Templates match on all sub types, so that a query on subjects with manifestation
FileDataObject also match subjects of types Attachment or ArchiveItem and all
other sub types of FileDataObject
"""

start_symbols = time.time()

Interpretation = SubjectInterpretation = Symbol("Interpretation", doc=INTERPRETATION_DOC)
Manifestation = SubjectManifestation = Symbol("Manifestation", doc=MANIFESTATION_DOC)

if IS_LOCAL:
	try:
		execfile(os.path.join(runpath, "../extra/ontology/zeitgeist.py"))
	except IOError:
		raise ImportError("Unable to load zeitgeist ontology, "
		                  "please run `make` and try again.")
else:
	#raise NotImplementedError
	# it should be similar to
	execfile("/home/markus/devel/zeitgeist/ontology_definition/extra/ontology/zeitgeist.py")

# try to resolve all lazy references to parent symbols
# this operation is expensive, this is why we only allow 'c' number of
# iterations (a sensible value seems to be the number of symbols needing
# child resolution)

initial_count = c = len(NEEDS_CHILD_RESOLUTION)

while NEEDS_CHILD_RESOLUTION and c:
	symbols = dict((str(i), i) for i in NEEDS_CHILD_RESOLUTION)
	x = dict((str(i), i.get_parents()) for i in NEEDS_CHILD_RESOLUTION)
	c -= 1
	missings_parents = set(sum(map(list, x.values()), []))
	candidates = missings_parents - set(x.keys())
	while candidates:
		candidate = candidates.pop()
		resolveable = filter(lambda v: len(v[1]) == 1 and candidate in v[1], x.items())
		if not resolveable:
			continue
		for uri, parent_uris in resolveable:
			symbol = symbols[uri]
			symbol._resolve_children()
			NEEDS_CHILD_RESOLUTION.remove(symbol)
	
if NEEDS_CHILD_RESOLUTION:
	print >> sys.stderr, ("Cannot resolve children of %r" %NEEDS_CHILD_RESOLUTION)
	raise SystemExit(1)
	
end_symbols = time.time()

if __name__ == "__main__":
	pass
	#~ x = len(Interpretation.get_all_children())
	#~ y = len(Manifestation.get_all_children())
	#~ print >> sys.stderr, \
		#~ ("Overall number of symbols: %i (man.: %i, int.: %i)" %(x+y, y, x))
	#~ print >> sys.stderr, ("Resolved %i symbols, needed %i iterations" %(initial_count, initial_count-c))
	#~ print >> sys.stderr, ("Loading symbols took %.4f seconds" %(end_symbols - start_symbols))
	#~ #
	#~ # shortcuts
	#~ EventManifestation = Manifestation.EventManifestation
	#~ EventInterpretation = Interpretation.EventInterpretation
	#~ 
	#~ DataContainer = Interpretation.DataContainer
	#~ 
	#~ # testing
	#~ print dir(EventManifestation)
	#~ print dir(Manifestation)
	#~ print EventManifestation.UserActivity
	#~ 
	#~ print DataContainer
	#~ print DataContainer.Filesystem
	#~ print DataContainer.Filesystem.__doc__
	#~ 
	#~ print " OR ".join(DataContainer.get_all_children())
	#~ print " OR ".join(DataContainer.Filesystem.get_all_children())
	#~ 
	#~ print DataContainer.Boo
	#~ 
	#~ #Symbol("BOO", DataContainer) #must fail with ValueError
	#~ #Symbol("Boo", DataContainer) #must fail with ValueError
	#~ Symbol("Foo", set([DataContainer,]))
	#~ print DataContainer.Foo
	#~ 
	#~ #DataContainer._add_child("booo") #must fail with TypeError
	#~ 
	#~ print Interpretation
	#~ #print Interpretation.get_all_children()
	#~ import pprint
	#~ pprint.pprint(Interpretation.Software.get_all_children())
	#~ 
	#~ print Interpretation["http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#MindMap"]
