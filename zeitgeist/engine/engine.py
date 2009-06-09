# -.- encoding: utf-8 -.-

import time
import sys
import os
import gc
import shutil
import sqlite3
import gettext
import gobject
from xdg import BaseDirectory

from zeitgeist import config
from zeitgeist.shared.zeitgeist_shared import *
from zeitgeist.engine.base import *

class ZeitgeistEngine(gobject.GObject):
	
	def __init__(self):
		
		gobject.GObject.__init__(self)
		self.reload_callback = None
		'''
		path = BaseDirectory.save_config_path("zeitgeist")
		database = os.path.join(path, "zeitgeist.sqlite")
		self.connection = self._get_database(database)
		self.cursor = self.connection.cursor()
		'''
		self._apps = set()
	
	def _result2data(self, result, timestamp=0, app="", usage=""):
		
		'''
		Get Tags
		'''
		# FIXME: Get tag
		tags = ""
		
		#FIXME: Get bookmark
		bookmark = False
		
		return (
			timestamp,
			store.find(URI.value, URI.id == result.id), # uri
			result.text, # name
			store.find(URI.value, URI.id == Item.id) or "N/A", # type
			result.mimetype, # mimetype
			tags, # tags
			"", # comment
			usage, # use
			bookmark, # bookmark
			result.icon, # icon
			app, # app
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
		if hasattr(item, "capitalize"):
			if uri_only:
				return item
			else:
				item = self.get_item(item)
		elif uri_only:
			return item["uri"]
		
		return item
	
	def _get_database(self, database):
		"""
		Return a connection to the indicated SQLite 3 database. If
		it doesn't already exist, create it. If something fails, abort
		the execution with error code 1.
		"""
		
		if not os.path.isfile(database):
			try:
				# Copy the empty database skeleton into .zeitgeist
				shutil.copy("%s/zeitgeist.sqlite" % config.pkgdatadir, database)
			except OSError, e:
				print _("Could not create database: %s") % e.strerror
				sys.exit(1)
		
		try:
			connection = sqlite3.connect(database, True,
				check_same_thread = False)
		except sqlite3.OperationalError, error:
			print _("Error connecting with database: %s") % error
			sys.exit(1)
		else:
			return connection
	
	def get_last_timestamp(self, uri=None):
		"""
		Gets the timestamp of the most recent item in the database. If
		`uri' is not empty, it will give the last timestamp for the
		indicated URI.
		
		Returns 0 if there are no items in the database.
		"""
		return 0
	
	def insert_item(self, ritem):
		"""
		Inserts an item into the database. Returns True on success,
		False otherwise (for example, if the item already is in the
		database).
		"""
		try:
		
			'''
			Init Source
			'''
			source = store.find(Source, Source.value == ritem["source"]).one()
			if not source:
				source = Source(ritem["source"])
				store.add(source)
			
			'''
			Init URI
			'''		
			uri = store.find(URI, URI.value == unicode(ritem["uri"])).one()
			if not uri:
				uri = URI(ritem["uri"])
				store.add(uri)
				
			'''
			Init Content
			'''		
			content = store.find(Content, Content.value == unicode(ritem["content"])).one()
			if not content:
				content = Content(ritem["content"])
				store.add(content)
			
			'''
			Init Item
			'''
			item = store.find(Item, Item.id == uri.id).one()
			if not item:
				item = Item(uri)
				item.content = content.id
				item.source = source.id
				item.text = ritem["text"]
				item.mimetype = ritem["mimetype"]
				item.icon = ritem["icon"]
				store.add(item)
				
			'''
			Init Event
			'''
			e_uri = "zeitgeist://event/"+ritem["use"]+"/"+str(uri.id)+"/"+str(ritem["timestamp"])
			event = store.find(URI, URI.value == e_uri).one()
			if not event:
				event = Event(e_uri, item.uri.value)
				event.start = ritem["timestamp"]
				event.end = ritem["timestamp"]
				event.item.text = u"Activity"
				
				'''
				Init Event.content
				'''
				source = store.find(Source, Source.value == u"http://gnome.org/zeitgeist/schema/Event#activity").one()
				if not source:
					source = Source(u"http://gnome.org/zeitgeist/schema/Event#activity")
				event.item.source = source
				'''
				Init Event.content
				'''
				content = store.find(Content, Content.value == ritem["use"]).one()
				if not content:
					content = Content(ritem["use"])
				event.item.content = content				
				'''
				Init Event.app
				'''
				app = store.find(URI,URI.value == ritem["app"]).one()
				if not app:
					app = App(ritem["app"])
					app.value = ritem["app"]
					app.item.text = u"Application"
					store.add(app)
				else:
					app = store.find(App,App.item_id == app.id).one()
				event.app_id = app.item_id

				store.add(event)
				
				del event, app, uri, content, source, item, e_uri
			
		except Exception, ex:
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
		
		#self.connection.commit()
		store.commit()
		gc.collect()
		print "DONE"
		print "got items"
		
		return amount_items
	
	def get_item(self, uri):
		"""Returns basic information about the indicated URI."""
		
		id = store.find(URI, URI.value == uri)
		item = store.find(Item, Item)
		
		if item:
			return self._result2data(item)
	
	
	def get_items(self, min=0, max=sys.maxint, tags="", mimetypes=""):
		"""
		Yields all items from the database between the indicated
		timestamps `min' and `max'. Optionally the argument `tags'
		may be used to filter on tags.
		"""
		func = self._result2data
		pack = []
		# Emulate optional arguments for the D-Bus interface
		if not max: max = sys.maxint
		
		for event in store.find(Event, Event.start >= min, Event.start <= max):
			start = event.start
			
			usage_id = store.find(URI, URI.id == event.item_id).one()
			usage = store.find(Item.content_id, Item.id == usage_id.id).one()
			usage = store.find(Content.value, Content.id == usage).one()
			
			item = store.find(Item, Item.id == event.subject_id).one()
			
			app= ""
			
			if item:
				pack.append(func(item, timestamp = start, usage=usage, app=app))
		return pack
	
	def update_item(self, item):
		"""
		Updates an item already in the database.
		
		If the item has tags, then the tags will also be updated.
		"""
		# Delete this item from the database if it's already present.
		self.cursor.execute('DELETE FROM data where uri=?',(item["uri"],))
		
		# (Re)insert the item into the database
		self.cursor.execute('INSERT INTO data VALUES (?,?,?,?,?,?,?)',
							 (item["uri"],
								unicode(item["name"]),
								item["comment"],
								item["icon"],
								item["bookmark"],
								item["mimetype"],
								item["type"]))
		self.connection.commit()
		
		# Delete old tags for this item
		self.cursor.execute('DELETE FROM tags where uri=?', (item["uri"],))
		
		# (Re)insert tags into the database
		for tag in (tag.strip() for tag in item["tags"].split(",") if tag.strip()):
			try:
				self.cursor.execute('INSERT INTO tags VALUES (?,?)',
					(unicode(tag.capitalize()), item["uri"]))
			except sqlite3.IntegrityError:
				pass
		self.connection.commit()
	
	def delete_item(self, item):
		pass
	
	def _get_tags(self, order_by, count, min, max):
		"""
		Private class used to retrive a list of tags according to a
		desired condition (eg., most used tags, recently used tags...).
		"""
		return []
	
	def get_all_tags(self):
		"""
		Returns a list containing the name of all tags.
		"""
		return []
	
	def get_types(self):
		"""
		Returns a list of all different types in the database.
		"""
		
		for type, icon in self.cursor.execute(
		"SELECT DISTINCT(type), icon FROM data").fetchall():
			yield(unicode(type), icon)
	
	def get_recently_used_tags(self, count=20, min=0, max=sys.maxint):
		"""
		Returns a list containing up to `count' recently used
		tags from between timestamps `min' and `max'.
		"""
		
		return self._get_tags("key", count, min, max)
	
	def get_most_used_tags(self, count=20, min=0, max=sys.maxint):
		"""
		Returns a list containing up to the `count' most used
		tags from between timestamps `min' and `max'.
		"""
		
		return self._get_tags("uri", count, min, max)
	
	def get_min_timestamp_for_tag(self, tag):
			return None
	
	def get_max_timestamp_for_tag(self, tag):
			return None
	
	def get_timestamps_for_tag(self, tag):
		pass
	
	def get_items_related_by_tags(self, item):
		# TODO: Is one matching tag enough or should more/all of them
		# match?
		pass
	
	def get_related_items(self, uri):
		pass
	
	def compare_nbhs(self,nbhs):
		pass
	
	def get_items_with_mimetype(self, mimetype, min=0, max=sys.maxint, tags=""):
		pass
	
	def get_uris_for_timestamp(self, timestamp):
		pass
	
	def get_bookmarks(self):
		print "xxxxxxxxxxxxxxxxxxxx"
		return []

engine = ZeitgeistEngine()
