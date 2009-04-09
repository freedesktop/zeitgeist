import shutil
import sqlite3
import tempfile
import re
import glob
import sys
import gc
import os
import time
import thread

# Imports from zeitgeist_engine
from zeitgeist_base import DataProvider, Data

class DBConnector():
	
	def __init__(self):
		path = glob.glob(os.path.expanduser("~/.Zeitgeist/gzg.sqlite"))
		path = self.create_db(path)
		self.connection = sqlite3.connect(path[0], True, check_same_thread=False)
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

	def insert_items_threaded(self,items):
		thread.start_new(self.insert_items, (items,))
		
	def insert_items(self, items):
		amount_items = 0
		for item in items:
			amount_items += 1
			try:
				self.cursor.execute('INSERT INTO timetable VALUES (?,?,?,?,?)', (item.timestamp,
					None,
					item.uri,
					item.use,
					str(item.timestamp)+"-"+item.uri))
				try:
					self.cursor.execute('INSERT INTO data VALUES (?,?,?,?,?,?,?,?,?,?)', (item.uri,
						item.name,
						item.comment,
						item.mimetype,
						item.tags,
						item.count,
						item.use,
						item.type,
						item.icon,
						0))
						
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
		return amount_items
	
	def get_items(self,min,max):
		t1 = time.time()
		for t in self.cursor.execute("SELECT start, uri FROM timetable WHERE usage!='linked' and start >= "+ str(int(min)) + " and start <= " + str(int(max))+" ORDER BY key").fetchall():
			i = self.cursor.execute("SELECT * FROM data WHERE  uri=?",(t[1],)).fetchone()
			if i:
				bookmark = False
				if i[9] ==1:
					bookmark=True
				
				d = Data(uri=i[0],
					timestamp=t[0],
					name=i[1],
			 		comment=i[2],
			 		mimetype=i[3],
					tags=i[4],
					count=i[5],
					use=i[6],
					type=i[7],
					icon=i[8],
					bookmark=bookmark)
				yield d 
		gc.collect()
		print time.time() -t1
	
	def update_item(self,item):
		self.cursor.execute('DELETE FROM  data where uri=?',(item.uri,))
		bookmark = 0
		if item.bookmark == True:
			bookmark = 1
				
		self.cursor.execute('INSERT INTO data VALUES (?,?,?,?,?,?,?,?,?,?)',(item.uri,
																		item.name,
																		item.comment,
																		item.mimetype,
																		unicode(item.tags),
																		item.count,
																		item.use,
																		item.type,
																		item.icon,
																		bookmark))	
		
		self.cursor.execute('DELETE FROM tags where uri=?', (item.uri,))
		
		for tag in item.get_tags():
			if not tag.strip() == "":
				try:
					self.cursor.execute('INSERT INTO tagids VALUES (?)',(tag,)) 
				except:
					pass
				#id = self.cursor.execute("SELECT rowid FROM tagids WHERE  tag=?",(tag,)).fetchone()
				self.cursor.execute('INSERT INTO tags VALUES (?,?,?)',(unicode(tag.capitalize()),item.uri,time.time())) 	
		self.connection.commit()
		 
	def get_recent_tags(self,count=20,min=0,max=sys.maxint):
		res = self.cursor.execute('SELECT tagid, COUNT(uri) FROM tags WHERE timestamp >='+ str(min) +" AND timestamp <="+ str(max) +' GROUP BY tagid ORDER BY  timestamp DESC').fetchall()
		
		i = 0
		while i < len(res) and i < count:
			#tag = self.cursor.execute('SELECT tag FROM tagids WHERE rowid=?', (res[i][0],)).fetchone()
			#print res[i][0]
			yield str(res[i][0])
			i += 1
			
	def get_most_tags(self,count=20,min=0,max=sys.maxint):
		res = self.cursor.execute('SELECT tagid, COUNT(uri) FROM tags WHERE timestamp >='+ str(min) +" AND timestamp <="+ str(max) +' GROUP BY tagid ORDER BY COUNT(uri) DESC').fetchall()
		i = 0
		while i < len(res) and i < count:
			#print res[i][0]
			#tag = self.cursor.execute('SELECT tag FROM tagids WHERE rowid=?', (res[i][0],)).fetchone()
			yield str(res[i][0])
			i += 1
			
	def get_min_timestamp_for_tag(self,tag):
		res = self.cursor.execute('SELECT timestamp FROM tags WHERE tagid = ? ORDER BY timestamp',(tag,)).fetchone()
		if res:
			return res[0]
		else:
			return None
			
	def get_max_timestamp_for_tag(self,tag):
		res = self.cursor.execute('SELECT timestamp FROM tags WHERE tagid = ? ORDER BY timestamp DESC',(tag,)).fetchone()
		if res:
			return res[0]
		else:
			return None
		
	def get_items_related_by_tags(self,item):
		for tag in item.get_tags():
			print tag
			res = self.cursor.execute('SELECT uri FROM tags WHERE tagid = ? ORDER BY COUNT(uri) DESC',(tag,)).fetchall()
			for raw in res:
				print raw
				i = self.cursor.execute("SELECT * FROM data WHERE  uri=?",(raw[0],)).fetchone()
				if i:
					bookmark = False
					if i[9] ==1:
						bookmark=True
					
					d = Data(uri=i[0], 
				 		name= i[1], 
				  		comment=i[2], 
				  		mimetype=  i[3], 
				        tags=i[4], 
				  		count=i[5], 
				  		use =i[6], 
				  		type=i[7],
				  		icon=i[8],
				  		bookmark=bookmark)
					yield d 
		
	def get_related_items(self, item):
		''' Parameter item may be a Data object or the URL of an item. '''
		list = []
		dict = {}
		current_timestamp = time.time() - (90*24*60*60)
		item_uri = item.uri if isinstance(item, Data) else item
		items = self.cursor.execute('SELECT * FROM timetable WHERE start >? AND uri=? ORDER BY start DESC',(current_timestamp,item_uri)).fetchall()
		for uri in items:
			'''
			min and max define the neighbourhood radius
			'''
			min = uri[0]-(60*60)
			max = uri[0]+(60*60)
			
			res = self.cursor.execute("SELECT uri FROM timetable WHERE start >=? and start <=? and uri!=?" ,(min,max,uri[2])).fetchall()
			
			for r in res:
				if dict.has_key(r[0]):
					dict[r[0]]=dict[r[0]]+1
				else:
					dict[r[0]]=0
		
		
		print"-----------------------------------------------------------------------------------------------"
		values = [(v, k) for (k, v) in dict.iteritems()]
		dict.clear()
 		values.sort()
 		values.reverse()
		print"-----------------------------------------------------------------------------------------------"
			
		counter =0
		for v in values:
			uri=v[1]
			i = self.cursor.execute("SELECT * FROM data WHERE uri=?",(uri,)).fetchone() 
			if i:
				if counter <= 5:
					d= Data(uri=i[0],timestamp= -1.0, name= i[1], comment=i[2], mimetype=  i[3], tags=i[4], count=i[5], use =i[6], type=i[7])
					list.append(d) 
					counter = counter +1
			
		return list
		
	def numeric_compare(x, y):
		if x[0]>y[0]:
			return 1
		elif x[0]==y[0]:
			return 0
		else: # x<y
			return -1
 
		
	def get_bookmarked_items(self):
		t1 = time.time()
		for i in self.cursor.execute("SELECT * FROM data WHERE boomark=1").fetchall():
				if i:
					d = Data(uri=i[0], 
				 		timestamp= -1, 
				 		name= i[1], 
				  		comment=i[2], 
				  		mimetype=  i[3], 
				        tags=i[4], 
				  		count=i[5], 
				  		use =i[6], 
				  		type=i[7],
				  		icon=i[8],
				  		bookmark=True)
				yield d 
		gc.collect()
		print time.time() -t1


db=DBConnector()
