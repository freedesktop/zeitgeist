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

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("zeitgeist.engine")


ALLOWED_FILTER_KEYS = set(["text_name", "text_uri", "tags", "mimetypes",
	"source", "content", "bookmarked"])

class ZeitgeistEngine(gobject.GObject):
	
	def __init__(self, storm_store):
		
		gobject.GObject.__init__(self)
		
		assert storm_store is not None
		self.store = storm_store
		self._apps = set()
		self._last_time_from_app = {}
		self._apps_id = {}
		
		'''
		path = BaseDirectory.save_data_path("zeitgeist")
		database = os.path.join(path, "zeitgeist.sqlite")
		self.connection = self._get_database(database)
		self.cursor = self.connection.cursor()
		'''
	
	def _get_app(self, id):
		if self._apps_id.has_key(id):
			return self._apps_id[id]
		
		info = self.store.execute("SELECT info FROM app WHERE item_id=?",
			(id,)).get_one()
		if info:
			self._apps_id[id] = info[0]
			return info[0]
	
	def _format_result(self, value):
		""" Takes a row from SQL containing all necessary event and item
		information and converts it into a tuple suitable for transmission
		over D-Bus. """
		
		return (
			value[1], # timestamp
			value[0], # uri
			value[7] or os.path.basename(value[0]), # name
			value[5], # source
			value[3], # content
			value[8], # mimetype
			value[12] or "", # tags
			"", # comment
			bool(value[11]), # bookmark
			value[4], # usage is determined by the event Content type # event.item.content.value
			value[9], # icon
			value[10], # app
			value[6] # origin
			)
	
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
		self._insert_event(id, content_id, source_id, text, origin, mimetype, icon)
		return self.store.find(Item, Item.id == id)
	
	def _insert_event(self, id, content_id, source_id, text, origin=None, mimetype=None, icon=None):
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
	
	def insert_event(self, ritem, commit=True, force=False):
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
			log.warning("Discarding item without a URI: %s" % ritem)
			return False
		if not ritem["content"].strip():
			log.warning("Discarding item without a Content type: %s" % ritem)
			return False
		if not ritem["source"].strip():
			log.warning("Discarding item without a Source type: %s" % ritem)
			return False
		if not ritem["mimetype"].strip():
			log.warning("Discarding item without a mimetype: %s" % ritem)
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
			log.exception("Couldn't insert event into DB.")
		
		return 1
	
	def insert_events(self, items):
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
			if self.insert_event(item, commit=False):
				inserted_items.append(item)
		self.store.commit()
		time2 = time.time()
		log.debug("Inserted %s items in %.5f s." % (len(inserted_items),
			time2 - time1))
		
		return inserted_items
	
	def get_item(self, uri):
		""" Returns basic information about the indicated URI. As we are
			fetching an item, and not an event, `timestamp' is 0 and `use'
			and `app' are empty strings."""
		
		item = self.store.execute("""
			SELECT uri.value, 0 AS timestamp, main_item.id, content.value,
				"" AS use, source.value, main_item.origin, main_item.text,
				main_item.mimetype, main_item.icon, "" AS app,
				(SELECT id
					FROM item
					INNER JOIN annotation ON annotation.item_id = item.id
					WHERE annotation.subject_id = main_item.id AND
						item.content_id = ?) AS bookmark,
				(SELECT group_concat(item.text, ", ")
					FROM item
					INNER JOIN annotation ON annotation.item_id = item.id
					WHERE annotation.subject_id = main_item.id AND
						item.content_id = ?
					) AS tags
			FROM item main_item
			INNER JOIN uri ON (uri.id = main_item.id)
			INNER JOIN content ON (content.id == main_item.content_id)
			INNER JOIN source ON (source.id == main_item.source_id)
			WHERE uri.value = ? LIMIT 1
			""", (Content.BOOKMARK.id, Content.TAG.id, unicode(uri))).get_one()
		
		if item:
			return self._format_result(item)
	
	def find_events(self, min=0, max=sys.maxint, limit=0,
			sorting_asc=True, mode="event", filters=(), only_count=False):
		"""
		Returns all items from the database between the indicated
		timestamps `min' and `max'. Optionally the argument `tags'
		may be used to filter on tags or `mimetypes' to filter on
		mimetypes.
		
		Parameter `mode' can be one of "event", "item" or "mostused".
		The first mode returns all events, the second one only returns
		the last event when items are repeated and the "mostused" mode
		is like "item" but returns the results sorted by the number of
		events.
		
		Parameter `filters' is an array of structs containing: (text
		to search in the name, text to search in the URI, tags,
		mimetypes, source, content). The filter between characteristics
		inside the same struct is of type AND (all need to match), but
		between diferent structs it is OR-like (only the conditions
		described in one of the structs need to match for the item to
		be returned).
		"""
		
		time1 = time.time()
		
		# Emulate optional arguments for the D-Bus interface
		if not max:
			max = sys.maxint
		if not mode:
			mode = "event"
		
		if not mode in ("event", "item", "mostused"):
			logging.error("Bad find_events call: mode \"%s\" not recongized." \
				% mode)
			return ()
		
		# filters is a list of dicts, where each dict can have the following items:
		#   text_name: <str>
		#   text_uri: <str>
		#   tags: <list> of <str>
		#   mimetypes: <list> or <str>
		#   source: <str>
		#   content: <str>
		#   bookmarked: <bool> (True means bookmarked items, and vice versa
		expressions = []
		additional_args = []
		for filter in filters:
			if not isinstance(filter, dict):
				raise TypeError("Expected a dict, got %s." % type(filter).__name__)
			invalid_filter_keys = set(filter.keys()) - ALLOWED_FILTER_KEYS
			if invalid_filter_keys:
				raise ValueError("Invalid key(s) for filter in ZeitgeistEngine.find_events: %s" %", ".join(invalid_filter_keys))
			filterset = []
			if "text_name" in filter:
				filterset += [ "main_item.text LIKE ? ESCAPE \"\\\"" ]
				additional_args += [ filter["text_name"] ]
			if "text_uri" in filter:
				filterset += [ "uri.value LIKE ? ESCAPE \"\\\"" ]
				additional_args += [ filter["text_uri"] ]
			if "tags" in filter:
				for tag in filter["tags"]:
					filterset += [ "(tags == \"%s\" OR tags LIKE \"%s, %%\" OR "
						"tags LIKE \"%%, %s, %%\" OR tags LIKE \"%%, %s\")" \
						% (tag, tag, tag, tag) ]
			if "mimetypes" in filter and len(filter["mimetypes"]):
				filterset += [ "(" + " OR ".join(
					['main_item.mimetype LIKE ? ESCAPE "\\"'] * \
					len(filter["mimetypes"])) + ")" ]
				additional_args += filter["mimetypes"]
			if "source" in filter:
				pass # source ...
			if "content" in filter:
				pass # content
			if "bookmarked" in filter:
				if filter["bookmarked"]:
					# Only get bookmarked items
					filterset += [ "bookmark > 0" ]
				else:
					# Only get items that aren't bookmarked
					pass # FIXME
					#filterset += [ "bookmark < 1" ]
			if filterset:
				expressions += [ "(" + " AND ".join(filterset) + ")" ]
		
		if expressions:
			expressions = ("AND (" + " OR ".join(expressions) + ")")
		else:
			expressions = ""
		
		preexpressions = ""
		additional_orderby = ""
		
		if mode in ("item", "mostused"):
			preexpressions += ", MAX(event.start)"
			expressions += " GROUP BY event.subject_id"
			if mode == "mostused":
				additional_orderby = "COUNT(event.rowid) DESC,"
		
		if not only_count:
			select = """
				uri.value, event.start, main_item.id, content.value,
				"" AS use, source.value, main_item.origin, main_item.text,
				main_item.mimetype, main_item.icon,
				(SELECT info
					FROM app
					WHERE app.item_id = event.app_id
					) AS app,
				(SELECT id
					FROM item
					INNER JOIN annotation ON annotation.item_id = item.id
					WHERE annotation.subject_id = main_item.id AND
						item.content_id = ?) AS bookmark,
				(SELECT group_concat(item.text, ", ")
					FROM item
					INNER JOIN annotation ON annotation.item_id = item.id
					WHERE annotation.subject_id = main_item.id AND
						item.content_id = ?
					) AS tags
				"""
			args = [ Content.BOOKMARK.id, Content.TAG.id, min, max ]
		else:
			select = "COUNT(event.rowid)"
			args = [ min, max ]
		
		args += additional_args
		args += [ limit or sys.maxint ]
		
		events = self.store.execute("""
			SELECT %s
				%s
			FROM item main_item
			INNER JOIN event ON (main_item.id = event.subject_id)
			INNER JOIN uri ON (uri.id = main_item.id)
			INNER JOIN content ON (content.id == main_item.content_id)
			INNER JOIN source ON (source.id == main_item.source_id)
			WHERE event.start >= ? AND event.start <= ? %s
			ORDER BY %s event.start %s LIMIT ?
			""" % (select, preexpressions, expressions, additional_orderby,
				"ASC" if sorting_asc else "DESC"), args).get_all()
		
		if not only_count:
			result = [self._format_result(event) for event in events]
			
			time2 = time.time()
			log.debug("Fetched %s items in %.5f s." % (len(result), time2 - time1))
		else:
			result = events[0][0]
		
		return result
	
	def _update_item(self, item):
		"""
		Updates an item already in the database.
		
		If the item has tags, then the tags will also be updated.
		"""
		
		#FIXME Delete all tags of the ITEM
		self._delete_item(item)
		self.store.commit()
		self.store.flush()
		self.insert_event(item, True, True)
		self.store.commit()
		self.store.flush()
	
	def update_items(self, items):
		map(self._update_item, items)
	
	def _delete_item(self, uri):
		
		uri_id = self.store.execute("SELECT id FROM URI WHERE value=?", (uri,)).get_one()
		uri_id = uri_id[0]
		annotation_ids = self.store.execute(
			"SELECT item_id FROM Annotation WHERE subject_id=?", (uri_id,)).get_all()
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
