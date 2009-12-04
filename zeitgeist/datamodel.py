# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
# Copyright © 2009 Markus Korn <thekorn@gmx.de>
# Copyright © 2009 Seif Lotfy <seif@lotfy.com>
# Copyright © 2009 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
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
gettext.install("zeitgeist")

class Symbol(str):
	
	"""Immutable string-like object representing a Symbol
	Zeitgeist uses Categories when defining Manifestations and 
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
		return self.__doc
		
	__doc__ = doc


class SymbolCollection(dict):
	
	def __init__(self, name):
		super(SymbolCollection, self).__init__()
		self.__name = name
	
	def register(self, name, uri, display_name, doc):
		if name in self:
			raise ValueError("cannot register symbol %r, a definition for this symbol already exists" %name)
		if not name.isupper():
			raise ValueError("cannot register %r, name must be uppercase" %name)
		self[name] = Symbol(self.__name, name, uri, display_name, doc)
		
	def __getattr__(self, name):
		if not name.isupper():
			# symbols must be uppercase
			raise AttributeError("'%s' has no attribute '%s'" %(self.__name, name))
		try:
			return self[name]
		except KeyError:
			# this symbol is not registered yet, create
			# it on the fly
			self[name] = Symbol(self.__name, name)
			return self[name]


Interpretation = SymbolCollection("Interpretation")
Manifestation = SymbolCollection("Manifestation")

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
        u"http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#SoftwareApplication",
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
	def __init__ (self, begin, end):
		super(TimeRange, self).__init__((begin, end))
	
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
	
	@staticmethod
	def until_now():
		"""
		Return a TimeRange from 0 to the instant of invocation
		"""
		return TimeRange(0, int(time.time()*1000))

class StorageState:
	"""
	Enumeration class defining the possible values for the storage state
	of an event subject.
	
	The StorageState enumeration can be used to control whether or not matched
	events must have their subjects available to the user. Fx. not including
	deleted files, files on unplugged USB drives, files available only when
	a network is available etc.
	
	This class has the following members:
	
	 * **0** - *NotAvailable*
	     The storage medium of the events subjects must not be available to the user
 	
	 * **1** - *Available*
	     The storage medium of all event subjects must be immediately available to the user
 
	 * **2** - *Any*
	     The event subjects may or may not be available
	"""
	(NotAvailable, Available, Any) = range(3)

class ResultType:
	"""
	An enumeration class used to define how query results should be returned
	from the Zeitgeist engine.
	
	This class has the following members:
	
	 * **0** - *MostRecentEvents*
	     All events with the most recent events first
	 * **1** - *LeastRecentEvents*
	     All events with the oldest ones first
	 * **2** - *MostRecentSubjects*
	     One event for each subject only, ordered with the most recent events first
	 * **3** - *LeastRecentSubjects*
	     One event for each subject only, ordered with oldest events first
	 * **4** - *MostPopularSubjects*
	     One event for each subject only, ordered by the popularity of the subject
	 * **5** - *LeastPopularSubjects*
	     One event for each subject only, ordered ascendently by popularity
	"""
	(MostRecentEvents,
	LeastRecentEvents,
	MostRecentSubjects,
	LeastRecentSubjects,
	MostPopularSubjects,
	LeastPopularSubjects) = range(6)

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
		:param storage: String identifier for the storage medium of the subject. This should be the UUID of the disk partition or the string *inet* for general resources on the internet or other items requiring connectivity.
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
	doc="Read/write property with a string id of the storage medium where the subject is stored. Fx. the UUID of the disk partition or just the string *inet* for items requiring general connectivity to be available")
	
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
	marshalled with the signature a(asaasay).
	
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
		if not self[0][Event.Timestamp] :
			self[0][Event.Timestamp] = str(int(time.time() * 1000))
		
	@staticmethod
	def new_for_data(event_data):
		"""
		Create a new Event setting event_data as the backing array
		behind the event metadata. The contents of the array must
		contain the event metadata at the positions defined by the
		Event.Fields enumeration.
		"""
		self = Event()
		if len(event_data) != len(Event.Fields):
			raise ValueError("event_data must have %s members, found %s" % \
				(len(Event.Fields), len(event_data)))
		self[0] = event_data
		return self
	
	@staticmethod
	def new_for_values (**values):
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
		self = Event()
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
	
	def _dict_contains_subject_keys (self, dikt):
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
		return self[0][Event.Id]
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
	doc="Read/write property defining the application or entity responsible for emitting the event. Applications should us the filename of their .desktop file without the .desktop extension as their identifiers. Eg. *gedit*, *firefox*, etc.") 
	
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
