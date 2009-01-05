
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
		self.connection = sqlite3.connect(path[0], True)
		self.cursor = self.connection.cursor()
		self.offset = 0
	
	def create_db(self):
		path = glob.glob(os.path.expanduser("~/.Zeitgeist/gzg.sqlite"))
		if len(path) == 0:
			try:
				homedir = glob.glob(os.path.expanduser("~/"))
				dbdir = homedir[0] +".Zeitgeist"
				try:
					os.mkdir(dbdir)
				except:
					pass
				shutil.copy("gzg.sqlite", dbdir)	  
			except :
				print "Unexpected error creating database:", sys.exc_info()[0]

	

	def get_last_timestmap(self):
		temp = self.cursor.execute( "SELECT * FROM timetable WHERE start IN (SELECT MAX(start) AS start FROM timetable)").fetchall()
		try:
			return temp[0][0]
		except:
			return 0
		
		
	def insert_items(self,items):
		for item in items:
				#print item.name
				#print item.timestamp
				try:
					self.cursor.execute('INSERT INTO timetable VALUES (?,?,?,?)', (item.timestamp,
																					None,
																					item.uri,
																					item.diff))
					self.cursor.execute('INSERT INTO data VALUES (?,?,?,?,?,?,?,?)', (item.uri,
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
				    #print "Error writing " + item.uri + " with timestamp "+ str(item.timestamp)
				del item
		del items
		self.connection.commit()
		   
	def get_items(self,min,max):

		for t in  self.cursor.execute("SELECT start , end,  uri FROM timetable WHERE start >= "+str(int(min)) +" and start <= " + str(int(max))).fetchall():
			
			i = self.cursor.execute("SELECT * FROM data WHERE uri=?",(t[2],)).fetchone()
			try:
				yield Data(uri=i[0], 
					          timestamp= t[0], 
					          name= i[1], 
					          comment=i[2], 
					          mimetype=  i[3], 
					          tags=i[4], 
					          count=i[5], 
					          use =i[6], 
					          type=i[7])
			except:
				print "ERROR"
				#pass
			del i,t
		gc.collect()
	 
	def update_item(self,item):
		 
		 self.cursor.execute('DELETE FROM  data where uri=?',(item.uri,))
		 self.cursor.execute('INSERT INTO data VALUES (?,?,?,?,?,?,?,?)',(item.uri,
																								   item.name,
																								   item.comment,
																								   item.mimetype,
																								   item.tags,
																								   item.count,
																								   item.use,
																								   item.type))
		
		
	 	 self.cursor.execute('DELETE FROM tags where uri=?',(item.uri,))
	 	 
		 for tag in item.get_tags():
		 	if not tag.strip() == "":
		 	    self.cursor.execute('INSERT INTO tags VALUES (?,?)',(tag,item.uri)) 		 	 
		 			 		
		 self.connection.commit()
		 
	def get_most_tags(self,count=10):
 	  pass
		
db=DBConnector()
