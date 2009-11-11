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

import gettext
gettext.install("zeitgeist")

class DictCache(type):
	""" Metaclass which has a _CACHE attribute. Each subclass has its own, fresh cache """
	
	def __init__(cls, name, bases, d):
		super(DictCache, cls).__init__(name, bases, d)
		cls.__CACHE = {}
	
	def _new_cache(cls, cache=None):
		if cache is None:
			cls.__CACHE.clear()
		else:
			cls.__CACHE = cache
		
	def _clear_cache(self):
		return self._new_cache()
		
	@property
	def _CACHE(cls):
		return cls.__CACHE


class Symbol(DictCache):
	
	def __init__(cls, name, bases, d):
		super(Symbol, cls).__init__(name, bases, d)
		if not cls._CACHE and issubclass(cls, Symbol):
			assert len(bases) == 1, "Multi-inheritance is not supported yet"
			cls._new_cache(bases[0]._CACHE)
			cls._attributes = bases[0]._ATTRIBUTES
			cls._database_cls = bases[0]._DATABASE_CLS
			cls._base = bases[0]
		else:
			cls._attributes = {}
			cls._database_cls = None
			cls._base = None
			
	def _clear_cache(cls):
		""" resets the cache of this Symbol. If the Symbol is bound to a
		database also reset the cache of this database object.
		"""
		super(Symbol, cls)._clear_cache()
		if cls._DATABASE_CLS is not None:
			cls._DATABASE_CLS._clear_cache()		
			
	@property
	def _ATTRIBUTES(cls):
		return cls._attributes
		
	@property
	def _DATABASE_CLS(cls):
		return cls._database_cls
		
	def __repr__(cls):
		return "<%s %r>" %(cls.__class__.__name__, cls.__name__)
		
	def __getattr__(cls, name):
		try:
			return cls._ATTRIBUTES[name]
		except KeyError:
			if cls._DATABASE_CLS is not None:
				try:
					return getattr(cls._DATABASE_CLS, name)
				except AttributeError:
					# ignore this error, raise the following AttributeError instead
					pass
		raise AttributeError("Object %r has no attribute %r" %(cls.__name__, name))
		
	def __call__(cls, *args, **kwargs):
		uri = kwargs.get("uri", args[0] if args else None)
		if uri and uri in cls._CACHE:
			return cls._CACHE[uri]
		return cls._CACHE.setdefault(uri, super(Symbol, cls).__call__(*args, **kwargs))
	
	def get(cls, uri):
		return cls._CACHE.setdefault(uri, cls(uri))
	
	def register(cls, name, uri, display_name=None, doc=None):
		if uri in cls._CACHE:
			raise ValueError("There has already been an %s object registered for %r" %(cls.__name__, uri))
		if name in cls._ATTRIBUTES:
			raise ValueError(
				("Can't register %(name)s object for %(uri)r, %(name)s "
				 "has already an attribute called %(attribute)r")
				%({"name": cls.__name__, "uri": uri, "attribute": name})
			)
		obj = cls(uri=uri, display_name=display_name, doc=doc)
		cls._CACHE[uri] = cls._ATTRIBUTES[str(name)] = obj
	
	def needs_lookup(cls, uri):
		try:
			return not (uri in cls._DATABASE_CLS._CACHE)
		except AttributeError:
			# the database class does not have a _CACHE
			# to stay safe, return True
			return True
		
	def bind_database(cls, database_cls):
		""" Binds the symbol to a database class object. This class must
		have a lookup_or_create() classmethod. This classmethod takes
		an uri as argument and returns the database object for this uri.
		The resulting object should be cached in an attribute called _CACHE
		"""
		if not hasattr(database_cls, "lookup_or_create"):
			raise TypeError
		cls._database_cls = database_cls
		if cls._base is not None:
			cls._base.bind_database(database_cls)


class Category(object):
	__metaclass__ = Symbol
	
	def __init__(self, uri, display_name=None, name=None, doc=None):
		if self.__class__ is Category:
			raise ValueError("Category is an abstract class")
		self._uri = uri
		self._display_name = display_name
		self.__doc__ = doc
		self._name = name
		self._database_obj = None
	
	def __repr__(self):
		return "<%s %r>" %(self.__class__.__name__, self.uri)
	
	def __str__(self):
		return self.uri
	
	def __unicode__(self):
		return unicode(self.uri)
		
	def __eq__(self, other):
		# Fixme
		# but in first approximation
		# two symbols with the same string presentation are the same
		return str(self) == str(other)
	
	@property
	def uri(self):
		return self._uri
	
	@property
	def display_name(self):
		return self._display_name or u""
	
	@property
	def name(self):
		if self._name is not None:
			return self._name
		else:
			return self.uri.split("#", 1).pop()
	
	@property
	def doc(self):
		return self.__doc__
	
	def __getattr__(self, name):
		if self._database_obj is not None and not self.__class__.needs_lookup(self.uri):
			return getattr(self._database_obj, name)
		if self.__class__._DATABASE_CLS is None:
			raise RuntimeError("Cannot get %r, object is not bound to a database" % name)
		self._database_obj = self.__class__._DATABASE_CLS.lookup_or_create(self.uri)
		return getattr(self._database_obj, name)


class Content(Category):
	pass
	

class Mimetype(Category):
	pass

	
class Source(Category):
	pass

#
# Content categories
#
Content.register(
	"TAG",
        u"http://www.semanticdesktop.org/ontologies/2007/08/15/nao#Tag",
	display_name=_("Tags"),
	doc="User provided tags. The same tag may refer multiple items"
)
Content.register(
	"BOOKMARK",
	u"http://www.semanticdesktop.org/ontologies/nfo/#Bookmark",
	display_name=_("Bookmarks"),
	doc="A user defined bookmark. The same bookmark may only refer exectly one item"
)
Content.register(
	"COMMENT",
	u"http://www.semanticdesktop.org/ontologies/2007/01/19/nie/#comment",
	display_name=_("Comments"),
	doc="User provided comment"
)
Content.register(
	"DOCUMENT",
	u"http://www.semanticdesktop.org/ontologies/2007/03/22/nfo/#Document",
	display_name=_("Documents"),
	doc="A document, presentation, spreadsheet, or other content centric item"
)
Content.register(
	"SOURCECODE",
	u"http://www.semanticdesktop.org/ontologies/2007/03/22/nfo/#SourceCode",
	display_name=_("Source Code"),
	doc="Code in a compilable or interpreted programming language."
)
Content.register(
	"IMAGE",
	u"http://www.semanticdesktop.org/ontologies/2007/03/22/nfo/#Image",
	display_name=_("Images"),
	doc="A photography, painting, or other digital image"
)
Content.register(
	"VIDEO",
	u"http://www.semanticdesktop.org/ontologies/2007/03/22/nfo/#Video",
	display_name=_("Videos"),
	doc="Any form of digital video, streaming and non-streaming alike"
)
Content.register(
	"MUSIC",
	u"http://www.semanticdesktop.org/ontologies/2007/03/22/nfo/#Audio",
	display_name=_("Music"),
	doc="Digital music or other creative audio work"
)
Content.register(
	"EMAIL",
	u"http://www.semanticdesktop.org/ontologies/2007/03/22/nmo/#Email",
	display_name=_("Email"),
	doc="An email is an email is an email"
)
Content.register(
	"IM_MESSAGE",
	u"http://www.semanticdesktop.org/ontologies/2007/03/22/nmo/#IMMessage",
	display_name=_("Messages"),
	doc="A message received from an instant messaging service"
)
Content.register(
	"RSS_MESSAGE",
        u"http://www.tracker-project.org/temp/mfo#FeedMessage",
	display_name=_("Feeds"),
	doc="Any syndicated item, RSS, Atom, or other"
)
Content.register(
	"BROADCAST_MESSAGE",
	u"http://zeitgeist-project.com/schema/1.0/core#BroadcastMessage",
	display_name=_("Broadcasts"), # FIXME: better display name
	doc="Small broadcasted message, like Twitter/Identica micro blogging (TBD in tracker)"
)
Content.register(
	"CREATE_EVENT",
	u"http://zeitgeist-project.com/schema/1.0/core#CreateEvent",
	display_name=_("Created"),
	doc="Event type triggered when an item is created"
)
Content.register(
	"MODIFY_EVENT",
	u"http://zeitgeist-project.com/schema/1.0/core#ModifyEvent",
	display_name=_("Modified"),
	doc="Event type triggered when an item is modified"
)
Content.register(
	"VISIT_EVENT",
	u"http://zeitgeist-project.com/schema/1.0/core#VisitEvent",
	display_name=_("Visited"),
	doc="Event type triggered when an item is visited or opened"
)
Content.register(
	"SEND_EVENT",
	u"http://zeitgeist-project.com/schema/1.0/core#SendEvent",
	display_name=_("Send"),
	doc="Event type triggered when the user sends/emails an item or message to a remote host"
)
Content.register(
	"RECEIVE_EVENT",
	u"http://zeitgeist-project.com/schema/1.0/core#ReceiveEvent",
	display_name=_("Received"),
	doc="Event type triggered when the user has received an item from a remote host"
)
Content.register(
	"FOCUS_EVENT",
	u"http://zeitgeist-project.com/schema/1.0/core#FocusEvent",
	display_name=_("Focused"),
	doc="Event type triggered when the user has switched focus to a new item"
)
Content.register(
	"WARN_EVENT",
	u"http://zeitgeist-project.com/schema/1.0/core#WarnEvent",
	display_name=_("Warnings"),
	doc="Event type triggered when the user is warned about something"
)
Content.register(
	"ERROR_EVENT",
	"http://zeitgeist-project.com/schema/1.0/core#ErrorEvent",
	display_name=_("Errors"),
	doc="Event type triggered when the user has encountered an error"
)
Content.register(
	"APPLICATION",
        u"http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#SoftwareApplication",
	display_name=_("Applications"),
	doc="An item that is a launchable application. The item's URI must point to the relevant .desktop file"
)

#
# Source categories
#
Source.register(
	"WEB_HISTORY",
        u"http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#WebHistory",
	display_name=_("Web History"),
	doc="An item that has been extracted from the user's browsing history"
)
Source.register(
	"USER_ACTIVITY",
	u"http://zeitgeist-project.com/schema/1.0/core#UserActivity",
	display_name=_("Activities"),
	doc="An item that has been created solely on the basis of user actions and is not otherwise stored in some physical location"
)
Source.register(
	"HEURISTIC_ACTIVITY",
	u"http://zeitgeist-project.com/schema/1.0/core#HeuristicActivity",
	display_name=_("Activities"),
	doc="An application has calculated via heuristics that some relationship is very probable."
)
Source.register(
	"USER_NOTIFICATION",
	u"http://zeitgeist-project.com/schema/1.0/core#UserNotification",
	display_name=_("Notifications"),
	doc="An item that has been send as a notification to the user"
)
Source.register(
	"FILE",
	u"http://www.semanticdesktop.org/ontologies/nfo/#FileDataObject",
	display_name=_("Files"),
	doc="An item stored on the local filesystem"
)
Source.register(
	"SYSTEM_RESOURCE",
	u"http://freedesktop.org/standards/xesam/1.0/core#SystemRessource",
	display_name=_("System Resources"),
	doc="An item available through the host operating system, such as an installed application or manual page (TBD in tracker)"
)


class Subject(list):
	Fields = (Uri,
		Interpretation,
		Manifestation,
		Origin,
		Mimetype,
		Text,
		Storage) = range(7)
	
	def __init__(self, **values):
		super(Subject, self).__init__()
		self.extend(([None]* len(Subject.Fields), [], None))
		for key, value in values.iteritems():
			print key
			setattr(self, key, value)
		
	def __repr__(self):
		return "%s(%s)" %(
			self.__class__.__name__, super(Subject, self).__repr__()
		)
		
	def get_uri(self):
		return self[Subject.Uri]
		
	def set_uri(self, value):
		self[Subject.Uri] = value
	uri = property(get_uri, set_uri)
		
	def get_interpretation(self):
		return self[Subject.Interpretation]
		
	def set_interpretation(self, value):
		self[Subject.Interpretation] = value
	interpretation = property(get_interpretation, set_interpretation) 
		
	def get_manifestation(self):
		return self[Subject.Manifestation]
		
	def set_manifestation(self, value):
		self[Subject.Manifestation] = value
	manifestation = property(get_manifestation, set_manifestation)
		
	def get_origin(self):
		return self[Subject.Origin]
		
	def set_origin(self, value):
		self[Subject.Origin] = value
	origin = property(get_origin, set_origin) 
		
	def get_mimetype(self):
		return self[Subject.Mimetype]
		
	def set_mimetype(self, value):
		self[Subject.Mimetype] = value
	mimetype = property(get_mimetype, set_mimetype) 
		
	def get_text(self):
		return self[Subject.Text]
		
	def set_text(self, value):
		self[Subject.Text] = value
	text = property(get_text, set_text) 
		
	def get_storage(self):
		return self[Subject.Storage]
		
	def set_storage(self, value):
		self[Subject.storage] = value
	storage = property(get_storage, set_storage)
	
	
class Event(list):
	Fields = (Id,
		Timestamp,
		Interpretation,
		Manifestation,
		Actor) = range(5)
	
	def __init__(self, **values):
		super(Event, self).__init__()
		self.extend(([None]* len(Event.Fields), [], None))
		for key, value in values.iteritems():
			print key
			setattr(self, key, value)
		
	def __repr__(self):
		return "%s(%s)" %(
			self.__class__.__name__, super(Event, self).__repr__()
		)
	
	def append_subject(self, subject=None):
		"""
		Append a new empty subject array and return a reference to
		the array.
		"""
		if not subject:
			subject = Subject()
		self.subject.append(subject)
		return subject
		
	@property
	def id(self):
		return self[0][Event.Id]
		
	def get_timestamp(self):
		return self[0][Event.Timestamp]
		
	def set_timestamp(self, value):
		self[0][Event.Timestamp] = value
	timestamp = property(get_timestamp, set_timestamp)
		
	def get_interpretation(self):
		return self[0][Event.Interpretation]
		
	def set_interpretation(self, value):
		self[0][Event.Interpretation] = value
	interpretation = property(get_interpretation, set_interpretation) 
		
	def get_manifestation(self):
		return self[0][Event.Manifestation]
		
	def set_manifestation(self, value):
		self[0][Event.Manifestation] = value
	manifestation = property(get_manifestation, set_manifestation)
		
	def get_actor(self):
		return self[0][Event.Actor]
		
	def set_actor(self, value):
		self[0][Event.Actor] = value
	actor = property(get_actor, set_actor) 
		
	def get_payload(self):
		return self[2]
		
	def set_payload(self, value):
		self[2] = value
	payload = property(get_payload, set_payload)
