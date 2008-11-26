
import shutil
import sqlite3 as db
import tempfile
import re
import glob
import os
from zeitgeist_engine.zeitgeist_base import ItemSource, Item

class DBConnector:
    
    def __init__(self):
        path = glob.glob(os.path.expanduser("~/.Zeitgeist/zeitgeist.sqlite"))
        
        self.connection = db.connect(path[0],True)
        self.cursor = self.connection.cursor()
        
    def insert_item(self,item):
        
        try:
            self.cursor.execute('INSERT INTO timetable VALUES ( ?, ?,?)',(item.timestamp, item.uri, item.get_name()))
            self.connection.commit()
            print("wrote "+item.uri+" into database")
        except:
            pass
    
    def get_items(self,min,max):
        items = []
        contents = "timestamp , data, name"
        #print ("min = " + str(min))
        #print ("max = " + str(max))
        temp = self.cursor.execute("SELECT " +contents+ " FROM timetable WHERE timestamp >= "+str(int(min)) +" and timestamp <= " + str(int(max))).fetchall()
        print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        for i in temp:
            timestamp = i[0]
            uri= i[1]
            name = i[2]
            print str(timestamp) + " " + uri + name
            item = Item(uri=uri, timestamp=timestamp, name=name)
            items.append(item)
        #print(str(len(items)))
        return items
        