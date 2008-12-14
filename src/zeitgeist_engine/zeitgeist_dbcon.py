
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
		command = "SELECT * FROM timetable WHERE start IN (SELECT MAX(start) AS start FROM timetable)"
		temp = self.cursor.execute(command).fetchall()
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

		tcontents = "start , end,  uri"
		perioditems = self.cursor.execute("SELECT " +tcontents+ " FROM timetable WHERE start >= "+str(int(min)) +" and start <= " + str(int(max))).fetchall()

		for t in perioditems:
			
			i = self.cursor.execute("SELECT * FROM data WHERE uri=?",(t[2],)).fetchall()
			try:
				yield Data(uri=i[0][0], 
					          timestamp= t[0], 
					          name= i[0][1], 
					          comment=i[0][2], 
					          mimetype=  i[0][3], 
					          tags=i[0][4], 
					          count=i[0][5], 
					          use =i[0][6], 
					          type=i[0][7])
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
		 self.connection.commit()
		
db=DBConnector()
