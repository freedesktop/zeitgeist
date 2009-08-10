# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Seif Lotfy <seif@lotfy.com>
# Copyright © 2009 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
# Copyright © 2009 Natan Yellin <aantny@gmail.com>
# Copyright © 2009 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
# Copyright © 2009 Markus Korn <thekorn@gmx.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sqlite3
import time
import sys
import os
import gettext
import logging
from xdg import BaseDirectory
from xdg.DesktopEntry import DesktopEntry

from zeitgeist.datamodel import *
import _zeitgeist.engine
from _zeitgeist.engine.engine_base import BaseEngine
from _zeitgeist.engine.querymancer import *
from _zeitgeist.lrucache import *
from zeitgeist.dbusutils import EventDict

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("zeitgeist.engine")

class Entity:
	def __init__(self, id, value):
		self.id = id
		self.value = value
	
	def __repr___ (self):
		return "%s (id: %s)" % (self.value, self.id)

class EntityTable(Table):
	"""
	Generic base class for Tables that has an 'id' and a 'value' column.
	This means Content, Source, and URI
	"""
	
	def __init__ (self, table_name):
		"""Create a new Entity with uri=value and insert it into the table"""		
		if table_name is None :
			raise ValueError("Can not create EntityTable with name None")
		
		Table.__init__(self, table_name, id=Integer(), value=String())
		self._CACHE = LRUCache(1000)
	
	def lookup(self, value):
		"""Look up an entity by value or id, return None if the
		   entity is not known"""
		if not value:
			raise ValueError("Looking up %s without a value" % self)
		
		try:
			return self._CACHE[value]
		except KeyError:
			pass # We didn't have it cached; fall through and handle it below
		
		row = self.find_one(self.id, self.value == value)
		if row :			
			ent = Entity(row[0], value)
			self._CACHE[value] = ent
			log.debug("Found %s: %s" % (self, ent))
			return ent
		return None
			
	
	def lookup_or_create(self, value):
		"""Find the entity matching the uri 'value' or create it if necessary"""
		ent = self.lookup(value)
		if ent : return ent
		
		try:
			row_id = self.add(value=value)
		except sqlite3.IntegrityError, e:
			log.warn("Unexpected integrity error when inserting %s %s: %s" % (self, value, e))
			return None
		
		# We can peek the last insert row id from SQLite,
		# this saves us a whole SELECT
		ent = Entity(row_id, value)
		self._CACHE[value] = ent
		log.debug("Created %s %s %s" % (self, ent.id, ent.value))
				
		return ent

# Table defs are assigned in create_db()
_content = None
_source = None
_uri = None
_item = None
_app = None
_annotation = None
_event = None

def create_db(file_path):
	"""Create the database and return a default cursor for it"""
	log.info("Creating database: %s" % file_path)
	conn = sqlite3.connect(file_path)
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS content
			(id INTEGER PRIMARY KEY, value VARCHAR UNIQUE)
		""")
	cursor.execute("""
		CREATE UNIQUE INDEX IF NOT EXISTS content_value
			ON content(value)
		""")
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS source
			(id INTEGER PRIMARY KEY, value VARCHAR UNIQUE)
		""")
	cursor.execute("""
		CREATE UNIQUE INDEX IF NOT EXISTS source_value
			ON source(value)""")
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS uri
			(id INTEGER PRIMARY KEY, value VARCHAR UNIQUE)
		""")
	cursor.execute("""
		CREATE UNIQUE INDEX IF NOT EXISTS uri_value ON uri(value)
		""")
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS item
			(id INTEGER PRIMARY KEY, content_id INTEGER,
				source_id INTEGER, origin VARCHAR, text VARCHAR,
				mimetype VARCHAR, icon VARCHAR, payload BLOB)
		""")
	# FIXME: Consider which indexes we need on the item table
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS app
			(item_id INTEGER PRIMARY KEY, info VARCHAR)
		""")
	cursor.execute("""
		CREATE UNIQUE INDEX IF NOT EXISTS app_value ON app(info)
		""")
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS annotation
			(item_id INTEGER, subject_id INTEGER, PRIMARY KEY (item_id, subject_id))
		""")
	cursor.execute("""
	CREATE TABLE IF NOT EXISTS event 
		(item_id INTEGER PRIMARY KEY, subject_id INTEGER, start INTEGER,
			end INTEGER, app_id INTEGER)
		""")
	cursor.execute("""
		CREATE INDEX IF NOT EXISTS
			event_subject_id ON annotation(subject_id)
		""")
	
	# Table defs
	global _cursor, _content, _source, _uri, _item, _app, _annotation, _event
	_cursor = cursor
	_content = EntityTable("content")
	_source = EntityTable("source")
	_uri = EntityTable("uri")
	_item = Table("item", id=Integer(), content_id=Integer(),
					source_id=Integer(), origin=String(), text=String(),
					mimetype=String(), icon=String(), payload=String(),
					comment=String())
	# FIXME: _item.payload should be a BLOB type
	# FIXME: _item.comment is really not in the table, it should be an annotation type
	_app = Table("app", item_id=Integer(), info=String())	
	_annotation = Table("annotation", item_id=Integer(), subject_id=Integer())	
	_event = Table("event", item_id=Integer(), subject_id=Integer(), start=Integer(),
					end=Integer(), app_id=Integer())
	
	_content.set_cursor(_cursor)
	_source.set_cursor(_cursor)
	_uri.set_cursor(_cursor)
	_item.set_cursor(_cursor)
	_app.set_cursor(_cursor)
	_annotation.set_cursor(_cursor)
	_event.set_cursor(_cursor)

	# Bind the db into the datamodel module
	Content._clear_cache()
	Source._clear_cache()
	Content.bind_database(_content)
	Source.bind_database(_source)
	
	return cursor

_cursor = None
def get_default_cursor():
	global _cursor
	if not _cursor:
		dbfile = _zeitgeist.engine.DB_PATH
		_cursor = create_db(dbfile)
	return _cursor

def set_cursor(cursor):
	global _cursor, _content, _source, _uri, _item, _event, _annotation, _app
	
	if _cursor :		
		_cursor.close()
	
	_cursor = cursor
	_content.set_cursor(cursor)
	_source.set_cursor(cursor)
	_uri.set_cursor(cursor)
	_item.set_cursor(cursor)
	_annotation.set_cursor(cursor)
	_app.set_cursor(cursor)	
	_event.set_cursor(cursor)

def reset():
	global _cursor, _content, _source, _uri, _item, _event, _annotation, _app
	
	if _cursor :		
		_cursor.connection.close()
	
	_cursor = None
	_content = None
	_source = None
	_uri = None
	_item = None
	_annotation = None
	_app = None
	_event = None

class ZeitgeistEngine(BaseEngine):
	
	def __init__(self, cursor=None):
		super(ZeitgeistEngine, self).__init__()
		if cursor is not None:
			set_cursor(cursor)
			self.cursor = cursor
		else:
			self.cursor = get_default_cursor()
		assert self.cursor is not None
	
	def _get_ids(self, uri, content, source):	
		uri_id = _uri.lookup_or_create(uri).id if uri else None
		content_id = Content.get(content).id if content else None
		source_id = Source.get(source).id if source else None
		return uri_id, content_id, source_id
	
	def _store_item(self, id, content_id, source_id,
					text, origin=None, mimetype=None, icon=None):
		try:
			_item.add(id=id, content_id=content_id, source_id=source_id,
						text=text, origin=origin, mimetype=mimetype, icon=icon)
		except sqlite3.IntegrityError:
			_item.update(_item.id == id,
							content_id=content_id, source_id=source_id, text=text,
							origin=origin, mimetype=mimetype, icon=icon)
		return _item.find_one("*", _item.id == id)
			
	def insert_event(self, ritem, commit=True, force=False):
		"""
		Inserts an item into the database. Returns a positive number on success,
		zero otherwise (for example, if the item already is in the
		database). In case the positive number is 1, the inserted event is new,
		in case it's 2 the event already existed and was updated (this only
		happens when `force' is True).
		"""
		
		# check for required items and make sure all items have the correct type
		EventDict.check_missing_items(ritem, True)
		
		# FIXME: uri, content, source are now required items, the statement above
		# will raise a KeyError if they are not there. What about mimetype?
		# and why are we printing a warning and returning False here instead of raising
		# an error at all? - Markus Korn
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
		
		# Get the IDs for the URI, the content and the source
		uri_id, content_id, source_id = self._get_ids(ritem["uri"],
			ritem["content"], ritem["source"])
		
		# Generate the URI for the event
		event_uri = "zeitgeist://event/%s/%%s/%s#%d" % (ritem["use"],
			ritem["timestamp"], uri_id)
		
		# Check whether the events is already in the database. If so,
		# don't do anything. If it isn't there yet, we proceed with the
		# process. Except if `force' is true, then we always proceed.
		event_exists = bool(_uri.find_one(_uri.id, _uri.value == event_uri))
		if not force and event_exists:
			return 0
		
		# Insert or update the item
		item = self._store_item(uri_id, content_id, source_id, ritem["text"],
			ritem["origin"], ritem["mimetype"], ritem["icon"])
		
		# Insert or update the tags
		for tag in (tag.strip() for tag in ritem["tags"].split(",") if tag):
			anno_uri = "zeitgeist://tag/%s" % tag
			anno_id, discard, discard = self._get_ids(anno_uri, None, None)
			anno_item = self._store_item(anno_id, Content.TAG.id,
                                       Source.USER_ACTIVITY.id, tag)
			try:
				_annotation.add(item_id=anno_id, subject_id=uri_id)
			except sqlite3.IntegrityError:
				pass # Tag already registered
		
		# Set the item as bookmarked, if it should be
		if ritem["bookmark"]:
			anno_uri = "zeitgeist://bookmark/%s" % ritem["uri"]
			anno_id, discard, discard = self._get_ids(anno_uri, None, None)
			anno_item = self._store_item(anno_id, Content.BOOKMARK.id,
				Source.USER_ACTIVITY.id, u"Bookmark")
			try:
				_annotation.add(item_id=anno_id, subject_id=uri_id)
			except sqlite3.IntegrityError:
				pass # Item already bookmarked
		
		# Do not update the application nor insert the event if `force' is
		# True, ie., if we are updating an existing item.
		if force:
			return 2 if event_exists else 1
		
		# Insert the application
		if ritem["app"] in self._applications:
			app_uri_id = self._applications[ritem["app"]]
		elif ritem["app"]:
			app_uri_id = None
			try:
				app_uri_id = _app.add(info=ritem["app"])				
			except sqlite3.IntegrityError:
				pass
			if not app_uri_id:
				row = _apps.find_one(_app.id, _app.info == ritem["app"])
				if row : app_uri_id = row["item_id"]
	
			if app_uri_id :
				self._applications[ritem["app"]] = app_uri_id
			else:
				log.warn("Unable to create or lookup app: %s" % ritem["app"])
		else:
			# No application specified:
			app_uri_id = 0
		
		# Insert the event
		e_id, e_content_id, e_subject_id = self._get_ids(event_uri, ritem["use"], None)
		e_item = self._store_item(e_id, e_content_id, Source.USER_ACTIVITY.id, u"Activity")
		try:
			_event.add(item_id=e_id, subject_id=uri_id,
						start=ritem["timestamp"], app_id=app_uri_id)				
		except sqlite3.IntegrityError:
			# This shouldn't happen.
			log.exception("Couldn't insert event into DB.")
		
		if commit:
			self.cursor.connection.commit()
		
		return 1
		
	def insert_events(self, items):
		"""
		Inserts items into the database and returns those items which were
		successfully inserted. If an item fails, that's usually because it
		already was in the database.
		"""
		result = super(ZeitgeistEngine, self).insert_events(items)
		self.cursor.connection.commit()
		return result
	
	def get_item(self, uri):
		""" Returns basic information about the indicated URI. As we are
			fetching an item, and not an event, `timestamp' is 0 and `use'
			and `app' are empty strings."""
		
		item = self.cursor.execute("""
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
			""", (Content.BOOKMARK.id, Content.TAG.id, unicode(uri))).fetchone()
		
		return item # Fixme: this is really an sqlite3.Row that acts as a dict
	
	def find_events(self, min=0, max=sys.maxint, limit=0,
			sorting_asc=True, mode="event", filters=(), return_mode=0):
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
		
		Possible values for return_mode, which is an internal variable
		not exposed in the API:
		 - 0: Return the events/items.
		 - 1: Return the amount of events/items which would be returned.
		 - 2: Return only the applications for the matching events.
		"""
		
		time1 = time.time()
		
		# Emulate optional arguments for the D-Bus interface
		if not max:
			max = sys.maxint
		if not mode:
			mode = "event"
		
		if not mode in ("event", "item", "mostused"):
			raise ValueError, \
				"Bad find_events call: mode \"%s\" not recongized." % mode
		
		# filters is a list of dicts, where each dict can have the following items:
		#   name: <str>
		#   uri: <str>
		#   tags: <list> of <str>
		#   mimetypes: <list> of <str>
		#   source: <list> of <str>
		#   content: <list> of <str>
		#   bookmarked: <bool> (True means bookmarked items, and vice versa
		expressions = []
		additional_args = []
		for filter in filters:
			invalid_filter_keys = set(filter.keys()) - self.ALLOWED_FILTER_KEYS
			if invalid_filter_keys:
				raise KeyError, "Invalid key(s) for filter in FindEvents: %s" %\
					", ".join(invalid_filter_keys)
			filterset = []
			if "name" in filter:
				filterset += [ "main_item.text LIKE ? ESCAPE \"\\\"" ]
				additional_args += [ filter["name"] ]
			if "uri" in filter:
				filterset += [ "uri.value LIKE ? ESCAPE \"\\\"" ]
				additional_args += [ filter["uri"] ]
			if "tags" in filter:
				if not hasattr(filter["tags"], "__iter__"):
					raise TypeError, "Expected a container type, found %s" % \
						type(filter["tags"])
				for tag in filter["tags"]:
					filterset += [ "(tags == \"%s\" OR tags LIKE \"%s, %%\" OR "
						"tags LIKE \"%%, %s, %%\" OR tags LIKE \"%%, %s\")" \
						% (tag, tag, tag, tag) ]
			if "mimetypes" in filter and len(filter["mimetypes"]):
				filterset += [ "(" + " OR ".join(
					["main_item.mimetype LIKE ? ESCAPE \"\\\""] * \
					len(filter["mimetypes"])) + ")" ]
				additional_args += filter["mimetypes"]
			if "source" in filter:
				filterset += [ "main_item.source_id IN (SELECT id "
					" FROM source WHERE value IN (%s))" % \
					",".join("?" * len(filter["source"])) ]
				additional_args += filter["source"]
			if "content" in filter:
				filterset += [ "main_item.content_id IN (SELECT id "
					" FROM content WHERE value IN (%s))" % \
					",".join("?" * len(filter["content"])) ]
				additional_args += filter["content"]
			if "application" in filter:
				filterset += [ "event.app_id IN (SELECT item_id "
					" FROM app WHERE info IN (%s))" % \
					",".join("?" * len(filter["application"])) ]
				additional_args += filter["application"]
			if "bookmarked" in filter:
				if filter["bookmarked"]:
					# Only get bookmarked items
					filterset += [ "bookmark == 1" ]
				else:
					# Only get items that aren't bookmarked
					filterset += [ "bookmark == 0" ]
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
				additional_orderby += " COUNT(event.rowid) DESC,"
		elif return_mode == 2:
			preexpressions += " , COUNT(event.app_id) AS app_count"
			expressions += " GROUP BY event.app_id"
			additional_orderby += " app_count DESC,"
		
		args = [ Content.BOOKMARK.id, Content.TAG.id, min, max ]
		args += additional_args
		args += [ limit or sys.maxint ]
		
		events = self.cursor.execute("""
			SELECT uri.value, event.start, main_item.id, content.value,
				"" AS use, source.value, main_item.origin, main_item.text,
				main_item.mimetype, main_item.icon,
				(SELECT info
					FROM app
					WHERE app.item_id = event.app_id
					) AS app,
				(SELECT COUNT(id)
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
				%s
			FROM item main_item
			INNER JOIN event ON (main_item.id = event.subject_id)
			INNER JOIN uri ON (uri.id = main_item.id)
			INNER JOIN content ON (content.id == main_item.content_id)
			INNER JOIN source ON (source.id == main_item.source_id)
			WHERE event.start >= ? AND event.start <= ? %s
			ORDER BY %s event.start %s LIMIT ?
			""" % (preexpressions, expressions, additional_orderby,
				"ASC" if sorting_asc else "DESC"), args).fetchall()
		
		if return_mode == 0:
			#result = map(EventDict.convert_result_to_dict, events)
			#result is a list of sqlite3.Rows, which each acts as a dict
			result = events
			time2 = time.time()
			log.debug("Fetched %s items in %.5f s." % (len(result), time2 - time1))
		elif return_mode == 1:
			# We could change the query above to "SELECT COUNT(*) FROM (...)",
			# where "..." is the complete query converted into a temporary
			# table, and get the result directly but there isn't enough of
			# a speed gain in doing that as that it'd be worth doing.
			result = len(events)
		elif return_mode == 2:
			# FIXME: What exactly are we returning here?
			return [(event[10], event[13]) for event in events]
		
		return result
	
	def update_items(self, items):
		""" Updates the given items, and their annotations, in the database. """
		# FIXME: This will remove *all* annotations, but only put back
        # the bookmarked status and the tags.
		self.delete_items([item["uri"] for item in items])
		
		for item in items:
			self.insert_event(item, force=True, commit=False)
		self.cursor.connection.commit()
		
		return items
	
	def delete_items(self, uris):
		uri_placeholder = ",".join("?" * len(uris))
		self.cursor.execute("""
			DELETE FROM annotation WHERE subject_id IN
				(SELECT id FROM uri WHERE value IN (%s))
			""" % uri_placeholder, uris, noresult=True)
		self.cursor.execute("""
			DELETE FROM item WHERE id IN
				(SELECT id FROM uri WHERE value IN (%s)) OR id IN
				(SELECT item_id FROM Annotation WHERE subject_id IN
					(SELECT id FROM uri WHERE value IN (%s)))
			""" % (uri_placeholder, uri_placeholder), uris * 2, noresult=True)
		self.cursor.connection.commit()
		return uris
	
	def get_types(self):
		"""
		Returns a list of all different types in the database.
		"""
		return [content["value"] for content in _contents.find("*")]
	
	def get_tags(self, min_timestamp=0, max_timestamp=0, limit=0, name_filter=""):
		"""
		Returns a list containing tuples with the name and the number of
		occurencies of the tags matching `name_filter', or all existing
		tags in case it's empty, sorted from most used to least used. `limit'
		can base used to limit the amount of results.
		
		Use `min_timestamp' and `max_timestamp' to limit the time frames you
		want to consider.
		"""
		# FIXME: Here we return a list of dicts (really sqlite.Rows), but
		#        should we reallu use Items - but they are only defined for Storm...
		result = self.cursor.execute("""
			SELECT item.text, (SELECT COUNT(rowid) FROM annotation
				WHERE annotation.item_id = item.id) AS amount
			FROM item
			WHERE item.id IN (SELECT annotation.item_id FROM annotation
				INNER JOIN event ON (event.subject_id = annotation.subject_id)
				WHERE event.start >= ? AND event.start <= ?)
				AND item.content_id = ? AND item.text LIKE ? ESCAPE "\\"
			ORDER BY amount DESC LIMIT ?
			""", (min_timestamp, max_timestamp or sys.maxint, Content.TAG.id,
			name_filter or "%", limit or sys.maxint)).fetchall()
		return map(lambda x : (x[0], x[1]), result)
	
	def get_last_insertion_date(self, application):
		"""
		Returns the timestamp of the last item which was inserted
		related to the given application. If there is no such record,
		0 is returned.
		"""
		
		query = self.cursor.execute("""
			SELECT start FROM event
			WHERE app_id = (SELECT item_id FROM app WHERE info = ?)
			ORDER BY start DESC LIMIT 1
			""", (application,)).fetchone()
		return query["start"] if query else 0
	
	def close(self):
		reset()
		self.cursor = None
	
	def is_closed(self):
		return self.cursor is None
		

