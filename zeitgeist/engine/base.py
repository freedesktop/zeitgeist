# -.- encoding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Seif Lotfy <seif@lotfy.com>
# Copyright © 2009 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
from storm.locals import *

class Symbol:
	""" A simple structure to hold a URI and a short label and magically
		cache and entity (integer) id.
		Used in Source and Content for pre-defined types. """
	
	def __init__ (self, entity_class, uri):
		self.value = uri
		self.name = uri.split("#")[1]
		self._entity_class = entity_class
		self._id = None
	
	def __str__ (self):
		return self.value
	
	def __getattr__ (self, name):
		""" This small piece of magic make self.id resolve to the actual
		   integer id of the entity class. """
		if name == "id":
			if not self._id :
				ent = self._entity_class.lookup_or_create(self.value)
				ent.resolve()
				self._id = ent.id
			return self._id
		else:
			raise AttributeError("Unknown attribute %s" % name)

class Entity(object):
	""" Generic base class for anything that has an 'id' and a 'value'.
		It is assumed that there is a unique index on the value column
	"""
	
	id = Int(allow_none=False)
	value = Unicode()
	
	def __init__ (self, value):
		"""Create an Entity in the store. Any created entity will automatically
		   be added to the store (but the store still need flushing) before an
		   id is assigned to the entity"""
		if value is None :
			raise ValueError("Can not create Entity with value None")
		
		self.value = unicode(value) # A no-op if value is already a unicode	
		_store.add(self)
	
	def resolve (self):
		"""Make sure that the id property of this object has been resolved.
			If the entity already has an id, this method is a no-op"""
		if not self.id:
			_store.flush()
		assert self.id
	
	@classmethod
	def lookup(klass, value=None, id=None):
		"""Look up an entity by value or id, return None if the
		   entity is not known"""
		global _store
		if value:
			value = unicode(value)
			return _store.find(klass, klass.value == value).one()
		elif id:
			return _store.find(klass, klass.id == id).one()
		else:
			raise ValueError("Looking up Entity without a value or id")
	
	@classmethod
	def lookup_or_create(klass, value):
		ent = klass.lookup(value)		
		return ent if ent else klass(value)

class Content(Entity):
	__storm_table__= "content"
	__storm_primary__= "id"
	
	def __init__ (self, value):				
		super(Content, self).__init__(value)		

class Source(Entity):
	__storm_table__= "source"
	__storm_primary__= "id"		
	
	def __init__ (self, value):				
		super(Source, self).__init__(value)


# Content and source symbols are created outside the classes because we can not
# refer to, fx. the Content class, from within the Content class scope
#
# When we add more Content types here, we should strive to take them from
# http://xesam.org/main/XesamOntology100 when possible

Content.TAG = Symbol(Content, "http://freedesktop.org/standards/xesam/1.0/core#Tag")
Content.BOOKMARK = Symbol(Content, "http://freedesktop.org/standards/xesam/1.0/core#Bookmark")
Content.COMMENT = Symbol(Content, "http://gnome.org/zeitgeist/schema/1.0/core#Comment")
Content.DOCUMENT = Symbol(Content, "http://freedesktop.org/standards/xesam/1.0/core#Document")
Content.CREATE_EVENT = Symbol(Content, "http://gnome.org/zeitgeist/schema/1.0/core#CreateEvent")
Content.MODIFY_EVENT = Symbol(Content, "http://gnome.org/zeitgeist/schema/1.0/core#ModifyEvent")
Content.VISIT_EVENT = Symbol(Content, "http://gnome.org/zeitgeist/schema/1.0/core#VisitEvent")
Content.LINK_EVENT = Symbol(Content, "http://gnome.org/zeitgeist/schema/1.0/core#LinkEvent")
Content.SEND_EVENT = Symbol(Content, "http://gnome.org/zeitgeist/schema/1.0/core#SendEvent")
Content.RECEIVE_EVENT = Symbol(Content, "http://gnome.org/zeitgeist/schema/1.0/core#ReceiveEvent")
Content.WARN_EVENT = Symbol(Content, "http://gnome.org/zeitgeist/schema/1.0/core#WarnEvent")
Content.ERROR_EVENT = Symbol(Content, "http://gnome.org/zeitgeist/schema/1.0/core#ErrorEvent")
Source.WEB_HISTORY = Symbol(Source, "http://gnome.org/zeitgeist/schema/1.0/core#WebHistory")
Source.USER_ACTIVITY = Symbol(Source, "http://gnome.org/zeitgeist/schema/1.0/core#UserActivity")
Source.USER_NOTIFICATION = Symbol(Source, "http://gnome.org/zeitgeist/schema/1.0/core#UserNotification")
Source.APPLICATION = Symbol(Source, "http://gnome.org/zeitgeist/schema/1.0/core#Application")

class URI(Entity):
	__storm_table__= "uri"
	__storm_primary__= "id"
	
	def __init__ (self, value):				
		super(URI, self).__init__(value)

class Item(object):
	__storm_table__ = "item"
	
	id = Int(primary=True, allow_none=False)
	uri = Reference(id, URI.id)
	
	content_id = Int()
	content = Reference(content_id, Content.id)
	
	source_id = Int()
	source = Reference(source_id, Source.id)
	
	origin = Unicode()
	text = Unicode()
	mimetype = Unicode()
	icon = Unicode()
	payload = RawStr() # Storm lingo for BLOB/BYTEA

	def __init__ (self, uri):
		"""Create an item on a given URI and add it to the store.
		   The 'uri' argument may be a 'str', 'unicode' or 'URI' instance"""
		super(Item, self).__init__()
		if isinstance(uri, (str, unicode)):
			uri = URI.lookup_or_create(uri)
			uri.resolve()
			self.uri = uri			
			self.id = self.uri.id
			assert self.id is not None			
		elif isinstance(uri, URI):
			uri.resolve()
			self.uri = uri
			self.id = uri.id
		else:
			raise TypeError("Expected 'str', 'unicode', or 'URI', got %s" % type(uri))
		
		_store.add(self) # All good, add us to the store
	
	@classmethod
	def lookup(klass, uri):
		global _store
		if isinstance(uri, str) or isinstance(uri,unicode):
			uri = unicode(uri)
			return _store.find(Item,
							Item.id == URI.id,
							URI.value == uri).one()
		elif isinstance(uri, URI):
			return _store.find(Item, Item.id == uri.id).one()
	
	@classmethod
	def lookup_or_create(klass, uri):
		item = klass.lookup(uri)
		if item : return item
		return klass(uri)


# Storm does not handle multi-table classes. The following design pattern is
# a simplifaction of Infoheritance described here:
# https://storm.canonical.com/Infoheritance

class ProxyItem(object):
	
	# Don't declare primary key here, because Annotation needs a compound key
	item_id = Int(allow_none=False)
	item = Reference(item_id, Item.id)
	uri = Reference(item_id, URI.id)
	
	def __init__ (self, uri):
		""" Create a ProxyItem with a given URI. If the URI is not
			already registered it will be soon. The 'uri' argument
			may be a 'str', 'unicode', or 'URI' instance. """
		
		super(ProxyItem, self).__init__()
		
		# The Item constructor will register the URI if needed
		self.item = Item(uri)
		self.uri_id = self.item.uri.id
		self.uri = self.item.uri
	
	@classmethod
	def lookup(self, uri):
		global _store
		if isinstance(uri, str) or isinstance(uri, unicode):
			uri = unicode(uri)
			return _store.find(self, self.item_id == URI.id, URI.value == uri).one()
		elif isinstance(uri, URI):
			return _store.find(self, self.item_id == uri.id).one()
	
	@classmethod
	def lookup_or_create(self, uri):
		proxy = self.lookup(uri)
		return proxy if proxy else self(uri)

class App(ProxyItem):
	__storm_table__= "app"
	__storm_primary__ = "item_id"
	info = Unicode()
	
	def __init__ (self, uri):
		super(App,self).__init__(uri)
		# FIXME: Somehow parse the application name out of the .desktop file
		_store.add(self)

class ReferencingProxyItem(ProxyItem):
	"""Base class for items which point to a subject URI. The primary subclasses
	   are Annotation and Event"""
	
	subject_id = Int()
	subject = Reference(subject_id, Item.id)
	
	def __init__ (self, uri, subject=None):
		"""Create a new ReferencingProxyItem. The 'subject' argument
		   may be a 'str', 'unicode', 'URI', 'Item', or 'ProxyItem'"""
		super(ReferencingProxyItem,self).__init__(uri)
		
		# Resolve the subject_id from a uri string or URI object
		if isinstance(subject, str) or isinstance(subject, unicode):
			uri = URI.lookup_or_create(subject)
			uri.resolve()
			self.subject_id = uri.id
		elif isinstance(subject, URI):
			subject.resolve()				
			self.subject_id = subject.id
		elif isinstance(subject, Item):
			self.subject_id = subject.uri.id
		elif isinstance(subject, ProxyItem):
			self.subject_id = subject.item.uri.id
		elif subject is None:
			pass
		else:
			raise TypeError("Expected 'str', 'unicode', 'URI', 'Item', "
							"or 'ProxyItem', got %s" % type(subject))

class Annotation(ReferencingProxyItem):
	# We use a compound primary key because the same annotation can point to
	# several subjects, so that only the (id,subject_id) pair is unique
	__storm_table__= "annotation"
	__storm_primary__ = "item_id", "subject_id"	   
	
	def __init__ (self, uri, subject=None):
		"""Create a new annotation and add it to the store. The 'subject'
		   argument may be a 'str', 'unicode', 'URI', 'Item', or 'ProxyItem'
		   and points at the object being the subject of the annotations"""
		super(Annotation,self).__init__(uri, subject)
		_store.add(self)

class Event(ReferencingProxyItem):
	__storm_table__= "event"
	__storm_primary__ = "item_id"
	
	start = Int()
	end = Int()
	app_id = Int()
	app = Reference(app_id, App.item_id)
	
	def __init__ (self, uri, subject=None):
		"""Create a new annotation and add it to the _store. The 'subject'
		   argument may be a 'str', 'unicode', 'URI', 'Item', or 'ProxyItem'
		   and points at the object being the subject of the annotations"""
		super(Event,self).__init__(uri, subject)
		_store.add(self)	

def create_store(storm_url):
	print "Creating database... %s" % storm_url
	db = create_database(storm_url)
	store = Store(db)
	store.execute("""
		CREATE TABLE IF NOT EXISTS content
			(id INTEGER PRIMARY KEY, value VARCHAR UNIQUE)
		""")
	store.execute("""
		CREATE UNIQUE INDEX IF NOT EXISTS content_value
			ON content(value)
		""")
	store.execute("""
		CREATE TABLE IF NOT EXISTS source
			(id INTEGER PRIMARY KEY, value VARCHAR UNIQUE)
		""")
	store.execute("""
		CREATE UNIQUE INDEX IF NOT EXISTS source_value
			ON source(value)""")
	store.execute("""
		CREATE TABLE IF NOT EXISTS uri
			(id INTEGER PRIMARY KEY, value VARCHAR UNIQUE)
		""")
	store.execute("""
		CREATE UNIQUE INDEX IF NOT EXISTS uri_value ON uri(value)
		""")
	store.execute("""
		CREATE TABLE IF NOT EXISTS item
			(id INTEGER PRIMARY KEY, content_id INTEGER,
				source_id INTEGER, origin VARCHAR, text VARCHAR,
				mimetype VARCHAR, icon VARCHAR, payload BLOB)
		""")
	# FIXME: Consider which indexes we need on the item table
	store.execute("""
		CREATE TABLE IF NOT EXISTS app
			(item_id INTEGER PRIMARY KEY, info VARCHAR)
		""")
	store.execute("""
		CREATE UNIQUE INDEX IF NOT EXISTS app_value ON app(info)
		""")
	store.execute("""
		CREATE TABLE IF NOT EXISTS annotation
			(item_id INTEGER, subject_id INTEGER)
		""")
	store.execute("""
		CREATE UNIQUE INDEX IF NOT EXISTS
			annotation_link ON annotation(item_id, subject_id)
		""")
	store.execute("""
	CREATE TABLE IF NOT EXISTS event 
		(item_id INTEGER PRIMARY KEY, subject_id INTEGER, start INTEGER,
			end INTEGER, app_id INTEGER)
		""")
	store.execute("""
		CREATE INDEX IF NOT EXISTS
			event_subject_id ON annotation(subject_id)
		""")
	store.commit()
	
	return store

_store = None
def get_default_store():
	global _store
	if not _store:
		_store = create_store("sqlite:stormtest.sqlite")
	return _store

def set_store(storm_store):
	global _store
	if _store :
		_store.close()
	_store = storm_store
