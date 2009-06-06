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
    id = URI(primary=True)
    content = Content()
    source = Source()
    caption = Unicode()
    mimetype = Unicode()
    icon = Unicode()
   # payload =
   
class App(Item):
    __storm__table__= "app"
    info = Unicode()
   # payload =
   
class Annotation(Item):
    __storm__table__= "annotation"
    target = Unicode()
   # payload =
   
class Event(Item):
    subject = Int()
    start = Int()
    end = Int()
    app = Int()