'''
Created on Jun 6, 2009

@author: seif
'''

from storm.locals import *

_database = create_database("sqlite:stormtest.sqlite")
store = Store(_database)

class Content(object):
    __storm_table__= "content"
    id = Int(primary=True)
    value = Unicode()
    
    def __init__ (self, value):                
        super(Content, self).__init__()
        if not isinstance(value, unicode):
            self.value = unicode(value)
        else:
            self.value = value
    
class Source(object):
    __storm_table__= "source"
    id = Int(primary=True)
    value = Unicode()
    
    def __init__ (self, value):                
        super(Source, self).__init__()
        if not isinstance(value, unicode):
            self.value = unicode(value)
        else:
            self.value = value
    
class URI(object):
    __storm_table__= "uri"
    id = Int(primary=True)
    value = Unicode()
    
    def __init__ (self, uri_string):                
        super(URI, self).__init__()
        if not isinstance(uri_string, unicode):
            self.value = unicode(uri_string)
        else:
            self.value = uri_string
    
    

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
        """Create a new Item and add it to the store. The 'uri' argument
           may be a 'str', 'unicode' or 'URI' instance"""
        super(Item, self).__init__()
        if isinstance(uri, str):
            self.uri = URI(unicode(uri))
        elif isinstance(uri, unicode):
            self.uri = URI(uri)
        elif isinstance(uri, URI):
            self.uri = uri
        else:
            raise ValueError("'uri' argument must be a 'str', "
                             "'unicode', or 'URI'. Found %s" % type(uri))
        
        # Prepare the URI of the item, we need the id
        store.add(self.uri)
        store.flush() # resolves the URI id
        self.id = self.uri.id
        assert self.id is not None
        
        # Add us to the store
        store.add(self)
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
        if not isinstance(uri, unicode):
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
    info = Unicode()
    
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
                raise ValueError("Creating annotation for "
                                 "non-registered uri %s" % subject_uri)
            self.subject_id = uri.id
        elif isinstance(subject_uri, URI):            
            if not self.subject_id:
                store.rollback()
                raise ValueError("Creating annotation for unresolved URI")
            self.subject_id = uri.id
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
    
print "DB setup"

try:
    store.execute("CREATE TABLE content" 
              "(id INTEGER PRIMARY KEY, value VARCHAR UNIQUE)")
except Exception, ex:
    print ex

try:
    store.execute("CREATE TABLE source" 
              "(id INTEGER PRIMARY KEY, value VARCHAR UNIQUE)")

except Exception, ex:
    print ex

try:
    store.execute("CREATE TABLE uri" 
              "(id INTEGER PRIMARY KEY, value VARCHAR UNIQUE)")

except Exception, ex:
    print ex

try:
    store.execute("CREATE TABLE item" 
              "(id INTEGER PRIMARY KEY, content_id INTEGER, source_id INTEGER, text VARCHAR, mimetype VARCHAR, payload BLOB)")

except Exception, ex:
    print ex

try:
    store.execute("CREATE TABLE app" 
              "(item_id INTEGER PRIMARY KEY, value VARCHAR)")

except Exception, ex:
    print ex

try:
    store.execute("CREATE TABLE annotation" 
              "(item_id INTEGER PRIMARY KEY, subject_id INTEGER)")

except Exception, ex:
    print ex

try:
    store.execute("CREATE TABLE event" 
              "(item_id INTEGER PRIMARY KEY, subject_id INTEGER, start INTEGER, end INTEGER, app_id INTEGER)")

except Exception, ex:
    print ex

store.commit()

print "Data fiddling"

