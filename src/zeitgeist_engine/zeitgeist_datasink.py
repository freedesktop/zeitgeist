#!/usr/bin/env python
from zeitgeist_engine.zeitgeist_base import ItemSource
from zeitgeist_engine.zeitgeist_firefox import FirefoxSource
from zeitgeist_engine.zeitgeist_tomboy import TomboySource
from zeitgeist_engine.zeitgeist_recent import *
from gettext import gettext as _
import urllib
import time
import sys

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
        recent_model.connect("reload", self.log)
        
        self.firefox = FirefoxSource()
        self.firefox.run()
        
        #self.chats = RecentContacts()
        self.tomboy = TomboySource()
        self.tomboy.run()
        self.tomboy.connect("reload", self.log)
        
        self.lasttimestamp = 0
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
    
    
    def log(self,x=None):
        print("reloading")
        note_path = os.path.expanduser("~/.zeitgeist.log")
        input = ""
        f= open(note_path,'r+')
        lines = f.read().split("\n")
        for item in self.get_items_by_time():
            line= str(item.timestamp) + "   |---GZG---|   " + item.uri
            try:
                index =  lines.index(line)
            except:
                f.write(str(item.timestamp) + "   |---GZG---|   " + item.uri+"\n")
        f.close()
        self.emit("reload")
            
       
    def get_items(self,min=0,max=sys.maxint):
        "Datasink getting all items from DaraProviders done"
        items =[]
        for source in self.sources:
            if source.get_active():
                for item in source.get_items(min,max):
                    items.append(item)
                    del item
            del source
        return items
        
    def get_items_by_time(self,min=0,max=sys.maxint):
        "Datasink getting all items from DaraProviders"
        items = self.get_items(min,max)
        items.sort(self.comparetime)
        return items
    
    def get_freq_items(self,min=0,max=sys.maxint):
        items =[]
        for source in self.sources:
            if source.get_active():
                sourcelist= source.get_freq_items(min,max)
                items += sourcelist
            del source
        items.sort(self.comparecount)
        return items
               
                    

datasink= DataSinkSource()
