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

"""
This module provides the abstract datamodel used by the Zeitgeist framework.
In addition to providing useful constructs for dealing with the Zeitgeist data
it also defines symbolic values for the common item types. Using symbolic values
instead of URI strings will help detect programmer typos.
"""

import time
import gettext
gettext.install("zeitgeist", unicode=1)

def get_timestamp_for_now():
	"""
	Return the current time in milliseconds since the Unix Epoch.
	"""
	return int(time.time() * 1000)

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
		self.__keys = set()
	
	def register(self, name, uri, display_name, doc):
		if name in self.__keys:
			raise ValueError("cannot register symbol %r, a definition for this symbol already exists" %name)
		if not name.isupper():
			raise ValueError("cannot register %r, name must be uppercase" %name)
		self.__dict__[name] = Symbol(self.__name__, name, uri, display_name, doc)
		self.__keys.add(name)
		
	def __len__(self):
		return len(self.__keys)
		
	def __getattr__(self, name):
		if not name.isupper():
			# symbols must be uppercase
			raise AttributeError("'%s' has no attribute '%s'" %(self.__name__, name))
		self.__dict__[name] = Symbol(self.__name__, name)
		return getattr(self, name)
			
	def __dir__(self):
		return list(self.__keys)
		

INTERPREATION_ID = "interpretation"
MANIFESTATION_ID = "manifestation"

INTERPRETATION_DOC = \
"""In general terms the *interpretation* of an event or subject is an abstract
description of *"what happened"* or *"what is this"*.

Each interpretation type is uniquely identified by a URI. This class provides
a list of hard coded URI constants for programming convenience. In addition;
each interpretation instance in this class has a *display_name* property, which
is an internationalized string meant for end user display.

The interpretation types listed here are all subclasses of *str* and may be
used anywhere a string would be used."""

MANIFESTATION_DOC = \
"""The manifestation type of an event or subject is an abstract classification
of *"how did this happen"* or *"how does this item exist"*.

Each manifestation type is uniquely identified by a URI. This class provides
a list of hard coded URI constants for programming convenience. In addition;
each interpretation instance in this class has a *display_name* property, which
is an internationalized string meant for end user display.

The manifestation types listed here are all subclasses of *str* and may be
used anywhere a string would be used."""


Interpretation = SymbolCollection(INTERPREATION_ID, doc=INTERPRETATION_DOC)
Manifestation = SymbolCollection(MANIFESTATION_ID, doc=MANIFESTATION_DOC)

#
# Interpretation categories
#
Interpretation.register(
	"TAG",
	u"http://www.semanticdesktop.org/ontologies/2007/08/15/nao#Tag",
	display_name=_("Tags"),
	doc="User provided tags. The same tag may refer multiple items"
)
Interpretation.register(
	"BOOKMARK",
	u"http://www.semanticdesktop.org/ontologies/nfo/#Bookmark",
	display_name=_("Bookmarks"),
	doc="A user defined bookmark. The same bookmark may only refer exectly one item"
)
Interpretation.register(
	"COMMENT",
	u"http://www.semanticdesktop.org/ontologies/2007/01/19/nie/#comment",
	display_name=_("Comments"),
	doc="User provided comment"
)
Interpretation.register(
	"DOCUMENT",
	u"http://www.semanticdesktop.org/ontologies/2007/03/22/nfo/#Document",
	display_name=_("Documents"),
	doc="A document, presentation, spreadsheet, or other content centric item"
)
Interpretation.register(
	"SOURCECODE",
	u"http://www.semanticdesktop.org/ontologies/2007/03/22/nfo/#ManifestationCode",
	display_name=_("Manifestation Code"),
	doc="Code in a compilable or interpreted programming language."
)
Interpretation.register(
	"IMAGE",
	u"http://www.semanticdesktop.org/ontologies/2007/03/22/nfo/#Image",
	display_name=_("Images"),
	doc="A photography, painting, or other digital image"
)
Interpretation.register(
	"VIDEO",
	u"http://www.semanticdesktop.org/ontologies/2007/03/22/nfo/#Video",
	display_name=_("Videos"),
	doc="Any form of digital video, streaming and non-streaming alike"
)
Interpretation.register(
	"MUSIC",
	u"http://www.semanticdesktop.org/ontologies/2007/03/22/nfo/#Audio",
	display_name=_("Music"),
	doc="Digital music or other creative audio work"
)
Interpretation.register(
	"EMAIL",
	u"http://www.semanticdesktop.org/ontologies/2007/03/22/nmo/#Email",
	display_name=_("Email"),
	doc="An email is an email is an email"
)
Interpretation.register(
	"IM_MESSAGE",
	u"http://www.semanticdesktop.org/ontologies/2007/03/22/nmo/#IMMessage",
	display_name=_("Messages"),
	doc="A message received from an instant messaging service"
)
Interpretation.register(
	"FEED_MESSAGE",
		u"http://www.tracker-project.org/temp/mfo#FeedMessage",
	display_name=_("Feeds"),
	doc="Any syndicated item, RSS, Atom, or other"
)
Interpretation.register(
	"BROADCAST_MESSAGE",
	u"http://zeitgeist-project.com/schema/1.0/core#BroadcastMessage",
	display_name=_("Broadcasts"), # FIXME: better display name
	doc="Small broadcasted message, like Twitter/Identica micro blogging (TBD in tracker)"
)
Interpretation.register(
	"CREATE_EVENT",
	u"http://zeitgeist-project.com/schema/1.0/core#CreateEvent",
	display_name=_("Created"),
	doc="Event type triggered when an item is created"
)
Interpretation.register(
	"MODIFY_EVENT",
	u"http://zeitgeist-project.com/schema/1.0/core#ModifyEvent",
	display_name=_("Modified"),
	doc="Event type triggered when an item is modified"
)
Interpretation.register(
	"VISIT_EVENT",
	u"http://zeitgeist-project.com/schema/1.0/core#VisitEvent",
	display_name=_("Visited"),
	doc="Event type triggered when an item is visited or opened"
)
Interpretation.register(
	"OPEN_EVENT",
	u"http://zeitgeist-project.com/schema/1.0/core#OpenEvent",
	display_name=_("Opened"),
	doc="Event type triggered when an item is visited or opened"
)
Interpretation.register(
	"SAVE_EVENT",
	u"http://zeitgeist-project.com/schema/1.0/core#SaveEvent",
	display_name=_("Saved"),
	doc="Event type triggered when an item is saved"
)
Interpretation.register(
	"CLOSE_EVENT",
	u"http://zeitgeist-project.com/schema/1.0/core#CloseEvent",
	display_name=_("Closed"),
	doc="Event type triggered when an item is closed"
)
Interpretation.register(
	"SEND_EVENT",
	u"http://zeitgeist-project.com/schema/1.0/core#SendEvent",
	display_name=_("Send"),
	doc="Event type triggered when the user sends/emails an item or message to a remote host"
)
Interpretation.register(
	"RECEIVE_EVENT",
	u"http://zeitgeist-project.com/schema/1.0/core#ReceiveEvent",
	display_name=_("Received"),
	doc="Event type triggered when the user has received an item from a remote host"
)
Interpretation.register(
	"FOCUS_EVENT",
	u"http://zeitgeist-project.com/schema/1.0/core#FocusEvent",
	display_name=_("Focused"),
	doc="Event type triggered when the user has switched focus to a new item"
)
Interpretation.register(
	"WARN_EVENT",
	u"http://zeitgeist-project.com/schema/1.0/core#WarnEvent",
	display_name=_("Warnings"),
	doc="Event type triggered when the user is warned about something"
)
Interpretation.register(
	"ERROR_EVENT",
	"http://zeitgeist-project.com/schema/1.0/core#ErrorEvent",
	display_name=_("Errors"),
	doc="Event type triggered when the user has encountered an error"
)
Interpretation.register(
	"APPLICATION",
		u"http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#Application",
	display_name=_("Applications"),
	doc="An item that is a launchable application. The item's URI must point to the relevant .desktop file"
)
Interpretation.register(
	"UNKNOWN",
	u"http://zeitgeist-project.com/schema/1.0/core#UnknownInterpretation",
	display_name=_("Unknown"),
	doc="An entity with an unknown interpretation"
)

#
# Manifestation categories
#
Manifestation.register(
	"WEB_HISTORY",
		u"http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#WebHistory",
	display_name=_("Web History"),
	doc="An item that has been extracted from the user's browsing history"
)
Manifestation.register(
	"USER_ACTIVITY",
	u"http://zeitgeist-project.com/schema/1.0/core#UserActivity",
	display_name=_("Activities"),
	doc="An item that has been created solely on the basis of user actions and is not otherwise stored in some physical location"
)
Manifestation.register(
	"HEURISTIC_ACTIVITY",
	u"http://zeitgeist-project.com/schema/1.0/core#HeuristicActivity",
	display_name=_("Activities"),
	doc="An application has calculated via heuristics that some relationship is very probable."
)
Manifestation.register(
	"SCHEDULED_ACTIVITY",
	u"http://zeitgeist-project.com/schema/1.0/core#ScheduledActivity",
	display_name=_("Activities"), # FIXME: Is this a bad name?
	doc="An event that has been triggered by some long running task activated by the user. Fx. playing a song from a playlist"
)
Manifestation.register(
	"USER_NOTIFICATION",
	u"http://zeitgeist-project.com/schema/1.0/core#UserNotification",
	display_name=_("Notifications"),
	doc="An item that has been send as a notification to the user"
)
Manifestation.register(
	"FILE",
	u"http://www.semanticdesktop.org/ontologies/nfo/#FileDataObject",
	display_name=_("Files"),
	doc="An item stored on the local filesystem"
)
Manifestation.register(
	"SYSTEM_RESOURCE",
	u"http://freedesktop.org/standards/xesam/1.0/core#SystemRessource",
	display_name=_("System Resources"),
	doc="An item available through the host operating system, such as an installed application or manual page (TBD in tracker)"
)
Manifestation.register(
	"UNKNOWN",
	u"http://zeitgeist-project.com/schema/1.0/core#UnknownManifestation",
	display_name=_("Unknown"),
	doc="An entity with an unknown manifestation"
)

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
		#print "T: %s" % self
		#print "E: %s" % event
		#print "------------"
		return event.matches_template(self)
	
	def in_time_range (self, time_range):
		"""
		Check if the event timestamp lies within a :class:`TimeRange`
		"""
		t = int(self.timestamp) # The timestamp may be stored as a string
		return (t >= time_range.begin) and (t <= time_range.end)
	
	def _special_str(self, obj):
		""" Return a string representation of obj
		If obj is None, return an empty string.
		"""
		return unicode(obj) if obj is not None else ""

	def _make_dbus_sendable(self):
		"""
		Ensure that all fields in the event struct are non-None
		"""
		for n, value in enumerate(self[0]):
			self[0][n] = self._special_str(value)
		for subject in self[1]:
			for n, value in enumerate(subject):
				subject[n] = self._special_str(value)
		# The payload require special handling, since it is binary data
		# If there is indeed data here, we must not unicode encode it!
		if self[2] is None: self[2] = u""

class Datasource(list):
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
	Fields = (Name,
		Description,
		Actors,
		Running,
		LastSeen,
		Enabled) = range(6)
	
	def __init__(self, name, description, actors, running=True, last_seen=None,
		enabled=True):
		super(Datasource, self).__init__()
		self.append(unicode(name))
		self.append(unicode(description))
		self.append([unicode(actor) for actor in actors])
		self.append(bool(running))
		self.append(int(last_seen) if last_seen else time.time() * 1000)
		self.append(bool(enabled))
	
	def __eq__(self, source):
		return self[self.Name] == source[self.Name]

NULL_EVENT = ([], [], [])
"""Minimal Event representation, a tuple containing three empty lists.
This `NULL_EVENT` is used by the API to indicate a queried but not
available (not found or blocked) Event.
"""
