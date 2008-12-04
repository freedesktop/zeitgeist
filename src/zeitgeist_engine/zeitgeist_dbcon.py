
import shutil
import sqlite3
import tempfile
import re
import glob
import sys
import gc
import os
from zeitgeist_engine.zeitgeist_base import DataProvider, Data

class DBConnector:
    
    def __init__(self):
        
        self.create_db()
        path = glob.glob(os.path.expanduser("~/.Zeitgeist/gzg.sqlite"))
        print (str(path))
        self.connection = sqlite3.connect(path[0],True)
        self.cursor = self.connection.cursor()
        self.offset = 0
    
    def create_db(self):
        path = glob.glob(os.path.expanduser("~/.Zeitgeist/gzg.sqlite"))
        if not os.path.exists(path[0]):
            try:
                
                homedir = glob.glob(os.path.expanduser("~/"))
                homedir = homedir[0] +".Zeitgeist"
                try:
                    os.mkdir(homedir)
                except:
                    pass
                shutil.copy("gzg.sqlite", homedir)    
            except :
                print "Unexpected error:", sys.exc_info()[0]

    def get_last_timestmap(self):
        command = "SELECT * FROM timetable WHERE start IN (SELECT MAX(start) AS start FROM timetable)"
        temp = self.cursor.execute(command).fetchall()
        try:
            return temp[0][0]
        except:
            return 0
        
    def insert_items(self,items):
            for item in items:
               try:
                   self.cursor.execute('INSERT INTO timetable VALUES (?,?,?,?)',(
                                                                                               item.timestamp,
                                                                                               None,
                                                                                               item.uri,
                                                                                               ""))
                   self.cursor.execute('INSERT INTO data VALUES (?,?,?,?,?,?,?,?)',(
                                                                                               item.uri,
                                                                                               item.name,
                                                                                               item.comment,
                                                                                               item.mimetype,
                                                                                               item.tags,
                                                                                               item.count,
                                                                                               item.use,
                                                                                               item.type))
                   print("wrote "+item.uri+" into database")
               except:
                   pass
               self.connection.commit()
               
    def get_items(self,min,max):
        items = []
        tcontents = "start , end,  uri,  diff"
        #print ("min = " + str(min))
        #print ("max = " + str(max))
        
        perioditems = self.cursor.execute("SELECT " +tcontents+ " FROM timetable WHERE start >= "+str(int(min)) +" and start <= " + str(int(max))).fetchall()
        
        for t in perioditems:
            
            uri = t[2]
            i = self.cursor.execute("SELECT * FROM data WHERE uri=?",(uri,)).fetchall()
            timestamp =t[0]
            uri= i[0][0]
            name = i[0][1]
            comment = i[0][2]
            mimetype = i[0][3]
            tags =i[0][4]
            count=i[0][5]
            use =i[0][6]
            type=i[0][7]
            yield Data(uri=uri, timestamp= timestamp, name=name, comment=comment, mimetype= mimetype, tags=tags, count=count, use=use, type =type)
        gc.collect()
        #print(str(len(items)))
     
        
db=DBConnector()