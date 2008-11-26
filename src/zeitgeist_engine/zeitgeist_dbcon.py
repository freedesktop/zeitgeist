
import shutil
import sqlite3 as db
import tempfile
import re
import glob
import sys
import os
from zeitgeist_engine.zeitgeist_base import ItemSource, Item

class DBConnector:
    
    def __init__(self):
        
        self.create_db()
        path = glob.glob(os.path.expanduser("~/.Zeitgeist/zeitgeist.sqlite"))
        print (str(path))
        self.connection = db.connect(path[0],True)
        self.cursor = self.connection.cursor()
        self.offset = 0
    
    def create_db(self):
        try:
            homedir = glob.glob(os.path.expanduser("~/"))
            homedir = homedir[0] +".Zeitgeist"
            os.mkdir(homedir)
            shutil.copy("./zeitgeist.sqlite", homedir)     
        except :
            print "Unexpected error:", sys.exc_info()[0]

    def get_last_timestmap(self):
        command = "SELECT * FROM timetable WHERE timestamp IN (SELECT MAX(timestamp) AS timestamp FROM timetable)"
        temp = self.cursor.execute(command).fetchall()
        try:
            return temp[0][0]
        except:
            return 0
        
    def insert_item(self,item):
            try:
                self.cursor.execute('INSERT INTO timetable VALUES ( ?,?,?,?,?,?)',(item.timestamp, item.uri, item.get_name(), "", item.count, item.use))
                self.connection.commit()
                print("wrote "+item.uri+" into database")
            except:
                pass
                '''
                command ="SELECT * FROM timetable WHERE timestamp = "+ str(item.timestamp)
                temp = self.cursor.execute(command).fetchall()
                temp = str(temp[0][1])
                uri = item.uri
                if not uri == temp:
                    self.offset = self.offset +1
                    item.timestamp = item.timestamp + self.offset
                    try:
                        self.cursor.execute('INSERT INTO timetable VALUES ( ?,?,?,?,?)',(item.timestamp, item.uri, item.get_name(), "", item.count))
                        self.connection.commit()
                        print("wrote "+item.uri+" into database")
                    except:
                        print ("Error on "+item.get_name())
                '''
                    
    def get_items(self,min,max):
        items = []
        contents = "timestamp , data,  name,  type, count, use"
        #print ("min = " + str(min))
        #print ("max = " + str(max))
        temp = self.cursor.execute("SELECT " +contents+ " FROM timetable WHERE timestamp >= "+str(int(min)) +" and timestamp <= " + str(int(max))).fetchall()
        for i in temp:
            timestamp = i[0]
            uri= i[1]
            name = i[2]
            type = i[3]
            count = i[4]
            use = i[5]
            item = Item(uri=uri, timestamp=timestamp, name=name, count=count, use=use)
            items.append(item)
        #print(str(len(items)))
        return items
        
db=DBConnector()