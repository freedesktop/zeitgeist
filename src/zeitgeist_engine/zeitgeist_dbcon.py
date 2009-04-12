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
from zeitgeist_engine.zeitgeist_base import DataProvider, Data

class DBConnector():
	
	def __init__(self):
		path = os.path.expanduser("~/.Zeitgeist/gzg.sqlite")
		self.create_db(path)
		self.connection = sqlite3.connect(path, True, check_same_thread=False)
		self.cursor = self.connection.cursor()
		self.offset = 0
	
	def _result2data(self, result, timestamp=0):
		return Data(
			uri			= result[0],
			name		= result[1],
			comment		= result[2],
			mimetype	= result[3],
			tags		= result[4],
			count		= result[5],
			use			= result[6],
			type		= result[7],
			icon		= result[8],
			bookmark	= (result[9] == 1),
			timestamp	= timestamp
			)
	
	def _ensure_item(self, item, uri_only=False):
		"""
		Takes either a Data object or an URI for an item in the
		database. If it's a Data object it is returned unchanged,
		but if it's an URI it's looked up in the database and the
		its returned converted into a complete Data object.
		
		If uri_only is True, only the URI of the item is returned
		(and no database query needs to take place).
		"""
		
		if type(item) is str:
			if uri_only:
				return item
			else:
				item = self._result2data(
					self.cursor.execute(
						"SELECT * FROM data WHERE uri=?", (item,)).fetchone())
		elif uri_only:
			return item.uri
		
		return item
	
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
				shutil.copy("data/gzg.sqlite", path)	  
	
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
		Inserts items into the database in a new thread.
		"""
		thread.start_new(self.insert_items, (items,))
	
	def insert_item(self, item):
		"""
		Inserts an item into the database. Returns True on success,
		False otherwise (for example, if the item already is in the
		database).
		"""
		
		try:
			# Insert into timetable
			self.cursor.execute('INSERT INTO timetable VALUES (?,?,?,?,?)',
				(item.timestamp,
				None,
				item.uri,
				item.use,
				"%s-%s" % (str(item.timestamp), item.uri)))
			
			# Insert into data, if it isn't there yet
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
			except sqlite3.IntegrityError, ex:
				pass
			
			try:
				# Add tags into the database
				# FIXME: Sometimes Data.tags is a string and sometimes it is a list.
				# TODO: Improve consistency.
				for tag in item.get_tags():
					self.cursor.execute('INSERT INTO tags VALUES (?,?,?)',
						(tag.capitalize(), item.uri, item.timestamp))
			except Exception, ex:
				print "Error inserting tags: %s" % ex
		
		except sqlite3.IntegrityError, ex:
			return False
		
		else:
			return True
	
	def insert_items(self, items):
		"""
		Inserts items into the database and returns the amount of
		items it inserted.
		"""
		
		amount_items = 0
		for item in items:
			if self.insert_item(item):
				amount_items += 1
		
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
			item = self.cursor.execute("SELECT * FROM data WHERE uri=?",
									(uri,)).fetchone()
			
			# TODO: Can item ever be None?
			if item is not None:
				itemobj = self._result2data(item, timestamp = start)
				yield itemobj
		
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
	
	def delete_item(self, item):
		item_uri = self._ensure_item(item, uri_only=True)
		self.cursor.execute('DELETE FROM data where uri=?', (item_uri,))
		self.cursor.execute('DELETE FROM tags where uri=?', (item_uri,))
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
	
	def get_items_related_by_tags(self, item):
		# TODO: Is one matching tag enough or should more/all of them
		# match?
		for tag in self._ensure_item(item).get_tags():
			res = self.cursor.execute('SELECT uri FROM tags WHERE tagid=? GROUP BY uri ORDER BY COUNT(uri) DESC', (tag,)).fetchall()
			for raw in res:
				item = self.cursor.execute("SELECT * FROM data WHERE uri=?", (raw[0],)).fetchone()
				if item:
					yield self._result2data(item)
	
	def get_related_items(self, item):
		# TODO: Only neighboorhood in time is considered? A bit poor,
		# this needs serious improvement.
		list = []
		dict = {}
		current_timestamp = time.time() - (90*24*60*60)
		item_uri = self._ensure_item(item, uri_only=True)
		items = self.cursor.execute('SELECT * FROM timetable WHERE start >? AND uri=? ORDER BY start DESC',(current_timestamp,item_uri)).fetchall()
		for uri in items:
			# min and max define the neighbourhood radius
			min = uri[0]-(60*60)
			max = uri[0]+(60*60)
			
			res = self.cursor.execute("SELECT uri FROM timetable WHERE start >=? and start <=? and uri!=?" ,(min,max,uri[2])).fetchall()
			
			for r in res:
				if dict.has_key(r[0]):
					dict[r[0]]=dict[r[0]]+1
				else:
					dict[r[0]]=0
		
		values = [(v, k) for (k, v) in dict.iteritems()]
		dict.clear()
 		values.sort()
 		values.reverse()
 		
		counter = 0
		for v in values:
			uri = v[1]
			item = self.cursor.execute("SELECT * FROM data WHERE uri=?",(uri,)).fetchone() 
			if item:
				if counter <= 5:
					d = self._result2data(item, timestamp = -1)
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
		for item in self.cursor.execute("SELECT * FROM data WHERE boomark=1").fetchall():
				if item:
					d = self._result2data(item, timestamp = -1)
				yield d 
		gc.collect()
		print time.time() - t1


db = DBConnector()
