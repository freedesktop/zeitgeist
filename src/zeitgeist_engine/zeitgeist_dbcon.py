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
		path = os.path.expanduser("~/.Zeitgeist/gzg.sqlite")
		self.create_db(path)
		self.connection = sqlite3.connect(path, True, check_same_thread=False)
		self.cursor = self.connection.cursor()
		self.offset = 0
	
	def create_db(self, path):
		"""
		Create the database at path if it doesn't already exist.
		"""
		# If the database doesn't already exists
		if not os.path.isdir(os.path.dirname(path)):
			try:
				os.mkdir(os.path.dirname(path))
			except OSError, e:
				print 'Could not create the data directory: %s' % e.strerror
			else:
				# Copy the empty database skeleton into .Zeitgeist
				shutil.copy("gzg.sqlite", dbdir)	  
	
	def get_last_timestamp(self):
		"""
		Gets the timestamp of the most recent item in the database.
		
		Returns 0 if there are no items in the database.
		"""
		query = "SELECT * FROM timetable LIMIT 1"
		result = self.cursor.execute(query).fetchone()
		if result is None:
			return 0
		else:
			return result[0]

	def insert_items_threaded(self, items):
		"""
		Insert items into the database in a new thread.
		"""
		thread.start_new(self.insert_items, (items,))
		
	def insert_items(self, items):
		"""
		Inserts items into the database.
		
		Returns len(items)
		"""
		# TODO: Is there any reason to return len(items)?
		# Will changing this break other parts of the codebase?
		
		amount_items = 0
		for item in items:
			amount_items += 1
			try:
				self.cursor.execute('INSERT INTO timetable VALUES (?,?,?,?,?)',
					(item.timestamp,
					None,
					item.uri,
					item.use,
					str(item.timestamp)+"-"+item.uri))
				try:
					self.cursor.execute('INSERT INTO data VALUES (?,?,?,?,?,?,?,?,?,?)',
						(item.uri,
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
				
				try:
					# Add tags into the database
					# FIXME: Sometimes Data.tags is a string and sometimes it is a list.
					# TODO: Improve consistency.
					if item.tags != "" and item.tags != []:
						for tag in item.get_tags():
							self.cursor.execute('INSERT INTO tags VALUES (?,?,?)',
								(tag.capitalize(), item.uri, item.timestamp))
				except Exception, ex:
					print "Error inserting tags: %s" % ex

			except sqlite3.IntegrityError, ex:
				pass
				
		self.connection.commit()
		return amount_items
	
	def get_items(self, min, max):
		"""
		Yields all items from the database between the timestamps min and max.
		"""
		# Loop over all items in the timetable table which are between min and max
		query = """SELECT start, uri 
				FROM timetable
				WHERE usage!='linked'
				and start >= ?
				and start <= ?
				ORDER BY key"""
		
		for start, uri in self.cursor.execute(query, (str(int(min)), str(int(max)))).fetchall():
			
			# Retrieve the item from the data table
			item = self.cursor.execute("SELECT * FROM data WHERE  uri=?",
									(uri,)).fetchone()
			
			# TODO: Can item ever be None?
			if item is not None:
				# Check if the item is bookmarked
				if item[9] == 1:
					bookmark = True
				else:
					bookmark = False
				
				yield Data(uri  = item[0],
					name		= item[1],
			 		comment		= item[2],
			 		mimetype	= item[3],
					tags		= item[4],
					count		= item[5],
					use			= item[6],
					type		= item[7],
					icon		= item[8],
					timestamp   = start,
					bookmark	= bookmark)
		
		gc.collect()
	
	def update_item(self, item):
		"""
		Updates an item already in the database.
		
		If the item has tags, then the tags will also be updated.
		"""
		# Delete this item from the database if it's already present.
		self.cursor.execute('DELETE FROM data where uri=?',(item.uri,))
		
		# Check if the item is bookmarked
		if item.bookmark == True:
			bookmark = 1
		else:
			bookmark = 0
		
		# (Re)insert the item into the database
		self.cursor.execute('INSERT INTO data VALUES (?,?,?,?,?,?,?,?,?,?)',
							(item.uri,
							item.name,
							item.comment,
							item.mimetype,
							unicode(item.tags),
							item.count,
							item.use,
							item.type,
							item.icon,
							bookmark))	
		
		# Delete old tags for this item
		self.cursor.execute('DELETE FROM tags where uri=?', (item.uri,))
		
		# (Re)insert tags into the database
		for tag in item.get_tags():
			if not tag.strip() == "":
				try:
					self.cursor.execute('INSERT INTO tagids VALUES (?)',(tag,)) 
				except:
					pass
				self.cursor.execute('INSERT INTO tags VALUES (?,?,?)',
					(unicode(tag.capitalize()),item.uri,time.time())) 	
		self.connection.commit()
		 
	def get_recent_tags(self, count=20, min=0, max=sys.maxint):
		"""
		Yields tags between the timestamps min and max.
		
		At most, count tags will be yielded.
		"""
		res = self.cursor.execute("""SELECT tagid, COUNT(uri)
									FROM tags
									WHERE timestamp >= ?
									AND timestamp <= ?
									GROUP BY tagid
									ORDER BY timestamp DESC
									LIMIT ?""",
									(str(min), str(max), str(count))).fetchall()
		
		for tagid, tagcount in res:
			yield str(tagid)
			
	def get_most_tags(self, count=20, min=0, max=sys.maxint):
		"""
		Yields the tags between min and max which are used the most often.
		
		At most, count tags will be yielded.
		"""
		res = self.cursor.execute("""SELECT tagid, COUNT(uri)
									FROM tags
									WHERE timestamp >= ?
									AND timestamp <= ?
									GROUP BY tagid
									ORDER BY COUNT(uri) DESC
									LIMIT ?""",
									(str(min), str(max), str(count))).fetchall()
		
		for tagid, tagcount in res:
			yield str(tagid)
			
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
