#!/usr/bin/env python
from mayanna_engine.mayanna_base import ItemSource
#from mayanna_engine.mayanna_pidgin import RecentContacts
from mayanna_engine.mayanna_tomboy import TomboySource
from mayanna_engine.mayanna_recent import *
import urllib
import time
from gettext import gettext as _

class DataSinkSource(ItemSource):
    def __init__(self, note_path=None):
        ItemSource.__init__(self,
                            name=_("Sink"),
                            icon=None,
                            uri="source:///Datasink")
        self.sources=[]
        recent_model.connect("reload",lambda x: self.emit("reload"))
        self.videos=RecentlyUsedVideoSource()
        self.music=RecentlyUsedMusicSource()
        self.images=RecentlyUsedImagesSource()
        self.docs=RecentlyUsedDocumentsSource()
        self.others = RecentlyUsedOthersSource()
        #self.chats = RecentContacts()
        self.tomboy = TomboySource()
        self.init_sources()
        
    def init_sources(self):
       self.sources=[
                     self.videos,
                     self.images,
                     self.music,
                     self.docs,
                     self.others,
                     #self.chats,
                     self.tomboy
                    ]
       
    def get_items_uncached(self):
         items =[]
         for source in self.sources:
             for item in source.get_items():
                 items.append(item)
         return items
    

datasink= DataSinkSource()