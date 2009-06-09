'''
Created on Jun 6, 2009

@author: seif, kamstrup
'''

import os
from storm.locals import *

class Entity(object):
    """Generic base class for anything that has an 'id' and a 'value'"""
    id = Int()
    value = Unicode()
    
    def __init__ (self, value=None, id=None):
        """Look up an Entity in the store, and create a new one if it was not
           found an the keyword argument 'value' is not None. Any created entity
           will be added to the store (but the store still need flushing)"""
        if value:
            value = unicode(value) # A no-op if value is already a unicode
            self.value = value
            ent = None
            try:
                # The store.find() triggers an implicit flush() and the
                # entity we are creating is in an illegal state atm
                store.block_implicit_flushes()
                ent = store.find(self.__class__, self.__class__.value == value).one()
            finally:
                store.unblock_implicit_flushes()
            
            if ent:
                self.id = ent.id
                self.value = value
            else:
                # This is a new entity, we don't have an id yet,
                # store.flush() will set the id for us
                self.value = value
                store.add(self)
        elif id:
            ent = store.find(self.__class__, self.__class__.id == id).one()
            if ent:
                self.id = id
                self.value = ent.value
            else:
                # Requested a URI, by id, but none was found
                store.rollback()
                raise ValueError("No URI registered for id %s" % id)

class Content(Entity):
    __storm_table__= "content"
    __storm_primary__= "id"
    
    def __init__ (self, value):                
        super(Content, self).__init__(value=value)        
    
class Source(Entity):
    __storm_table__= "source"
    __storm_primary__= "id"

    def __init__ (self, value):                
        super(Source, self).__init__(value=value)       
    
class URI(Entity):
    __storm_table__= "uri"
    __storm_primary__= "id"
    
    def __init__ (self, uri_string):                
        super(URI, self).__init__(value=uri_string)    

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
        """Lookup and item based on its URI or create a new Item and add it to
           the store if no item can be found for the URI. The 'uri' argument
           may be a 'str', 'unicode' or 'URI' instance"""
        super(Item, self).__init__()
        if isinstance(uri, str) or isinstance(uri,unicode):
            uri = unicode(uri) # A no-op if value is already a unicode
            this = store.find(Item, Item.id == URI.id, URI.value == uri).one()
            if this:
                self.clone_item(this)
            else:
                # This is a new item, we don't have an id yet,
                # store.flush() will set the id for us
                self.uri = URI(uri)
                store.add(self.uri)
                store.flush() # We need to flush the uri to get an id assigned
                self.id = self.uri.id
                assert self.id is not None
                store.add(self) # All good, add us to the store
        elif isinstance(uri, URI):
            if uri.id is None:
                store.rollback()
                raise ValueError("Creating item on non-registered URI")            
            this = store.find(Item, Item.id == uri.id).one()
            if this:
                # The item was already known
                self.clone_item(this)
            else:
                # Create a new item on the given URI
                self.uri = uri
                self.id = uri.id
                store.add(self)
    
    def clone_item (self, item):
        """Read all properties of 'item' into 'self'"""
        self.id = item.id
        self.uri = item.uri
        self.content_id = item.content_id
        self.source_id = item.source_id
        self.icon = item.icon
        self.text = item.text
        self.mimetype = item.mimetype
        self.payload = item.payload
            
        
#
# Storm does not handle multi-table classes. The following design pattern is
# a simplifaction of Infoheritance described here:
# https://storm.canonical.com/Infoheritance
#

class ProxyItem(object):
    
    # Don't declare primary key here, because Annotation needs a compound key
    item_id = Int(allow_none=False, name="item_id") # private
    item = Reference(item_id, Item.id)
    
    def __init__ (self, uri):
        super(ProxyItem, self).__init__()
        uri = unicode(uri)
        
        # Prepare the URI of the annotation, we need the id
        uri = URI(uri)
        store.add(uri)
        store.flush() # resolves the URI id
        self.item_id = uri.id
        assert self.item_id is not None
        
        # Set up the backing Item representing the annotation
        self.item = Item(uri)        
    
class App(ProxyItem):
    __storm_table__= "app"
    __storm_primary__ = "item_id"
    value = Unicode()
    
    def __init__ (self, uri):
        super(App,self).__init__(uri)

class ReferencingProxyItem(ProxyItem):
    """Base class for items which point to a subject URI. The primary subclasses
       are Annotation and Event"""
    
    subject_id = Int(allow_none=False)
    subject = Reference(subject_id, Item.id)
    
    def __init__ (self, uri, subject_uri):
        """Create a new ReferencingProxyItem. The 'subject_uri'
           argument may be a 'str', 'unicode', or 'URI'"""
        super(ReferencingProxyItem,self).__init__(uri)
        
        # Resolve the subject_id from a uri string or URI object
        if isinstance(subject_uri, str) or isinstance(subject_uri, unicode):
            uri = None
            try:
                # The store.find() triggers an implicit flush() and the
                # annotation we are creating is in an illegal state atm
                store.block_implicit_flushes()
                uri = store.find(URI, URI.value == unicode(subject_uri)).one()
            finally:
                store.unblock_implicit_flushes()
            if not uri:
                store.rollback()
                raise ValueError("Creating reference to "
                                 "non-registered URI %s" % subject_uri)
            self.subject_id = uri.id
        elif isinstance(subject_uri, URI):            
            if not self.subject_id:
                store.flush() # This should set the id                
            self.subject_id = subject_uri.id
            return # No need to resolve the URI        
        else:
            store.rollback()
            raise ValueError("The 'subject_uri' argument must be a 'str', "
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
                
        # Add the new annotation to the store
        store.add(self)      
   
class Event(ReferencingProxyItem):
    __storm_table__= "event"
    __storm_primary__ = "item_id"
    
    start = Int(allow_none=False)
    end = Int(allow_none=False)
    app_id = Int(allow_none=False)
    app = Reference(app_id, Item.id)
    
    def __init__ (self, uri, subject_uri):
        """Create a new Event and add it to the store. The 'subject_uri'
           argument may be a 'str', 'unicode', or 'URI' and points to the
           subject which have been effected by the event"""
        super(Event,self).__init__(uri, subject_uri)
        
        # Add the new event to the store
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
				"(item_id INTEGER PRIMARY KEY, value VARCHAR)")
		store.execute("CREATE UNIQUE INDEX IF NOT EXISTS app_value ON app(value)")
	except Exception, ex:
		print ex
	
	try:
		store.execute("CREATE TABLE IF NOT EXISTS annotation" 
				"(item_id INTEGER, subject_id INTEGER)")
		store.execute("CREATE UNIQUE INDEX IF NOT EXISTS "
					"annotation_link ON annotation(item_id,subject_id)")
	except Exception, ex:
		print ex
	
	try:
		store.execute("CREATE TABLE IF NOT EXISTS event" 
				"(item_id INTEGER PRIMARY KEY, subject_id INTEGER, start INTEGER, end INTEGER, app_id INTEGER)")
		store.execute("CREATE UNIQUE INDEX IF NOT EXISTS event_link ON event(subject_id,item_id)")
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
