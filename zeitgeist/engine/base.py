'''
Created on Jun 6, 2009

@author: seif
'''

from storm.locals import *

class Content(object):
    __storm__table__= "content"
    id = Int(primary=True)
    value = Unicode()
    
class Source(object):
    __storm__table__= "source"
    id = Int(primary=True)
    value = Unicode()
    
class URI(object):
    __storm__table__= "uri"
    id = Int(primary=True)
    value = Unicode()
    
    

class Item(object):
    __storm__table__= "item"
    content = Content()
    source = Source()
    caption = Unicode()
    mimetype = Unicode()
    icon_name = Unicode()
    icon_type = Unicode()
    #payload = ByteArray()
   
class App(Item):
    __storm__table__= "app"
    info = Unicode()
   
class Annotation(Item):
    __storm__table__= "annotation"
    target = Unicode()
   
class Event(Item):

    __storm__table__= "event"
    subject = Int()
    start = Int()
    end = Int()
    app = Int()
    

database = create_database("sqlite:/home/seif/Desktop/test.sqlite")
store = Store(database)
try:
    store.execute("CREATE TABLE content" 
              "(id INTEGER PRIMARY KEY, value VARCHAR)")
except:
    pass

try:
    store.execute("CREATE TABLE source" 
              "(id INTEGER PRIMARY KEY, value VARCHAR)")
except:
    pass

try:
    store.execute("CREATE TABLE uri" 
              "(id INTEGER PRIMARY KEY, value VARCHAR)")
except:
    pass

try:
    store.execute("CREATE TABLE item" 
              "(id INTEGER PRIMARY KEY, content INTEGER, source INTEGER, caption VARCHAR, mimetype VARCHAR, icon_name VARCHAR, icon_type VARCHAR, payload BLOB)")
except:
    pass

try:
    store.execute("CREATE TABLE app" 
              "(id INTEGER PRIMARY KEY, value VARCHAR)")
except:
    pass

try:
    store.execute("CREATE TABLE annotation" 
              "(id INTEGER PRIMARY KEY, value VARCHAR)")
except:
    pass

try:
    store.execute("CREATE TABLE event" 
              "(id INTEGER PRIMARY KEY, subject INTEGER, start INTEGER, end INTEGER, app INTEGER")
except:
    pass




store.commit()


