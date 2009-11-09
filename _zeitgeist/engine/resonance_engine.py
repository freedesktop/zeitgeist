# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
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
	This means URI, Interpretation, Manifestation, Text, Actor, and Mimetype
	"""
	
	def __init__ (self, table_name):
		"""Create a new EntityTable with table name 'table_name'"""		
		if table_name is None :
			raise ValueError("Can not create EntityTable with name None")
		
		Table.__init__(self, table_name, id=Integer(), value=String())
		self._CACHE = LRUBiCache(1000)
	
	def lookup_by_id (self, id):
		"""
		Look up an entity given its id
		"""
		if not value:
			raise ValueError("Looking up %s without a id" % self)
		
		try:
			return self._CACHE.lookup_by_value[id]
		except KeyError:
			pass # We didn't have it cached; fall through and handle it below
		
		row = self.find_one(self.value, self.id == id)
		if row :			
			ent = Entity(id, row[0])
			self._CACHE[value] = ent
			#log.debug("Found %s: %s" % (self, ent))
			return ent
		return None
	
	def lookup(self, value):
		"""Look up an entity by value, return None if the
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

class StatefulEntity (Entity) :
	"""
	A variant of an Entity that also has a 'state' member.
	Used by StatefulEntityTable
	"""
	def __init__(self, id, value, state):
		Entity.__init__ (self, id, value)
		self.state = state
	
	def __repr___ (self):
		return "%s (id: %s, state: %s)" % (self.value, self.id, self.state)

class StatefulEntityTable(Table):
	"""
	Generic base class for Tables that has an 'id', a 'value', and a 'state'
	column. This is primarily for the 'storage' table
	"""
	
	def __init__ (self, table_name):
		"""Create a new StatefulEntityTable with table name 'table_name'"""		
		if table_name is None :
			raise ValueError("Can not create EntityTable with name None")
		
		Table.__init__(self, table_name, id=Integer(), value=String(), state=Integer())
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
			ent = StatefulEntity(row[0], value, row[2])
			self._CACHE[value] = ent
			#log.debug("Found %s" % self)
			return ent
		return None
	
	def lookup_or_create(self, value, state=1):
		"""
		Find the entity matching the uri 'value' or create it if necessary.
		The default state is "available", ie. 1.
		"""
		ent = self.lookup(value)
		if ent : return ent
		
		try:
			row_id = self.add(value=value, state=state)
		except sqlite3.IntegrityError, e:
			log.warn("Unexpected integrity error when inserting %s %s: %s" % (self, value, e))
			return None
		
		# We can peek the last insert row id from SQLite,
		# this saves us a whole SELECT
		ent = StatefulEntity(row_id, value, state)
		self._CACHE[value] = ent
		#log.debug("Created %s" % self)
				
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
_actor = None           # id, string
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
	
	# storage, represented by a StatefulEntityTable
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS storage
			(id INTEGER PRIMARY KEY,
			 value VARCHAR UNIQUE,
			 state INTEGER)
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
			 payload INTEGER,
			 subj_id INTEGER,
			 subj_interpretation INTEGER,
			 subj_manifestation INTEGER,
 			 subj_origin INTEGER,
			 subj_mimetype INTEGER,
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
		CREATE INDEX IF NOT EXISTS event_subj_id
			ON event(subj_id)""")
	cursor.execute("""
		CREATE INDEX IF NOT EXISTS event_subj_interpretation
			ON event(subj_interpretation)""")
	cursor.execute("""
		CREATE INDEX IF NOT EXISTS event_subj_manifestation
			ON event(subj_manifestation)""")
	cursor.execute("""
		CREATE INDEX IF NOT EXISTS event_subj_origin
			ON event(subj_origin)""")
	cursor.execute("""
		CREATE INDEX IF NOT EXISTS event_subj_mimetype
			ON event(subj_mimetype)""")
	cursor.execute("""
		CREATE INDEX IF NOT EXISTS event_subj_text
			ON event(subj_text)""")
	cursor.execute("""
		CREATE INDEX IF NOT EXISTS event_subj_storage
			ON event(subj_storage)""")
	
	# event view (interpretation, manifestation and mimetype are cached in ZG)
	#cursor.execute("DROP VIEW event_view")
	cursor.execute("""
		CREATE VIEW IF NOT EXISTS event_view AS
			SELECT event.id,
				event.timestamp,
				event.interpretation,
				event.manifestation,
				(SELECT value FROM actor WHERE actor.id = event.actor) AS actor,
				event.payload,
				event.subj_id,
				event.subj_id,
				event.subj_interpretation,
				event.subj_manifestation,
				event.subj_origin,
				event.subj_mimetype,
				(SELECT value FROM text WHERE text.id = event.subj_text)
					AS subj_text,
				(SELECT state FROM storage
					WHERE storage.id=event.subj_storage) AS subj_storage_state
			FROM event
		""")

	# Table defs
	global _cursor, _uri, _interpretation, _manifestation, _mimetype, _actor, \
		_text, _payload, _storage, _event
	_cursor = cursor
	_uri = EntityTable("uri")
	_manifestation = EntityTable("manifestation")
	_interpretation = EntityTable("interpretation")
	_mimetype = EntityTable("mimetype")
	_actor = EntityTable("actor")
	_text = EntityTable("text")
	_payload = EntityTable("payload") # FIXME: Should have a Blob type value
	_storage = StatefulEntityTable("storage")
	
	# FIXME: _item.payload should be a BLOB type	
	_event = Table("event",
	               id=Integer(),
	               timestamp=Integer(),
	               interpretation=Integer(),
	               manifestation=Integer(),
	               actor=Integer(),	               
	               payload=Integer(),
	               subj_id=Integer(),
	               subj_interpretation=Integer(),
	               subj_manifestation=Integer(),
	               subj_origin=Integer(),
	               subj_mimetype=Integer(),
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
	Content._clear_cache() # FIXME: Renamings in datamodel module
	Source._clear_cache()  # FIXME: Renamings in datamodel module
	Content.bind_database(_interpretation) # FIXME: Renamings in datamodel module
	Source.bind_database(_manifestation) # FIXME: Renamings in datamodel module
	
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

# Thin wrapper for dict-like access, with fast symbolic lookups
# eg: ev[Name] (speed of array lookups rather than dict lookups)
class _FastDict:
	
	@classmethod
	def get_from_row(cls, row):
		obj = cls()
		obj._get(row)
		return obj
	
	def __init__ (self, data=None):
		if data:
			self._data = data
		else:
			self._data = []
			for i in self.Fields:
				self._data.append(None)
	
	def __getitem__ (self, offset):
		return self._data[offset]
	
	def __setitem__ (self, offset, value):
		self._data[offset] = value
		
	def _get(self, row):
		raise NotImplementedError

class Event(_FastDict):
	Fields = (Id,
		Timestamp,
		Interpretation,
		Manifestation,
		Actor,
		Payload,
		Subjects) = range(7)
	
	def _get(self, row):
		self[self.Id] = row["id"]
		self[self.Timestamp] = row["timestamp"]
		self[self.Interpretations] = _interpretation.lookup_by_id(row["interpretation"])
		self[self.Manifestation] = _manifestation.lookup_by_id(row["manifestation"])
		self[self.Actor] = row["actor"]
		self[self.Origin] = row["origin"]
		self[self.Payload] = row["payload"]
		self[self.Subjects] = []
	
	def append_subject(self, row=None):
		"""
		Append a new empty subject array and return a reference to
		the array.
		"""
		if self._data[self.Subjects] is None:
			self._data[self.Subjects] = []
		if row :
			if isinstance(row, Subject) : subj = row
			else : subj = Subject().get(row)			
		else:
			subj = Subject()
		self._data[Event.Subjects].append(subj)
		return subj

class Subject(_FastDict):
	Fields = (Uri,
		Interpretation,
		Manifestation,
		Origin,
		Mimetype,
		Text,
		Storage) = range(7)
	
	def _get(self, row):
		self[self.Uri] = row["subj_uri"]
		self[self.Interpretation] = _interpretation.lookup_by_id(row["subj_interpretation"])
		self[self.Manifestation] = _manifestation.lookup_by_id(row["subj_manifestation"])
		self[self.Origin] = row["subj_origin"]
		self[self.Mimetype] = _mimetype.lookup_by_id(row["subj_mimetype"])
		self[self.Text] = row["subj_text"]
		self[self.Storage] = row["subj_storage_state"]
		return self

# This class is not compatible with the normal Zeitgeist BaseEngine class
class ZeitgeistEngine :
	def __init__ (self):
		global _event
		self._cursor = get_default_cursor()
		
		# Find the last event id we used, and start generating
		# new ids from that offset
		row = _event.find("max(id)").fetchone()
		if row[0]:
			self._last_event_id = row[0]
		else:
			self._last_event_id = 0
	
	def next_event_id (self):
		self._last_event_id += 1
		return self._last_event_id
	
	def get_events(self, ids):
		"""
		Look up a list of events.
		"""
		global _cursor
		# FIXME: Determine if using our caches instead of SQLite JOINs
		#        is in fact faster
		
		rows = _cursor.execute("""
			SELECT * FROM event_view
			WHERE id IN (%s)
			""" % ",".join(["?" for id in ids]), ids).fetchall()
		events = {}
		for row in rows:
			# Assumption: all rows of a same event for its different
			# subjects are in consecutive order.
			event = Event.get_by_row(row)
			if event[Event.Id] not in events:
				events[event[Event.Id]] = event
			events[event[Event.Id]].append_subject(Subject.get_by_row(row))
		
		# Sort events into the requested order
		sorted_events = []
		for id in ids:
			sorted_events.append(events[id])
		return sorted_events
	
	def insert_events (self, events):
		return map (self.insert_event, events)
	
	def insert_event (self, event):
		global _cursor, _uri, _interpretation, _manifestation, _mimetype, _actor, _text, _payload, _storage, _event
		
		id = self.next_event_id()
		timestamp = event[Event.Timestamp]
		inter_id = _interpretation.lookup_or_create(event[Event.Interpretation]).id
		manif_id = _manifestation.lookup_or_create(event[Event.Manifestation]).id
		actor_id = _actor.lookup_or_create(event[Event.Actor]).id
		
		if event[Event.Payload]:
			payload_id = _payload.add(event[Event.Payload])
		else:
			payload_id = None		
		
		for subj in (event[Event.Subjects] or []) :
			suri_id = _uri.lookup_or_create(subj[Subject.Uri]).id
			sinter_id = _interpretation.lookup_or_create(subj[Subject.Interpretation]).id
			smanif_id = _manifestation.lookup_or_create(subj[Subject.Manifestation]).id
			sorigin_id = _uri.lookup_or_create(subj[Subject.Origin]).id
			smime_id = _mimetype.lookup_or_create(subj[Subject.Mimetype]).id
			stext_id = _text.lookup_or_create(subj[Subject.Text]).id
			sstorage_id = _storage.lookup_or_create(subj[Subject.Storage]).id # FIXME: Storage is not an EntityTable
			
			# We store the event here because we need one row per subject
			#_event.set_cursor(EchoCursor())
			_event.add(
				id=id,
				timestamp=timestamp,
				interpretation=inter_id,
				manifestation=manif_id,
				actor=actor_id,
				payload=payload_id,
				subj_id=suri_id,
				subj_interpretation=sinter_id,
				subj_manifestation=smanif_id,
				subj_origin=sorigin_id,
				subj_mimetype=smime_id,				
				subj_text=stext_id,
				subj_storage=sstorage_id)
		
		_cursor.connection.commit()
		return id
	
	def delete_events (self, uris):
		# FIXME
		pass

	def find_eventids (self,
			 time_range,
			 event_templates,
			 storage_state,
			 num_events,
			 order):
		# FIXME
		pass

class QueryCompiler :
	def __init__ (self):
		pass
	
	def compile (self, event_templates):
		"""
		Return and SQL query representation (as a string) of
		event_templates. The returned string will be suitable for
		embedding in an SQL WHERE-clause
		"""
	
	def compile_single_template (self, event_template):
		clauses = []
		if event_template[Event.Id] :
			clause.append("event.id = " + event_template[Event.Id])
