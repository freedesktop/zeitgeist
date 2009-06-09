'''
Created on Jun 6, 2009

@author: seif, kamstrup
'''

import os
from storm.locals import *

class Entity(object):
	"""Generic base class for anything that has an 'id' and a 'value'.
		It is assumed that there is a unique index on the value column"""
	id = Int(allow_none=False)
	value = Unicode()
	
	def __init__ (self, value):
		"""Create an Entity in the store. Any created entity will automatically
		   be added to the store (but the store still need flushing) before an
		   id is assigned to the entity"""
		if value is None :
			raise ValueError("Can not create Entity with value None")
		
		self.value = unicode(value) # A no-op if value is already a unicode	
		store.add(self)
	
	def resolve (self):
		"""Make sure that the id property of this object has been resolved.
			If the entity already has an id, this method is a no-op"""
		if not self.id:
			store.flush()
		assert self.id

	@classmethod
	def lookup(klass, value=None, id=None):
		"""Look up an entity by value or id, return None if the
		   entity is not known"""
		if value:
			value = unicode(value)
			return store.find(klass, klass.value == value).one()
		elif id:
			return store.find(klass, klass.id == id).one()
		else:
			raise ValueError("Looking up Entity without a value or id")
	
	@classmethod
	def lookup_or_create(klass, value):
		ent = klass.lookup(value)		
		if ent : return ent
		return klass(value)
		

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
	
class URI(Entity):
	__storm_table__= "uri"
	__storm_primary__= "id"
	
	def __init__ (self, value):				
		super(URI, self).__init__(value)

class Item(object):
	__storm_table__= "item"

	id = Int(primary=True, allow_none=False)
	uri = Reference(id, URI.id)
	
	content_id = Int()
	content = Reference(content_id, Content.id)
	
	source_id = Int()
	source = Reference(source_id, Source.id)
	
	icon = Unicode()
	
	text = Unicode()
	mimetype = Unicode()
	payload = RawStr() # Storm lingo for BLOB/BYTEA

	def __init__ (self, uri):
		"""Create an item on a given URI and add it to the store.
		   The 'uri' argument may be a 'str', 'unicode' or 'URI' instance"""
		super(Item, self).__init__()
		if isinstance(uri, str) or isinstance(uri,unicode):
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
		
		store.add(self) # All good, add us to the store
	
	@classmethod
	def lookup(klass, uri):
		if isinstance(uri, str) or isinstance(uri,unicode):
			uri = unicode(uri)
			return store.find(Item,
							Item.id == URI.id,
							URI.value == uri).one()
		elif isinstance(uri, URI):
			return store.find(Item, Item.id == uri.id).one()
	
	@classmethod
	def lookup_or_create(klass, uri):
		item = klass.lookup(uri)
		if item : return item
		return klass(uri)
			
		
#
# Storm does not handle multi-table classes. The following design pattern is
# a simplifaction of Infoheritance described here:
# https://storm.canonical.com/Infoheritance
#

class ProxyItem(object):
	
	# Don't declare primary key here, because Annotation needs a compound key
	item_id = Int(allow_none=False)
	item = Reference(item_id, Item.id)
	uri = Reference(item_id, URI.id)
	
	def __init__ (self, uri):
		"""Create a ProxyItem with a given URI. If the URI is not already 
		   registered it will be so. The 'uri' argument may be a 'str',
		   'unicode', or 'URI' instance"""
		super(ProxyItem, self).__init__()
		
		# The Item constructor will register the URI if needed
		self.item = Item(uri)
		self.uri_id = self.item.uri.id
		self.uri = self.item.uri
	
	@classmethod
	def lookup (klass, uri):
		if isinstance(uri, str) or isinstance(uri, unicode):
			uri = unicode(uri)
			return store.find(klass, klass.item_id == URI.id, URI.value == uri).one()
		elif isinstance(uri, URI):
			return store.find(klass, klass.item_id == uri.id).one()
	
	@classmethod
	def lookup_or_create(klass, uri):
		proxy = klass.lookup(uri)
		if proxy : return proxy
		return klass(uri)
	
	
class App(ProxyItem):
	__storm_table__= "app"
	__storm_primary__ = "item_id"
	info = Unicode()
	
	def __init__ (self, uri):
		super(App,self).__init__(uri)
		# FIXME: Somehow parse the application name out of the .desktop file
		store.add(self)

class ReferencingProxyItem(ProxyItem):
	"""Base class for items which point to a subject URI. The primary subclasses
	   are Annotation and Event"""
	
	subject_id = Int()
	subject = Reference(subject_id, Item.id)
	
	def __init__ (self, uri, subject_uri):
		"""Create a new ReferencingProxyItem. The 'subject_uri'
		   argument may be a 'str', 'unicode', or 'URI'"""
		super(ReferencingProxyItem,self).__init__(uri)
		
		# Resolve the subject_id from a uri string or URI object
		if isinstance(subject_uri, str) or isinstance(subject_uri, unicode):
			uri = URI.lookup_or_create(subject_uri)
			uri.resolve()
			self.subject_id = uri.id
		elif isinstance(subject_uri, URI):
			subject_uri.resolve()				
			self.subject_id = subject_uri.id
		else:
			store.rollback()
			raise TypeError("The 'subject_uri' argument must be a 'str', "
							 "'unicode', or 'URI'. Found %s" % type(subject_uri))
	
class Annotation(ReferencingProxyItem):
	# We use a compound primary key because the same annotation can point to
	# several subjects, so that only the (id,subject_id) pair is unique
	__storm_table__= "annotation"
	__storm_primary__ = "item_id", "subject_id"	   
	
	def __init__ (self, uri, subject_uri):
		"""Create a new annotation and add it to the store. The 'subject_uri'
		   argument may be a 'str', 'unicode', or 'URI' and points at the
		   object being the subject of the annotations"""
		super(Annotation,self).__init__(uri, subject_uri)
		store.add(self)

class Event(ReferencingProxyItem):
	__storm_table__= "event"
	__storm_primary__ = "item_id"
	
	start = Int()
	end = Int()
	app_id = Int()
	app = Reference(app_id, App.item_id)
	
	def __init__ (self, uri, subject_uri):
		"""Create a new Event and add it to the store. The 'subject_uri'
		   argument may be a 'str', 'unicode', or 'URI' and points to the
		   subject which have been effected by the event"""
		super(Event,self).__init__(uri, subject_uri)
		store.add(self)	

def create_store(storm_url):
	print "DB setup, %s" % storm_url
	db = create_database(storm_url)
	store = Store(db)
	try:
		store.execute("CREATE TABLE IF NOT EXISTS content" 
				"(id INTEGER PRIMARY KEY, value VARCHAR UNIQUE)")
		store.execute("CREATE UNIQUE INDEX IF NOT EXISTS content_value ON content(value)")
	except Exception, ex:
		print ex
	
	try:
		store.execute("CREATE TABLE IF NOT EXISTS source" 
				"(id INTEGER PRIMARY KEY, value VARCHAR UNIQUE)")
		store.execute("CREATE UNIQUE INDEX IF NOT EXISTS source_value ON source(value)")
	except Exception, ex:
		print ex

	try:
		store.execute("CREATE TABLE IF NOT EXISTS uri" 
				"(id INTEGER PRIMARY KEY, value VARCHAR UNIQUE)")
		store.execute("CREATE UNIQUE INDEX IF NOT EXISTS uri_value ON uri(value)")
	except Exception, ex:
		print ex
	
	try:
		store.execute("CREATE TABLE IF NOT EXISTS item" 
				"(id INTEGER PRIMARY KEY, content_id INTEGER, source_id INTEGER, text VARCHAR, mimetype VARCHAR, icon VARCHAR, payload BLOB)")
		# FIXME: Consider which indexes we need on the item table
	except Exception, ex:
		print ex
	
	try:
		store.execute("CREATE TABLE IF NOT EXISTS app" 
				"(item_id INTEGER PRIMARY KEY, info VARCHAR)")
		store.execute("CREATE UNIQUE INDEX IF NOT EXISTS app_value ON app(info)")
	except Exception, ex:
		print ex
	
	try:
		store.execute("CREATE TABLE IF NOT EXISTS annotation" 
				"(item_id INTEGER, subject_id INTEGER)")
		store.execute("CREATE UNIQUE INDEX IF NOT EXISTS "
					"annotation_link ON annotation(item_id,subject_id,start)")
	except Exception, ex:
		print ex
	
	try:
		store.execute("CREATE TABLE IF NOT EXISTS event" 
				"(item_id INTEGER PRIMARY KEY, subject_id INTEGER, start INTEGER, end INTEGER, app_id INTEGER)")
	except Exception, ex:
		print ex

	store.commit()
	return store

store = create_store("sqlite:stormtest.sqlite")

def reset_store(storm_url):
	"""Mainly used for debugging and unit tests - closes, and removes the global
	   store. Then sets the global store to point at storm_url"""
	global store
	print "Resetting store", store, "to ", storm_url
	if isinstance(store, Store):
		store.close()
	
	db_file = storm_url.split(":")[1]
	if os.path.exists(db_file):
		os.remove(db_file)
	
	store = create_store(storm_url)
	return store
