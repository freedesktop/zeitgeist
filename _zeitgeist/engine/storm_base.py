# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Seif Lotfy <seif@lotfy.com>
# Copyright © 2009 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
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

import os
import sys
import logging
from storm.locals import *
from xdg import BaseDirectory

from zeitgeist.datamodel import Content, Source, DictCache
from _zeitgeist.lrucache import LRUCacheMetaclass
import _zeitgeist.engine

log = logging.getLogger("zeitgeist.engine.base")

class Entity(object):
	""" Generic base class for anything that has an 'id' and a 'value'.
		It is assumed that there is a unique index on the value column
	"""
	
	id = Int(allow_none=False)
	value = Unicode()
	
	def __init__ (self, value, add_to_store=True):
		"""Create an Entity in the store. Any created entity will automatically
		   be added to the store (but the store still need flushing) before an
		   id is assigned to the entity"""
		if self.__class__ == Entity:
			raise ValueError("Entity is an abstract class an "
							 "can not be instantiated")
		if value is None :
			raise ValueError("Can not create Entity with value None")
		
		self.value = unicode(value) # A no-op if value is already a unicode
		
		if add_to_store:
			_store.add(self)
			_store.flush()
			self.__class__._CACHE[value] = self
	
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
		if value:
			value = unicode(value)
			if klass._CACHE is not None and value in klass._CACHE:
				return klass._CACHE[value]
			ent = _store.find(klass, klass.value == value).one()
			if klass._CACHE is not None and ent:
				klass._CACHE[value] = ent
			return ent
		elif id:
			return _store.get(id) # Lookup on primary key
		else:
			raise ValueError("Looking up Entity without a value or id")
	
	@classmethod
	def lookup_or_create(klass, value):
		"""Find the entity matching the uri 'value' or create it if necessary"""
		#
		# The algorithm used here is as follows:
		#  1) Return it if we have it cached
		#  2) Try to create it
		#  3) Look it up and return it
		#
		if klass._CACHE is not None and value in klass._CACHE:
			return klass._CACHE[value]
		
		value = unicode(value)
		ent = klass(value, add_to_store=False)
		try:
			_store.execute(
			"INSERT INTO %s (value) VALUES (?)" % klass.__storm_table__,
			(value, ), noresult=True)
		except Exception, ex:
			pass
		_store.flush()
		
		id_query = _store.execute(
					"SELECT id FROM %s WHERE VALUE=?" % klass.__storm_table__,
					(value, )).get_one()
		if not id_query:
			log.error("Failed to insert %s entity: %s" % (
				klass.__storm_table__,value))
			return None
		ent.id = id_query[0]
		if klass._CACHE is not None:
			klass._CACHE[value] = ent
		
		return ent


class _Content(Entity):
	__storm_table__= "content"
	__storm_primary__= "id"
	__metaclass__ = DictCache
Content.bind_database(_Content)


class _Source(Entity):
	__storm_table__= "source"
	__storm_primary__= "id"
	__metaclass__ = DictCache
Source.bind_database(_Source)


class URI(Entity):
	__storm_table__= "uri"
	__storm_primary__= "id"
	
	# URI uses an LRUCache rather than a plain dict because it may end up
	# storing thousands and thousands of items
	__metaclass__ = LRUCacheMetaclass

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
			self.id = uri.id
			assert self.id is not None			
		elif isinstance(uri, URI):
			self.uri = uri
			self.id = uri.id
		else:
			raise TypeError("Expected 'str', 'unicode', or 'URI', got %s" % type(uri))
		
		_store.add(self) # All good, add us to the store
	
	@classmethod
	def lookup(klass, uri):
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
		self.item = Item.lookup_or_create(uri)
		self.uri_id = self.item.uri.id
		self.uri = self.item.uri
	
	@classmethod
	def lookup(cls, uri):
		if isinstance(uri, str) or isinstance(uri, unicode):
			uri = unicode(uri)
			return _store.find(cls, cls.item_id == URI.id, URI.value == uri).any()
		elif isinstance(uri, URI):
			return _store.find(cls, cls.item_id == uri.id).any()
	
	@classmethod
	def lookup_or_create(cls, uri):
		proxy = cls.lookup(uri)
		return proxy if proxy else cls(uri)

class App(ProxyItem):
	__storm_table__= "app"
	__storm_primary__ = "item_id"
	info = Unicode()
	
	def __init__ (self, uri):
		super(App,self).__init__(uri)
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
	
	@classmethod
	def subjects_of(klass, uri):
		""""""
		if isinstance(uri, str) or isinstance(uri, unicode):
			uri = unicode(uri)
			return _store.find(Item,
							   klass.item_id == URI.id,
							   URI.value == uri,
							   Item.id == klass.subject_id)
		elif isinstance(uri, URI):
			return _store.find(self,
							   klass.item_id == uri.id,
							   Item.id == klass.subject_id)
	
	def find_subjects(self):
		return _store.find(Item, Item.id == self.subject_id)

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

#
# Many-to-many relationships
#
Item.annotations = ReferenceSet(Item.id, Annotation.subject_id)
Item.events = ReferenceSet(Item.id, Event.subject_id)

def create_store(storm_url):
	log.info("Creating database: %s" % storm_url)
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
			(item_id INTEGER, subject_id INTEGER, PRIMARY KEY (item_id, subject_id))
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

def clear_entity_cache():
	"""All entity ids are cached because they can be assumed to remain stable
	   across a session. In cases like unit tests where the db is often reset,
	   this cache needs to be reset in order to provide correct results"""
	URI._clear_cache()
	Content._clear_cache()
	Source._clear_cache()

_store = None
def get_default_store():
	global _store
	if not _store:
		file = _zeitgeist.engine.DB_PATH
		_store = create_store("sqlite:" + file)
		clear_entity_cache()
	return _store

def set_store(storm_store):
	global _store
	if _store :
		clear_entity_cache()
		_store.close()
	_store = storm_store
