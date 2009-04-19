import shutil
import sqlite3
import sys
import gc
import os

from zeitgeist_engine.zeitgeist_base import DataProvider
from zeitgeist_shared.basics import BASEDIR

class DBConnector:
    
    def __init__(self):
        path = os.path.expanduser("~/.zeitgeist/gzg.sqlite")
        self.create_db(path)
        self.connection = sqlite3.connect(path, True, check_same_thread=False)
        self.cursor = self.connection.cursor()
    
    def _result2data(self, result, timestamp=0):
        
        return (
            timestamp,
            result[0], # uri
            result[1], # name
            result[2], # comment
            result[3], # tags
            result[4] or "first use", # use
            result[5], # icon
            result[6], # bookmark
            result[7] or "N/A", # mimetype
            result[8] or 1, # count
            result[9] or "N/A", # type
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
        
        # Is it a string (can be str, dbus.String, etc.)?
        if hasattr(item, 'capitalize'):
            if uri_only:
                return item
            else:
                item = self._result2data(
                    self.cursor.execute(
                        "SELECT * FROM data WHERE uri=?", (item,)).fetchone())
        elif uri_only:
            return item["uri"]
        
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
                # Copy the empty database skeleton into .zeitgeist
                shutil.copy("%s/data/gzg.sqlite" % BASEDIR, path)
    
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
    
    def insert_item(self, item):
        """
        Inserts an item into the database. Returns True on success,
        False otherwise (for example, if the item already is in the
        database).
        """
        
        try:
            # Insert into timetable
            self.cursor.execute('INSERT INTO timetable VALUES (?,?,?,?,?)',
                (item["timestamp"],
                None,
                item["uri"],
                item["use"],
                "%d-%s" % (item["timestamp"], item["uri"])))
            
            # Insert into data, if it isn't there yet
            try:
                self.cursor.execute('INSERT INTO data VALUES (?,?,?,?,?,?,?,?,?,?)',
                    (item["uri"],
                    unicode(item["name"]),
                    item["comment"],
                    item["tags"],
                    item["use"],
                    item["icon"],
                    0,
                    item["mimetype"],
                    item["count"],
                    unicode(item["type"])))
            except sqlite3.IntegrityError, ex:
                pass
            
            try:
                # Add tags into the database
                # FIXME: Sometimes Data.tags is a string and sometimes it is a list.
                # TODO: Improve consistency.
                for tag in (tag.strip() for tag in item["tags"].split(",") if tag.strip()):
                    self.cursor.execute('INSERT INTO tags VALUES (?,?)',
                        (tag.capitalize(), item["uri"]))
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
        
        func = self._result2data
        for start, uri in self.cursor.execute(query, (str(int(min)), str(int(max)))).fetchall():
            # Retrieve the item from the data table
            item = self.cursor.execute("SELECT * FROM data WHERE uri=?",
                                    (uri,)).fetchone()
            
            # TODO: Can item ever be None?
            if item:
                yield func(item, timestamp = start)
    
    def update_item(self, item):
        """
        Updates an item already in the database.
        
        If the item has tags, then the tags will also be updated.
        """
        # Delete this item from the database if it's already present.
        self.cursor.execute('DELETE FROM data where uri=?',(item["uri"],))
        
        # (Re)insert the item into the database
        	
        self.cursor.execute('INSERT INTO data VALUES (?,?,?,?,?,?,?,?,?,?)',
                             (item["uri"],
			                    unicode(item["name"]),
			                    item["comment"],
			                    item["tags"],
			                    item["use"],
			                    item["icon"],
			                    item["bookmark"],
			                    item["mimetype"],
			                    item["count"],
			                    item["type"]))
        self.connection.commit()
        
        # Delete old tags for this item
        self.cursor.execute('DELETE FROM tags where uri=?', (item["uri"],))
        
        # (Re)insert tags into the database
        for tag in (tag.strip() for tag in item["tags"].split(",") if tag.strip()):
            self.cursor.execute('INSERT INTO tags VALUES (?,?)',
                (unicode(tag.capitalize()), item["uri"]))     
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
        
        uris = [] 
        tags = []
        
        # Get uri's in in time intervall sorted desc by time
    	query = """SELECT  uri 
                FROM timetable
                WHERE usage!='linked'
                and start >= ?
                and start <= ?
                ORDER BY key DESC"""
        
        for uri in self.cursor.execute(query, (str(int(min)), str(int(max)))).fetchall():
            	# Retrieve the item from the data table:
         	uri = uri[0]
		if uris.count(uri) <= 0 and len(tags) < count:
			uris.append(uri)
       		uri = self.cursor.execute("SELECT * FROM data WHERE uri=?",
                                   (uri,)).fetchone()
		if uri:
			res = self.cursor.execute("""SELECT tagid
        	                    	FROM tags
        	                    	WHERE uri = ?""",
                                    (uri[0],)).fetchall()
       	                            
       			for tag in res:
				if tags.count(tag) <= 0:
   					if len(tags) < count:
       						tags.append(tag)
       						yield str(tag[0])
       		  			
    def get_items_for_tag(self,tag):
        """
        Gets all of the items with tag.
        """
        func = self._result2data
        res = self.cursor.execute("""SELECT uri
                                    FROM tags
                                    WHERE tagid= ?
                                    """,
                                    (tag,)).fetchall()
        
        for uri in res:
	        item = self.cursor.execute("SELECT * FROM data WHERE uri=?",(uri[0],)).fetchone()
	       	if item:
	       			yield func(item, timestamp = -1)
	    
    def get_most_tags(self, count=20, min=0, max=sys.maxint):
        """
        Yields the tags between min and max which are used the most often.
        
        At most, count tags will be yielded.
        """
        
        uris = [] 
        tags = []
        
        # Get uri's in in time intervall sorted desc by time
    	query = """SELECT  uri 
                FROM timetable
                WHERE usage!='linked'
                and start >= ?
                and start <= ?
                ORDER BY uri DESC"""
        
        for uri in self.cursor.execute(query, (str(int(min)), str(int(max)))).fetchall():
            	# Retrieve the item from the data table:
         	uri = uri[0]
		if uris.count(uri) <= 0 and len(tags) < count:
			uris.append(uri)
       		uri = self.cursor.execute("SELECT * FROM data WHERE uri=?",
                                   (uri,)).fetchone()
		if uri:
			res = self.cursor.execute("""SELECT tagid
        	                    	FROM tags
        	                    	WHERE uri = ?
                                    ORDER BY tagid
                                    """,
                                    (uri[0],)).fetchall()
       	                            
       			for tag in res:
				if tags.count(tag) <= 0:
   					if len(tags) < count:
       						tags.append(tag)
       						yield str(tag[0])
              					
    def get_min_timestamp_for_tag(self,tag):
    	timestamp = sys.maxint
        res = self.cursor.execute('SELECT uri FROM tags WHERE tagid = ?',(tag,)).fetchall()
        if res:
        	for uri in res:
			res = self.cursor.execute('SELECT start FROM timetable WHERE uri=? ORDER BY start ',(uri[0],)).fetchone()
			if res[0] < timestamp:
				timestamp = res[0]
		return timestamp
        else:
            return None
    
    def get_max_timestamp_for_tag(self,tag):
        timestamp = 0
        res = self.cursor.execute('SELECT uri FROM tags WHERE tagid = ?',(tag,)).fetchall()
        if res:
        	for uri in res:
			res = self.cursor.execute('SELECT start FROM timetable WHERE uri=? ORDER BY start DESC',(uri[0],)).fetchone()
			if res[0] > timestamp:
				timestamp = res[0]
		return timestamp
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
       
    	for i in self.get_items_related_by_tags():
    		yield i
    
        '''
        list = []
        dict = {}
        current_timestamp = time.time() - (90*24*60*60)
        item_uri = self._ensure_item(item, uri_only=True)
        items = self.cursor.execute("SELECT * FROM timetable WHERE start >? AND uri=? ORDER BY start DESC",
            (current_timestamp, item_uri)).fetchall()
        for uri in items:
            # min and max define the neighbourhood radius
            min = uri[0]-(60*60)
            max = uri[0]+(60*60)
            
            res = self.cursor.execute("SELECT uri FROM timetable WHERE start >=? and start <=? and uri!=?",
                (min, max, uri[2])).fetchall()
            
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
            item = self.cursor.execute("SELECT * FROM data WHERE uri=?",
                (uri,)).fetchone() 
            if item:
                if counter <= 5:
                    d = self._result2data(item, timestamp = -1)
                    list.append(d) 
                    counter = counter +1
            
        return list
       	'''
       	
    def get_bookmarked_items(self):
        for item in self.cursor.execute("SELECT * FROM data WHERE boomark=1").fetchall():
            yield self._result2data(item, timestamp = -1)
        

db = DBConnector()
