# -.- encoding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Seif Lotfy <seif@lotfy.com>
# Copyright © 2009 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
# Copyright © 2009 Natan Yellin <aantny@gmail.com>
# Copyright © 2009 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
# Copyright © 2009 Markus Korn <thekorn@gmx.de>
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
import gettext
import gobject
import logging
from xdg import BaseDirectory
from xdg.DesktopEntry import DesktopEntry
import sqlite3

from zeitgeist import config
from zeitgeist.engine.base import *
from zeitgeist.dbusutils import ITEM_STRUCTURE_KEYS, TYPES_DICT

class ZeitgeistEngine(gobject.GObject):
	
	def __init__(self, storm_store):
		
		gobject.GObject.__init__(self)
		
		assert storm_store is not None
		self.store = storm_store
		self._apps = set()
		self._bookmarks = []
		self._last_time_from_app = {}
		
		'''
		path = BaseDirectory.save_data_path("zeitgeist")
		database = os.path.join(path, "zeitgeist.sqlite")
		self.connection = self._get_database(database)
		self.cursor = self.connection.cursor()
		'''
	
	def _set_bookmarks(self):
		self._bookmarks = self.store.find(Annotation.subject_id,
			Item.content_id == Content.BOOKMARK.id,
			Annotation.item_id == Item.id).values(Annotation.subject_id)
	
	def _result2data(self, event=None, item=None):
		
		if not item:
			item = event.subject
		
		# The SQL calls to get the bookmark status and the tags here
		# is really time consuming when done for a set of results from
		# find_events. Rather, the SQL queries getting the events should
		# also fetch this information.
		
		# Check if the item is bookmarked
		bookmark = item.id in self._bookmarks
		
		result = self._get_tags_for_item(item)
		tags = ",".join(set(result)) if result else ""
		
		return (
			event.start if event else 0, # timestamp
			item.uri.value, # uri
			item.text or os.path.basename(item.uri.value), # name
			item.source.value or "", # source
			item.content.value or "", # content
			item.mimetype or "", # mimetype
			tags, # tags
			"", # comment
			bookmark, # bookmark
			# FIXME: I guess event.item.content below should never be None
			event.item.content.value if (event and event.item.content) else "", # usage is determined by the event Content type
			item.icon or "", # icon
			"", # app	  # FIXME!
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
	
	def _get_ids(self, uri, content, source):	
		uri_id = URI.lookup_or_create(uri).id if uri else None
		content_id = Content.lookup_or_create(content).id if content else None
		source_id = Source.lookup_or_create(source).id if source else None
		return uri_id, content_id, source_id
	
	def _get_item(self, id, content_id, source_id, text, origin=None, mimetype=None, icon=None):
		self._insert_item(id, content_id, source_id, text, origin, mimetype, icon)
		return self.store.find(Item, Item.id == id)
	
	def _insert_item(self, id, content_id, source_id, text, origin=None, mimetype=None, icon=None):
		try:
			self.store.execute("""
				INSERT INTO Item
				(id, content_id, source_id, text, origin, mimetype, icon)
				VALUES (?,?,?,?,?,?,?)""",
				(id, content_id, source_id, text, origin, mimetype, icon),
				noresult=True)
		except Exception:
			self.store.execute("""
				UPDATE Item SET
				content_id=?, source_id=?, text=?, origin=?,
				mimetype=?, icon=? WHERE id=?""",
				(content_id, source_id, text, origin, mimetype, icon, id),
				noresult=True)
	
	def insert_item(self, ritem, commit=True, force=False):
		"""
		Inserts an item into the database. Returns a positive number on success,
		zero otherwise (for example, if the item already is in the
		database). In case the positive number is 1, the inserted event is new,
		in case it's 2 the event already existed and was updated (this only
		happens when `force' is True).
		"""
		# we require all  all keys here
		missing = ITEM_STRUCTURE_KEYS - set(ritem.keys())
		if missing:
			raise KeyError(("these keys are missing in order to add "
							"this item properly: %s" %", ".join(missing)))
		if not ritem["uri"].strip():
			logging.warning("Discarding item without a URI: %s" % ritem)
			return False
		if not ritem["content"].strip():
			logging.warning("Discarding item without a Content type: %s" % ritem)
			return False
		if not ritem["source"].strip():
			logging.warning("Discarding item without a Source type: %s" % ritem)
			return False
		if not ritem["mimetype"].strip():
			logging.warning("Discarding item without a mimetype: %s" % ritem)
			return False
		ritem = dict((key, TYPES_DICT[key](value)) for key, value in ritem.iteritems())
		
		# Get the IDs for the URI, the content and the source
		uri_id, content_id, source_id = self._get_ids(ritem["uri"],
			ritem["content"], ritem["source"])
		
		# Generate the URI for the event
		event_uri = "zeitgeist://event/%s/%%s/%s#%d" % (ritem["use"],
			ritem["timestamp"], uri_id)
		
		# Check whether the events is already in the database. If so,
		# don't do anything. If it isn't there yet, we proceed with the
		# process. Except if `force' is true, then we always proceed.
		event_exists = bool(self.store.execute(
			"SELECT id FROM uri WHERE value = ?", (event_uri,)).get_one())
		if not force and event_exists:
			return 0
		
		# Insert or update the item
		item = self._get_item(uri_id, content_id, source_id, ritem["text"],
			ritem["origin"], ritem["mimetype"], ritem["icon"])
		
		# Insert or update the tags
		for tag in (tag.strip() for tag in ritem["tags"].split(",") if tag):
			anno_uri = "zeitgeist://tag/%s" % tag
			anno_id, discard, discard = self._get_ids(anno_uri, None, None)
			anno_item = self._get_item(anno_id, Content.TAG.id, Source.USER_ACTIVITY.id, tag)
			try:
				self.store.execute(
					"INSERT INTO annotation (item_id, subject_id) VALUES (?,?)",
					(anno_id, uri_id), noresult=True)
			except sqlite3.IntegrityError:
				pass # Tag already registered
		
		# Set the item as bookmarked, if it should be
		if ritem["bookmark"]:
			anno_uri = "zeitgeist://bookmark/%s" % ritem["uri"]
			anno_id, discard, discard = self._get_ids(anno_uri, None, None)
			anno_item = self._get_item(anno_id, Content.BOOKMARK.id,
				Source.USER_ACTIVITY.id, u"Bookmark")
			try:
				self.store.execute(
					"INSERT INTO annotation (item_id, subject_id) VALUES (?,?)",
					(anno_id, uri_id), noresult=True)
			except sqlite3.IntegrityError:
				pass # Item already bookmarked
		
		# Do not update the application nor insert the event if `force' is
		# True, ie., if we are updating an existing item.
		if force:
			return 2 if event_exists else 1
		
		# Insert the application
		# FIXME: Is reading the .desktop file and storing that stuff into
		# the DB really required?
		app_info = DesktopEntry(ritem["app"])
		app_uri_id, app_content_id, app_source_id = self._get_ids(ritem["app"],
			unicode(app_info.getType()), unicode(app_info.getExec()).split()[0])
		app_item = self._get_item(app_uri_id, app_content_id, app_source_id,
			unicode(app_info.getName()), icon=unicode(app_info.getIcon()))
		try:
			self.store.execute("INSERT INTO app (item_id, info) VALUES (?,?)",
				(app_uri_id, unicode(ritem["app"])), noresult=True)
		except sqlite3.IntegrityError:
			pass
		
		# Insert the event
		e_id, e_content_id, e_subject_id = self._get_ids(event_uri, ritem["use"], None)
		e_item = self._get_item(e_id, e_content_id, Source.USER_ACTIVITY.id, u"Activity")
		try:
			self.store.execute(
				"INSERT INTO event (item_id, subject_id, start, app_id) VALUES (?,?,?,?)",
				(e_id, uri_id, ritem["timestamp"], app_uri_id), noresult=True)
		except sqlite3.IntegrityError:
			# This shouldn't happen.
			logging.exception("Couldn't insert event into DB.")
		
		return 1
	
	def insert_items(self, items):
		"""
		Inserts items into the database and returns those items which were
		successfully inserted. If an item fails, that's usually because it
		already was in the database.
		"""
		
		inserted_items = []
		
		time1 = time.time()
		for item in items:
			# This is always 0 or 1, no need to consider 2 as we don't
			# use the `force' option.
			if self.insert_item(item, commit=False):
				inserted_items.append(item)
		self.store.commit()
		time2 = time.time()
		logging.debug("Inserted %s items in %.5f s." % (len(inserted_items),
			time2 - time1))
		
		self._set_bookmarks()
		return inserted_items
	
	def get_item(self, uri):
		"""Returns basic information about the indicated URI."""
		item = self.store.find(Item, Item.id == URI.id,
			URI.value == unicode(uri)).one()
		if item:
			return self._result2data(item=item)
	
	def find_events(self, min=0, max=sys.maxint, limit=0,
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
		
		# filters is a list of dicts, where each dict can have the following items:
		#   text_name: <str>
		#   text_uri: <str>
		#   tags: <list> of <str>
		#   mimetypes: <list> or <str>
		#   source: <str>
		#   content: <str>
		#   bookmarked: <bool> (True means bookmarked items, and vice versa
		expressions = []
		for filter in filters:
			if not isinstance(filter, dict):
				raise TypeError("Expected a dict, got %s." % type(filter).__name__)
			filterset = []
			if "text_name" in filter:
				filterset += [ Item.text.like(unicode(filter["text_name"]), escape="\\") ]
			if "text_uri" in filter:
				filterset += [ URI.value.like(unicode(filter["text_uri"]), escape="\\") ]
			if "tags" in filter:
				pass # tags...
			if "mimetypes" in filter:
				condition = ' OR '.join(
					['mimetype LIKE ? ESCAPE "\\"'] * len(filter["mimetypes"]))
				mimetypes = [m[0] for m in self.store.execute("""
						SELECT DISTINCT(mimetype) FROM item
						WHERE %s""" % condition, filter["mimetypes"]).get_all()]
				filterset += [ Item.mimetype.is_in(mimetypes) ]
			if "source" in filter:
				pass # source ...
			if "content" in filter:
				pass # content
			if "bookmarked" in filter:
				bookmarks = Select(Annotation.subject_id, And(
					Item.content_id == Content.BOOKMARK.id,
					Annotation.item_id == Item.id))
				if filter["bookmarked"]:
					# Only get bookmarked items
					filterset += [Event.subject_id.is_in(bookmarks)]
				else:
					# Only get items that aren't bookmarked
					filterset += [Not(Event.subject_id.is_in(bookmarks))]
			if filterset:
				expressions += [ And(*filterset) ]
		
		t1 = time.time()
		events = self.store.find(Event, Event.start >= min, Event.start <= max,
			URI.id == Event.subject_id, Item.id == Event.subject_id,
			Or(*expressions) if expressions else True)
		events.order_by(Event.start if sorting_asc else Desc(Event.start))
		
		if unique:
			events.max(Event.start)
			events.group_by(Event.subject_id)
		
		return [self._result2data(event) for event in events[:limit or None]]
	
	def _update_item(self, item):
		"""
		Updates an item already in the database.
		
		If the item has tags, then the tags will also be updated.
		"""
		
		#FIXME Delete all tags of the ITEM
		self._delete_item(item)
		self.store.commit()
		self.store.flush()
		self.insert_item(item, True, True)
		self.store.commit()
		self.store.flush()
		self._set_bookmarks()
	
	def update_items(self, items):
		map(self._update_item, items)
	
	def _get_tags_for_item(self, item):
		package = []
		id = item.id
		tags = self.store.find(Annotation.item_id, Annotation.subject_id == id)
		for tag in tags:
			tag = self.store.find(Item.text, Item.id == tag).one()
			package.append(tag)
		return package
	
	def _delete_item(self, item):
		
		uri_id = self.store.execute("SELECT id FROM URI WHERE value=?",(item["uri"],)).get_one()
		uri_id = uri_id[0]
		annotation_ids = self.store.execute("SELECT item_id FROM Annotation WHERE subject_id=?",(uri_id,)).get_all()
		if len(annotation_ids) > 0:
			for anno in annotation_ids[0]:
				self.store.execute("DELETE FROM Annotation WHERE subject_id=?",
					(uri_id,), noresult=True)
				self.store.execute("DELETE FROM Item WHERE id=?",
					(anno,), noresult=True)		
		self.store.execute("DELETE FROM Item WHERE id=?",
			(uri_id,), noresult=True)
	
	def delete_items(self, items):
		map(self._delete_item, items)
	
	def get_types(self):
		"""
		Returns a list of all different types in the database.
		"""
		contents = self.store.find(Content)
		return [content.value for content in contents]
	
	def get_tags(self, name_filter="", limit=0, min_timestamp=0, max_timestamp=0):
		"""
		Returns a list containing tuples with the name and the number of
		occurencies of the tags matching `name_filter', or all existing
		tags in case it's empty, sorted from most used to least used. `limit'
		can base used to limit the amount of results.
		
		Use `min_timestamp' and `max_timestamp' to limit the time frames you
		want to consider.
		"""
		
		return self.store.execute("""
			SELECT item.text, (SELECT COUNT(rowid) FROM annotation
				WHERE annotation.item_id = item.id) AS amount
			FROM item
			WHERE item.id IN (SELECT annotation.item_id FROM annotation
				INNER JOIN event ON (event.subject_id = annotation.subject_id)
				WHERE event.start >= ? AND event.start <= ?)
				AND item.content_id = ? AND item.text LIKE ? ESCAPE "\\"
			ORDER BY amount DESC LIMIT ?
			""", (min_timestamp, max_timestamp or sys.maxint, Content.TAG.id,
			name_filter or "%", limit or sys.maxint)).get_all()
	
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
		return []

_engine = None
def get_default_engine():
	global _engine
	if not _engine:
		_engine = ZeitgeistEngine(get_default_store())
	return _engine
