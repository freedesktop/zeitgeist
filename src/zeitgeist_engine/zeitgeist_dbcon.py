import shutil
import sqlite3
import tempfile
import re
import glob
import sys
import gc
import os
from zeitgeist_engine.zeitgeist_base import DataProvider, Data
import time

# Constants for quick use in SQL queries:
# - Rows in the data table
D_URI		= 0
D_NAME		= 1
D_COMMENT	= 2
D_MIMETYPE	= 3
D_TAGS		= 4
D_COUNT		= 5
D_USE		= 6
D_TYPE		= 7

# - Rows in the tags table
TAG = 0
TAG_URI = 1

# - Rows in the timetable table
TIMESTAMP_BEGIN		= 0
TIMESTAMP_END		= 1
TIMESTAMP_URI		= 2
TIMESTAMP_DIFF		= 3


class DBConnector:
	
	def __init__(self):
		path = glob.glob(os.path.expanduser("~/.Zeitgeist/gzg.sqlite"))
		path = self.create_db(path)
		self.connection = sqlite3.connect(path[0], True)
		self.cursor = self.connection.cursor()
		self.offset = 0
	
	def create_db(self, path):
		if len(path) == 0:
			try:
				homedir = glob.glob(os.path.expanduser("~/"))
				dbdir = homedir[0] +".Zeitgeist"
				try:
					os.mkdir(dbdir)
				except:
					pass
				shutil.copy("gzg.sqlite", dbdir)	  
			except:
				print "Unexpected error creating database:", sys.exc_info()[0]	
			return glob.glob(os.path.expanduser("~/.Zeitgeist/gzg.sqlite"))
		else:
			return path
	
	def get_last_timestamp(self):
		query = "SELECT * FROM timetable LIMIT 1"
		result = self.cursor.execute(query).fetchone()
		if result is None:
			return 0
		else:
			return result[TIMESTAMP_BEGIN]
		
	def insert_items(self, items):
		for item in items:
			try:
				self.cursor.execute('INSERT INTO timetable VALUES (?,?,?,?,?)', (item.timestamp,
																				None,
																				item.uri,
																				item.use,
																				str(item.timestamp)+"-"+item.uri))
				try:
					self.cursor.execute('INSERT INTO data VALUES (?,?,?,?,?,?,?,?)', (item.uri,
																					item.name,
																					item.comment,
																					item.mimetype,
																					item.tags,
																					item.count,
																					item.use,
																					item.type))
					print "Wrote %s into the database." % item.uri
				except Exception, ex:
					print ex.__class__
					print "Error writing %s with timestamp %s." %(item.uri, item.timestamp)
			except sqlite3.IntegrityError, ex:
				pass
		self.connection.commit()

		   
	def get_items(self,min,max):
		for t in self.cursor.execute("SELECT start , end,  uri FROM timetable WHERE start >= "+ str(int(min)) + " and start <= " + str(int(max))+" ORDER BY key").fetchall():
			i = self.cursor.execute("SELECT * FROM data WHERE  uri=?",(t[2],)).fetchone()
			if i[6]!="linked":
				if i:
					yield Data(uri=i[0], 
					  timestamp= t[0], 
					  name= i[1], 
					  comment=i[2], 
					  mimetype=  i[3], 
					  tags=i[4], 
					  count=i[5], 
					  use =i[6], 
					  type=i[7])
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
		self.cursor.execute('DELETE FROM tags where uri=?', (item.uri,))
		 
		for tag in item.get_tags():
			if not tag.strip() == "":
				self.cursor.execute('INSERT INTO tags VALUES (?,?)',(tag,item.uri)) 			 
							
		self.connection.commit()
		 
	def get_most_tags(self,count=10):
		res = self.cursor.execute('SELECT tag, COUNT(uri) FROM tags GROUP BY tag ORDER BY COUNT(uri) DESC').fetchall()
		list = []
		for i in range(count):
			if i >= len(res):
				break
			yield res[i]
		
	def get_related_items(self,item):
		list = []
		items = self.cursor.execute('SELECT * FROM timetable WHERE uri=? ORDER BY start DESC',(item.uri,)).fetchall()
		type=item.type
		relevant=[]
		relevant2=[]
		for i in items:
			'''
			min and max define the neighbourhood radius
			'''
			min = i[0]-4500
			max = i[0]+4500
			
			priority=i[0]/time.time() 
			res = self.cursor.execute("SELECT  uri,start FROM timetable WHERE start >="+ str(min) + " and start <= " + str(max)).fetchall()
			for r in res:
				rtemp=float(abs(i[0]-r[1]))
				temp = (i[0]-rtemp)/i[0]
				temp=(temp-0.99999)*100000
				if temp > 0 and temp <1 and item.uri !=res[0] :
					relevant.append(r[0])
					relevant2.append(temp)
		
		
		list ={}
		while relevant != []:
			r = relevant[0]
			x =  1
			heat=0
			while relevant.count(r)>0:
				index = relevant.index(r)
				if relevant2[index]>heat:
					heat=relevant2[index]
					x+=1
				relevant.pop(index)
				relevant2.pop(index)
				
			if r  != item.uri:
				list[r]=[x,heat]

		values = [(v, k) for (k, v) in list.iteritems()]
		list.clear()
		values.sort()
		values.reverse()
		
		
		types=[]
		items=[]
		for index in range(len(values)):
			try:
				uri = values[index][1]
				i = self.cursor.execute("SELECT * FROM data WHERE uri=?",(uri,)).fetchone() 
				if i:
					if types.count(i[7]) <= 10:
						d= Data(uri=i[0],timestamp= -1.0, name= i[1], comment=i[2], mimetype=  i[3], tags=i[4], count=i[5], use =i[6], type=i[7])
						types.append(i[7])
						items.append(d)
			except:
				pass
		return items
		
		
	def numeric_compare(x, y):
		if x[0]>y[0]:
			return 1
		elif x[0]==y[0]:
			return 0
		else: # x<y
			return -1
 

db=DBConnector()
