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
			return result[0]
		
	def insert_items(self, items):
		for item in items:
			try:
				self.cursor.execute('INSERT INTO timetable VALUES (?,?,?,?,?)', (item.timestamp,
					None,
					item.uri,
					item.use,
					str(item.timestamp)+"-"+item.uri))
				try:
					self.cursor.execute('INSERT INTO data VALUES (?,?,?,?,?,?,?,?,?)', (item.uri,
						item.name,
						item.comment,
						item.mimetype,
						item.tags,
						item.count,
						item.use,
						item.type,
						item.icon))
						
				except Exception, ex:
					pass
					#print "---------------------------------------------------------------------------"					
					#print ex
					#print "Error writing %s with timestamp %s." %(item.uri, item.timestamp)
					#print "---------------------------------------------------------------------------"	
				
				try:
					# Add tags into the database
					# FIXME: Sometimes Data.tags is a string and sometimes it is a list.
					# TODO: Improve consistency.
					if item.tags != "" and item.tags != []:
						for tag in item.get_tags():
							self.cursor.execute('INSERT INTO tags VALUES (?,?,?)', (tag.capitalize(), item.uri,item.timestamp))
				except Exception, ex:
					print "Error inserting tags:"
					print ex

			except sqlite3.IntegrityError, ex:
					pass
		self.connection.commit()

		   
	def get_items(self,min,max):
		t1 = time.time()
		for t in self.cursor.execute("SELECT start, uri FROM timetable WHERE usage!='linked' and start >= "+ str(int(min)) + " and start <= " + str(int(max))+" ORDER BY key").fetchall():
			i = self.cursor.execute("SELECT * FROM data WHERE  uri=?",(t[1],)).fetchone()
			if i:
				  d = Data(uri=i[0], 
				  timestamp= t[0], 
				  name= i[1], 
				  comment=i[2], 
				  mimetype=  i[3], 
				  tags=i[4], 
				  count=i[5], 
				  use =i[6], 
				  type=i[7],
				  icon=i[8])
				  yield d 
		gc.collect()
		print time.time() -t1
	 
	def update_item(self,item):
		self.cursor.execute('DELETE FROM  data where uri=?',(item.uri,))
		self.cursor.execute('INSERT INTO data VALUES (?,?,?,?,?,?,?,?,?)',(item.uri,
																		item.name,
																		item.comment,
																		item.mimetype,
																		item.tags,
																		item.count,
																		item.use,
																		item.type,
																		item.icon))	
			
		self.cursor.execute('DELETE FROM tags where uri=?', (item.uri,))
		 
		for tag in item.get_tags():
			if not tag.strip() == "":
				try:
					self.cursor.execute('INSERT INTO tagids VALUES (?)',(tag,)) 
				except:
					pass
				id = self.cursor.execute("SELECT rowid FROM tagids WHERE  tag=?",(tag,)).fetchone()
				self.cursor.execute('INSERT INTO tags VALUES (?,?,?)',(id[0],item.uri,item.timestano)) 			 
							
		self.connection.commit()
		 
	def get_most_tags(self,count=20,min=0,max=sys.maxint):
		res = self.cursor.execute('SELECT tagid, COUNT(uri) FROM tags WHERE timestamp >='+ str(min) +" AND timestamp <="+ str(max) +' GROUP BY tagid ORDER BY  timestamp DESC').fetchall()
		
		i = 0
		while i < len(res) and i < count:
			#tag = self.cursor.execute('SELECT tag FROM tagids WHERE rowid=?', (res[i][0],)).fetchone()
			yield res[i][0]
			i += 1
		
	def get_related_items(self,item):
		list = []
		items = self.cursor.execute('SELECT * FROM timetable WHERE uri=? ORDER BY start DESC',(item.uri,)).fetchall()
		type=item.type
		relevant=[]
		relevant2=[]
		relevant3=[]
		for i in items:
			'''
			min and max define the neighbourhood radius
			'''
			min = i[0]-28800
			max = i[0]+28800
			res = self.cursor.execute("SELECT  uri,start FROM timetable WHERE start >="+ str(min) + " and start <= " + str(max)+" and uri!=? ORDER BY start",(item.uri,)).fetchall()
			for r in res:
				rtemp=float(abs(i[0]-r[1]))
				if rtemp < 1000:
					#temp = (i[0]-rtemp)/i[0]
					#temp=(temp-0.99999)*100000
					try:
						temp=1.0/rtemp**2
					except:
						temp = 1.0
					if item.uri !=res[0] :
						relevant.append(r[0])
						relevant2.append(temp)
						relevant3.append(r[1])
		
		
		list ={}
		while relevant != []:
			r = relevant[0]
			x =  1
			heat=0
			timestamp=0
			while relevant.count(r)>0:
				index = relevant.index(r)
				if relevant3[index]>timestamp:
					timestamp = relevant3[index]
				if relevant2[index]>heat:
					heat=relevant2[index]
				x+=1
					#print"----------------"
					#print heat
					#print timestamp
					#print x
					
				relevant.pop(index)
				relevant2.pop(index)
				relevant3.pop(index)
				
			if r  != item.uri:
				list[r]=[timestamp*2*heat*x]

		values = [(v, k) for (k, v) in list.iteritems()]
		list.clear()
		values.sort()
		values.reverse()
		
		for v in values:
			print v
		
		types=[]
		items=[]
		for index in xrange(20):
			try:
				uri = values[index][1]
				i = self.cursor.execute("SELECT * FROM data WHERE uri=?",(uri,)).fetchone() 
				if i:
						d= Data(uri=i[0],timestamp= -1.0, name= i[1], comment=i[2], mimetype=  i[3], tags=i[4], count=i[5], use =i[6], type=i[7])
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
