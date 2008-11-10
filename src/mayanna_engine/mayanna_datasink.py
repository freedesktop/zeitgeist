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
        
        '''
        Recently Used
        '''
        
        self.videos=RecentlyUsedVideoSource()
        self.videos.run()
        self.music=RecentlyUsedMusicSource()
        self.music.run()
        self.images=RecentlyUsedImagesSource()
        self.images.run()
        self.docs=RecentlyUsedDocumentsSource()
        self.docs.run()
        self.others = RecentlyUsedOthersSource()
        self.others.run()
        recent_model.connect("reload",lambda x: self.emit("reload"))
        
        
        
        self.firefox = FirefoxSource()
        self.firefox.run()
        #self.chats = RecentContacts()
        self.tomboy = TomboySource()
        self.tomboy.run()
        self.tomboy.connect("reload",lambda x: self.emit("reload"))
        
        
        self.init_sources()
        
        
    def init_sources(self):
       self.sources=[
                     self.videos,
                     self.images,
                     self.music,
                     self.docs,
                     self.others,
                     self.firefox,
                     #self.chats,
                     self.tomboy
                    ]
       
    def get_items(self):
        "Datasink getting all items from DaraProviders"
        items =[]
        for source in self.sources:
            if source.get_active():
                for item in source.get_items():
                    items.append(item)
        items.sort(self.compare)
        items = sorted(items, self.compare_columns)
        "Datasink getting all items from DaraProviders done"
        
        return items
    
    def compare(self,a, b):
        return cmp(a.timestamp, b.timestamp) # compare as integers

    def compare_columns(self,a, b):
        # sort on ascending index 0, descending index 2
        return cmp(a.timestamp, b.timestamp)


datasink= DataSinkSource()
