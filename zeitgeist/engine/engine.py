# -.- encoding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Seif Lotfy <seif@lotfy.com>
# Copyright © 2009 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
# Copyright © 2009 Natan Yellin <aantny@gmail.com>
# Copyright © 2009 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import time
import sys
import os
import shutil
import sqlite3
import gettext
import gobject
from xdg import BaseDirectory
from xdg.DesktopEntry import DesktopEntry

import traceback
from random import randint

from zeitgeist import config
from zeitgeist.engine.base import *

class ZeitgeistEngine(gobject.GObject):

	def __init__(self, storm_store):
		
		gobject.GObject.__init__(self)
		
		assert storm_store is not None
		self.store = storm_store
		self._apps = set()
		self._last_time_from_app = {}
        
		'''
		path = BaseDirectory.save_data_path("zeitgeist")
		database = os.path.join(path, "zeitgeist.sqlite")
		self.connection = self._get_database(database)
		self.cursor = self.connection.cursor()
		'''
	
	def _result2data(self, event=None, item=None):
		
		# FIXME: Get tag
		tags = ""
		
		# FIXME: Get bookmark
		bookmark = False
		
		if not item :
			item = event.subject
		#check if the item is bookmarked
		#FIXME: this seems redundant if i am fetching bookmarked items
		bool = self.store.find(Item, Item.content_id == Content.BOOKMARK.id, Annotation.subject_id == item.id , Annotation.item_id == Item.id).one()
		if bool:
			bookmark = True
		
		return (
			event.start if event else 0, # timestamp
			item.uri.value, # uri
			item.text or os.path.basename(item.uri.value), # name
			item.source.value or "", # source
			item.content.value or "", # content
			item.mimetype or "", # mimetype
			tags or "", # tags
			event.item.content.value if event else "",# usage is determined by the event Content type
			bookmark, # bookmark
			item.icon or "", # icon
			"", # app
			item.origin or "" # origin
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
	
	def get_last_timestamp(self, uri=None):
		"""
		Gets the timestamp of the most recent item in the database. If
		`uri' is not empty, it will give the last timestamp for the
		indicated URI.
		
		Returns 0 if there are no items in the database.
		"""
		
		return 0
	
	def insert_item(self, ritem, commit=True, force=False):
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
		if not ritem.has_key("mimetype") or not ritem["mimetype"]:
			print >> sys.stderr, "Discarding item without a mimetype: %s" % ritem
			return False
		
		item_changed = False
		
		item = Item.lookup(ritem["uri"])
		if not item or force:
			item_changed = True
			if not item:
				item = Item.lookup_or_create(ritem["uri"])
			item.content = Content.lookup_or_create(ritem["content"])
			item.source = Source.lookup_or_create(ritem["source"])
			item.mimetype = unicode(ritem["mimetype"])
			item.text = unicode(ritem["text"]) if ritem.has_key("text") else None
			item.origin = unicode(ritem["origin"]) if ritem.has_key("origin") else None
			item.icon = unicode(ritem["icon"]) if ritem.has_key("icon") else None
			
			# Extract tags
			if ritem.has_key("tags") and ritem["tags"].strip():
				for tag in (tag for tag in ritem["tags"].split(",") if tag):
					tag_uri = "zeitgeist://tag/%s" % tag
					print "Tagging ---> ", ritem["uri"], "with", tag_uri
					a = Annotation(tag_uri)
					item.annotations.add(a)#Annotation.lookup_or_create("zeitgeist://tag/%s" % tag)
					a.item.text = tag
					a.item.source_id = Source.USER_ACTIVITY.id
					a.item.content_id = Content.TAG.id
					try:
						self.store.flush()
					except sqlite3.IntegrityError:
						print "Tagging relation", tag_uri, "-->", ritem["uri"], "already known"
			
			# Extract bookmarks
			if ritem.has_key("bookmark") and ritem["bookmark"]:
				a_uri = "zeitgeist://bookmark/%s" % ritem["uri"]
				print "Bookmarking ---> "+ ritem["uri"]
				a = Annotation(a_uri)
				item.annotations.add(a)
				a.item.text = u"Bookmark"
				a.item.source_id = Source.USER_ACTIVITY.id
				a.item.content_id = Content.BOOKMARK.id
				try:
					self.store.flush()
				except sqlite3.IntegrityError:
					print "Bookmark", a_uri, "-->", ritem["uri"], "already known"
			if force:
				   return True

		e_uri = "zeitgeist://event/%s/%%s/%s#%d" % (ritem["use"],
			ritem["timestamp"], item.id)
		
		# Check if the event already exists: if so, don't bother inserting
		e = Event.lookup(e_uri)
		if not e:
			item_changed = True
			# Store the event
			e = Event.lookup_or_create(e_uri)
			item.events.add(e)
			e.start = ritem["timestamp"]
			e.item.text = u"Activity"
			e.item.source_id = Source.USER_ACTIVITY.id
			e.item.content_id = Content.lookup_or_create(ritem["use"]).id
			
			# Store the application
			app_info = DesktopEntry(ritem["app"])
			app = App.lookup_or_create(ritem["app"])
			app.item.text = unicode(app_info.getName())
			app.item.content = Content.lookup_or_create(app_info.getType())
			# Use only the first word (eg. "firefox" out of "firefox %u")
			app.item.source = Source.lookup_or_create(app_info.getExec().split()[0])
			app.item.icon = unicode(app_info.getIcon())
			app.info = unicode(ritem["app"])
			e.app = app
			
			# FIXME: This seems to pollute the user provided tags
			"""for tag in app_info.getCategories(): 
				a = Annotation.lookup_or_create("zeitgeist://tag/%s" % tag)
				a.subject = e.app.item
				a.item.text = unicode(tag)
				a.item.source_id = Source.APPLICATION.id
				a.item.content_id = Content.TAG.id"""
		
		if commit:
			self.store.flush()
		
		return item_changed
	
	def insert_items(self, items):
		"""
		Inserts items into the database and returns the amount of
		items it inserted.
		"""
		
		amount_items = 0
		
		# Check if event is before the last logs
		t1 = time.time()
		for item in items:
			if self.insert_item(item, commit=False):
				amount_items += 1
		self.store.commit()
		t2 = time.time()
		print ">>>>>> Inserted %s items in %ss" % (amount_items,t2-t1)
		
		return amount_items
	
	def get_item(self, uri):
		"""Returns basic information about the indicated URI."""
		item = self.store.find(Item, Item.id == URI.id,
			URI.value == unicode(uri)).one()		
		if item:
			return self._result2data(item=item)
	
	def get_items(self, min=0, max=sys.maxint, limit=0,
	sorting_asc=True, unique=False, filters=()):
		"""
		Returns all items from the database between the indicated
		timestamps `min' and `max'. Optionally the argument `tags'
		may be used to filter on tags or `mimetypes' to filter on
		mimetypes.
		
		Parameter filters is an array of structs containing: (text
		to search in the name, text to search in the URI, tags,
		mimetypes, source, content). The filter between characteristics
		inside the same struct is of type AND (all need to match), but
		between diferent structs it is OR-like (only the conditions
		described in one of the structs need to match for the item to
		be returned).
		"""
		
		# Emulate optional arguments for the D-Bus interface
		if not max: max = sys.maxint
		
		t1 = time.time()
		events = self.store.find(Event, Event.start >= min, Event.start <= max)
		events.order_by(Event.start if sorting_asc else Desc(Event.start))
		
		if limit > 0:
			events = events[:limit]
		if unique:
			events.max(Event.start)
			events.group_by(Event.subject_id)
		
		return [self._result2data(event) for event in events]
	
	def update_item(self, item):
		"""
		Updates an item already in the database.
		
		If the item has tags, then the tags will also be updated.
		"""
		
		#FIXME Delete all annotations of the ITEM
		self.delete_item(item)
		self.store.commit()
		self.store.flush()
		self.insert_item(item, True, True)
		self.store.commit()
		self.store.flush()
	
	
	def delete_item(self, item):
		
		uri_id = self.store.execute("SELECT id FROM URI WHERE value=?",(item["uri"],)).get_one()
		uri_id = uri_id[0]
		annotation_ids = self.store.execute("SELECT item_id FROM Annotation WHERE subject_id=?",(uri_id,)).get_all()
		print annotation_ids
		if len(annotation_ids) > 0:
			for anno in annotation_ids[0]:
				self.store.execute("DELETE FROM Annotation WHERE subject_id=?",(uri_id,))
				print anno
				self.store.execute("DELETE FROM Item WHERE id=?",(anno,))
		
		self.store.execute("DELETE FROM Item WHERE id=?",(uri_id,))
		
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
		tags = self.store.find(Item, Item.content_id == Content.TAG.id)
		return [tag.text for tag in tags]		
	
	def get_types(self):
		"""
		Returns a list of all different types in the database.
		"""
		contents = self.store.find(Content)
		return [content.value for content in contents]
	
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
	
	def get_last_insertion_date(self, application):
		"""
		Returns the timestamp of the last item which was inserted
		related to the given application. If there is no such record,
		0 is returned.
		"""
		
		app = App.lookup(application)
		
		return self.store.find(Event.start, Event.app == app.item.id
			).order_by(Event.start).last() if app else 0
	
	def get_related_items(self, uri):
		pass
	
	def compare_nbhs(self,nbhs):
		pass
	
	def get_uris_for_timestamp(self, timestamp):
		pass
	
	def get_bookmarks(self):
		uris = self.store.find(URI, Item.content_id == Content.BOOKMARK.id, URI.id == Annotation.subject_id, Annotation.item_id == Item.id)
		for uri in uris:
			#Get the item for the uri
			item = self.store.find(Item, Item.id == uri.id).one()
			yield self._result2data(None, item)
                
_engine = None
def get_default_engine():
	global _engine
	if not _engine:
		_engine = ZeitgeistEngine(get_default_store())
	return _engine
