#!/usr/bin/env python
from mayanna_engine.mayanna_base import ItemSource
#from mayanna_engine.mayanna_pidgin import RecentContacts
from mayanna_engine.mayanna_firefox import FirefoxSource
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
        self.firefox = FirefoxSource()
        #self.chats = RecentContacts()
        self.tomboy = TomboySource()
        self.tomboy.connect("reload",lambda x: self.emit("reload"))
        self.init_sources()
        
    def init_sources(self):
       self.sources=[
                     self.videos,
                     self.images,
                     self.music,
                     self.docs,
                     self.others,
                     #self.firefox,
                     #self.chats,
                     self.tomboy
                    ]
       
    def get_items(self):
        items =[]
        for source in self.sources:
            if source.get_active():
                for item in source.get_items():
                    items.append(item)
        items.sort(self.compare)
        items = sorted(items, self.compare_columns)
        return items
    
    def compare(self,a, b):
        return cmp(a.timestamp, b.timestamp) # compare as integers

    def compare_columns(self,a, b):
        # sort on ascending index 0, descending index 2
        return cmp(a.timestamp, b.timestamp)


datasink= DataSinkSource()