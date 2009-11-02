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
from zeitgeist.dbusutils import Event, Item, Annotation

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
			#log.debug("Found %s: %s" % (self, ent))
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
		#log.debug("Created %s %s %s" % (self, ent.id, ent.value))
				
		return ent
	
	def _clear_cache(self):
		self._CACHE.clear()

#		
# Table defs are assigned in create_db()
#
_uri = None             # id, string
_interpretation = None  # id, string
_manifestation = None   # id, string
_mimetype = None        # id, string
_actor = None             # id, string
_text = None            # id, string
_payload = None         # id, blob
_storage = None         # id, value, available
_event = None           # ...


def create_db(file_path):
	"""Create the database and return a default cursor for it"""
	log.info("Creating database: %s" % file_path)
	conn = sqlite3.connect(file_path)
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	
	# uri
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS uri
			(id INTEGER PRIMARY KEY, value VARCHAR UNIQUE)
		""")
	cursor.execute("""
		CREATE UNIQUE INDEX IF NOT EXISTS uri_value ON uri(value)
		""")
	
	# interpretation
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS interpretation
			(id INTEGER PRIMARY KEY, value VARCHAR UNIQUE)
		""")
	cursor.execute("""
		CREATE UNIQUE INDEX IF NOT EXISTS interpretation_value
			ON interpretation(value)
		""")
	
	# manifestation
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS manifestation
			(id INTEGER PRIMARY KEY, value VARCHAR UNIQUE)
		""")
	cursor.execute("""
		CREATE UNIQUE INDEX IF NOT EXISTS manifestation_value
			ON manifestation(value)""")
	
	# mimetype
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS mimetype
			(id INTEGER PRIMARY KEY, value VARCHAR UNIQUE)
		""")
	cursor.execute("""
		CREATE UNIQUE INDEX IF NOT EXISTS mimetype_value
			ON mimetype(value)""")
	
	# app
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS actor
			(id INTEGER PRIMARY KEY, value VARCHAR UNIQUE)
		""")
	cursor.execute("""
		CREATE UNIQUE INDEX IF NOT EXISTS actor_value
			ON actor(value)""")
	
	# text
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS text
			(id INTEGER PRIMARY KEY, value VARCHAR UNIQUE)
		""")
	cursor.execute("""
		CREATE UNIQUE INDEX IF NOT EXISTS text_value
			ON text(value)""")
	
	# payload, there's no value index for payload,
	# they can only be fetched by id
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS payload
			(id INTEGER PRIMARY KEY, value BLOB)
		""")	
	
	# storage
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS storage
			(id INTEGER PRIMARY KEY,
			 value VARCHAR UNIQUE,
			 available INTEGER)
		""")
	cursor.execute("""
		CREATE UNIQUE INDEX IF NOT EXISTS storage_value
			ON storage(value)""")
	
	# event - the primary table for log statements
	# note that event.id is NOT unique, we can have multiple subjects per id
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS event
			(id INTEGER,
			 timestamp INTEGER,
			 interpretation INTEGER,
			 manifestation INTEGER,			 
			 actor INTEGER,
			 origin INTEGER,
			 payload INTEGER,
			 subj_id INTEGER,
			 subj_interpretation INTEGER,
			 subj_manifestation INTEGER,
			 subj_mimetype INTEGER,
			 subj_origin INTEGER,
			 subj_text INTEGER,
			 subj_storage INTEGER
			 )
		""")
	cursor.execute("""
		CREATE INDEX IF NOT EXISTS event_id
			ON event(id)""")
	cursor.execute("""
		CREATE INDEX IF NOT EXISTS event_timestamp
			ON event(timestamp)""")
	cursor.execute("""
		CREATE INDEX IF NOT EXISTS event_interpretation
			ON event(interpretation)""")
	cursor.execute("""
		CREATE INDEX IF NOT EXISTS event_manifestation
			ON event(manifestation)""")
	cursor.execute("""
		CREATE INDEX IF NOT EXISTS event_actor
			ON event(actor)""")
	cursor.execute("""
		CREATE INDEX IF NOT EXISTS event_origin
			ON event(origin)""")
	cursor.execute("""
		CREATE INDEX IF NOT EXISTS event_subj_id
			ON event(subj_id)""")
	cursor.execute("""
		CREATE INDEX IF NOT EXISTS event_subj_interpretation
			ON event(subj_interpretation)""")
	cursor.execute("""
		CREATE INDEX IF NOT EXISTS event_subj_manifestation
			ON event(subj_manifestation)""")
	cursor.execute("""
		CREATE INDEX IF NOT EXISTS event_subj_mimetype
			ON event(mimetyype)""")
	cursor.execute("""
		CREATE INDEX IF NOT EXISTS event_subj_origin
			ON event(subj_origin)""")
	cursor.execute("""
		CREATE INDEX IF NOT EXISTS event_subj_text
			ON event(subj_text)""")
	cursor.execute("""
		CREATE INDEX IF NOT EXISTS event_subj_storage
			ON event(subj_storage)""")
	# FIXME: Indexes on the event table
		
	# Table defs
	global _cursor, _uri, _interpretation, _manifestation, _mimetype, _actor, _text, _payload, _storage, _event
	_cursor = cursor
	_uri = EntityTable("uri")
	_manifestation = EntityTable("manifestation")
	_interpretation = EntityTable("interpretation")
	_mimetype = EntityTable("mimetype")
	_actor = EntityTable("actor")
	_text = EntityTable("text")
	_payload = EntityTable("payload") # FIXME: Should have a Blob type value
	_storage = Table("storage", id=Integer(), value=String(), available=Integer())
	
	# FIXME: _item.payload should be a BLOB type	
	_event = Table("event",
	               id=Integer(),
	               timestamp=Integer(),
	               interpretation=Integer(),
	               manifestation=Integer(),
	               app=Integer(),
	               origin=Integer(),
	               payload=Integer(),
	               subj_id=Integer(),
	               subj_interpretation=Integer(),
	               subj_manifestation=Integer(),
	               subj_mimetype=Integer(),
	               subj_origin=Integer(),
	               subj_text=Integer(),
	               subj_storage=Integer())
	
	_uri.set_cursor(_cursor)
	_interpretation.set_cursor(_cursor)
	_manifestation.set_cursor(_cursor)
	_mimetype.set_cursor(_cursor)
	_actor.set_cursor(_cursor)
	_text.set_cursor(_cursor)
	_payload.set_cursor(_cursor)
	_storage.set_cursor(_cursor)
	_event.set_cursor(_cursor)

	# Bind the db into the datamodel module
	Content._clear_cache()
	Source._clear_cache()
	Content.bind_database(_interpretation)
	Source.bind_database(_manifestation)
	
	return cursor

_cursor = None
def get_default_cursor():
	global _cursor
	if not _cursor:
		dbfile = _zeitgeist.engine.DB_PATH
		_cursor = create_db(dbfile)
	return _cursor

def set_cursor(cursor):
	global _cursor, _uri, _interpretation, _manifestation, _mimetype, _actor, _text, _payload, _storage, _event
	
	if _cursor :		
		_cursor.close()
	
	_uri.set_cursor(_cursor)
	_interpretation.set_cursor(_cursor)
	_manifestation.set_cursor(_cursor)
	_mimetype.set_cursor(_cursor)
	_actor.set_cursor(_cursor)
	_text.set_cursor(_cursor)
	_payload.set_cursor(_cursor)
	_storage.set_cursor(_cursor)
	_event.set_cursor(_cursor)

def reset():
	global _cursor, _uri, _interpretation, _manifestation, _mimetype, _actor, _text, _payload, _storage, _event
	
	if _cursor :		
		_cursor.connection.close()
	
	_cursor = None
	_uri = None
	_interpretation = None
	_manifestation = None	
	_mimetype = None	
	_actor = None
	_text = None
	_payload = None
	_storage = None
	_event = None

# Thin wrapper for event data, with fast symbolic lookups
# like ev.origin (speed of tuple lookups rather than dict lookups)
class Event :
	(uri,
	 timestamp,
	 interpretation,
	 manifestation,
	 actor,
	 origin,
	 subjects,
	 subj_interpretation,
	 subj_manifestation,
	 subj_mimetype,
	 subj_origin,
	 subj_text) = range (12)
	 
	 def __init__ (self, data_tuple):
	 	self._data = data_tuple
	 
	 def __getattr__ (self, key):
	 	return self._data[key]
	 
	 

# This class is not compatible with the normal Zeitgeist BaseEngine class
class Engine :
	def __init__ (self):
		self._cursor = get_default_cursor()
	
	def get_events (self, uris):
		if not uris : return []
		# FIXME escape quotes in 'uris' to avoid SQL injection
		sql = "SELECT * FROM event WHERE value IN ('" + "', '".join(uris) + "')"
		return self._cursor.execute(sql)
	
	def insert_events (self, events):
		map (self.insert_event, events)
	
	def insert_event (self, event):
		global _cursor, _uri, _interpretation, _manifestation, _mimetype, _actor, _text, _payload, _storage, _event
		# TODO insert event
	
	def delete_events (self, uris):
		pass
	
	def find_events (self,
			 time_ranges,
			 event_templates,
			 filter_available,
			 with_result_set,
			 result_set_to_close,			 
			 num_events,
			 order):
		pass

