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

import traceback
from random import randint

from zeitgeist import config
from zeitgeist.shared.zeitgeist_shared import *
from zeitgeist.engine.base import *

class ZeitgeistEngine(gobject.GObject):
	_salt = 0

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
	
	def _next_salt(self):
		self._salt += 1
		return self._salt

	def get_last_timestamp(self, uri=None):
		"""
		Gets the timestamp of the most recent item in the database. If
		`uri' is not empty, it will give the last timestamp for the
		indicated URI.
		
		Returns 0 if there are no items in the database.
		"""
		return 0
	
	def insert_item(self, ritem, commit=True):
		"""
		Inserts an item into the database. Returns True on success,
		False otherwise (for example, if the item already is in the
		database).
		"""
		
		if not ritem.has_key("uri") or not ritem["uri"]:
			print >> sys.stderr, "Discarding item without a URI: %s" % ritem
			return False
		if not ritem.has_key("content") or not ritem["content"]:
			print >> sys.stderr, "Discarding item without a Content type: %s" % ritem
			return False
		if not ritem.has_key("source") or not ritem["source"]:
			print >> sys.stderr, "Discarding item without a Source type: %s" % ritem
			return False
		
		try:
			# The item may already exist in the db,
			# so only create it if necessary
			item = Item.lookup_or_create(ritem["uri"])
			item.content = Content.lookup_or_create(ritem["content"])
			item.source = Source.lookup_or_create(ritem["source"])
			item.text = unicode(ritem["text"])
			item.mimetype = unicode(ritem["mimetype"])
			item.icon = unicode(ritem["icon"])
			item.origin = ritem["origin"]
		except sqlite3.IntegrityError, ex:
			traceback.print_exc()
			print >> sys.stderr, "Failed to insert item:\n%s" % ritem
			print >> sys.stderr, "Error was: %s" % ex			
			return False
		
		# Store a new event for this
		try:			
			e_uri = "zeitgeist://event/"+ritem["use"]+"/"+str(item.id)+"/"+str(ritem["timestamp"]) + "#" + str(self._next_salt())
			e = Event.lookup_or_create(e_uri)
			e.subject = item
			e.start = ritem["timestamp"]
			e.item.text = u"Activity"
			e.item.source_id = Source.USER_ACTIVITY.id
			e.item.content = Content.lookup_or_create(ritem["use"])
			
			#FIXME: Lots of info from the applications, try to sort them out here properly
			
			app_info = resolve_dot_desktop(ritem["app"])
			
			e.app = App.lookup_or_create(ritem["app"])
			#print app_info
			e.app.item.text = unicode(app_info["name"])
			e.app.item.content = Content.lookup_or_create(app_info["type"])
			e.app.item.source = Source.lookup_or_create(app_info["exec"])
			e.app.item.icon = unicode(app_info["icon"])
			e.app.info = unicode(ritem["app"]) # FIXME: App constructor could parse out appliction name from .desktop file
			if app_info.has_key("categories") and app_info["categories"].strip() != "":			
				# Iterate over non-empty strings only
				for tag in filter(lambda t : bool(t), app_info["categories"].split(";")):
					print "TAG:", tag
					a_uri = "zeitgeist://tag/%s" % tag
					a = Annotation.lookup_or_create(a_uri)
					a.subject = e.app.item
					a.item.text = tag
					a.item.source_id = Source.APPLICATION.id
					a.item.content_id = Content.TAG.id
			
			
		except sqlite3.IntegrityError, ex:
			traceback.print_exc()
			print >> sys.stderr, "Failed to insert event, '%s':\n%s" % (e_uri, ritem)
			print >> sys.stderr, "Error was: %s" % ex			
			return False
		
		# Extract tags
		if ritem.has_key("tags") and ritem["tags"].strip() != "":			
			# Iterate over non-empty strings only
			for tag in filter(lambda t : bool(t), ritem["tags"].split(";")):
				print "TAG:", tag
				a_uri = "zeitgeist://tag/%s" % tag
				a = Annotation.lookup_or_create(a_uri)
				a.subject = item
				a.item.text = tag
				a.item.source_id = Source.USER_ACTIVITY.id
				a.item.content_id = Content.TAG.id
		
		# Extract bookmarks
		if ritem.has_key("bookmark") and ritem["bookmark"]:
			print "BOOKMARK:", ritem["uri"]
			a_uri = "zeitgeist://bookmark/%s" % ritem["uri"]
			a = Annotation.lookup_or_create(a_uri)
			a.subject = item
			a.item.text = u"Bookmark"
			a.item.source_id = Source.USER_ACTIVITY.id
			a.item.content_id = Content.BOOKMARK.id

		if commit:
			store.flush()		
		
		return True
	
	def insert_items(self, items):
		"""
		Inserts items into the database and returns the amount of
		items it inserted.
		"""
		amount_items = 0
		for item in items:
			if self.insert_item(item, commit=False):
				amount_items += 1
			else:
				print >> sys.stderr, "Error inserting %s" % item["uri"]
		
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
		return []

engine = ZeitgeistEngine()
