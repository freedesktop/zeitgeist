import datetime
import os
import re
import glob
import sqlite3 as db
from gettext import gettext as _
from xml.dom.minidom import parse
from xml.parsers.expat import ExpatError

import gobject
import gtk
import gnomevfs
import W3CDate

from mayanna_base import Item, ItemSource
from mayanna_util import FileMonitor, launcher


class FirefoxItem(Item):
    def __init__(self,uri,name,timestamp):
        self.uri = uri
        self.name = name
        self.timestamp = timestamp
        Item.__init__(self,name=name,uri=uri, timestamp = timestamp)

class FirefoxSource(ItemSource):
    def __init__(self, name = "Firefox History", icon = None):
        
        self.items=[]
        ItemSource.__init__(self, name=name, icon=icon)
        self.name = "Firefox History"
        historydb = glob.glob(os.path.expanduser("~/.mozilla/firefox/*/places.sqlite"))
        self.connection = db.connect(historydb[0])
        #print(cursor)
        #self.emit("reload")
        
    def get_history_items(self,history,i):
        
        items = []
        cursor = self.connection.cursor()
        contents = "id, url, title"
        item = cursor.execute("SELECT " +contents+ " FROM moz_places WHERE id="+str(i[1])).fetchall()
        url = item[0][1]
        name = item[0][2]
        timestamp = history[0][2]
        print(timestamp)
        timestamp = timestamp / (1000000)
        print(timestamp)
        items.append(FirefoxItem(url,name,timestamp))
        
        gtk.gdk.threads_enter()
        self.items += items
        self.emit("reload")
        gtk.gdk.threads_leave()
    
    def get_history(self):
        
        print("reloading firefox history")
        cursor = self.connection.cursor()
        contents = "id, place_id, visit_date"
        history = cursor.execute("SELECT " +contents+ " FROM moz_historyvisits WHERE visit_type=" +str(2)).fetchall()
        for i in history:
            for j in range(len(history) / 10 + 1):
                self.get_history_items(history[j*10:j*10+10],i)
            
        
        print("DONE")
        
    
    def get_items_uncached(self):#
        self.items=[]
        self.get_history()
        return self.items