# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
# Copyright © 2009 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
# Copyright © 2009 Seif Lotfy <seif@lotfy.com>
# Copyright © 2009 Markus Korn <thekorn@gmx.net>

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

from zeitgeist.datamodel import Subject as _Subject, Event as _Event
from zeitgeist.datamodel import Content, Source, Mimetype
import _zeitgeist.engine
from _zeitgeist.engine.dbutils import *
from _zeitgeist.engine.engine_base import BaseEngine
from _zeitgeist.engine.querymancer import *
from _zeitgeist.lrucache import *

import commands
commands.getoutput("espeak EAT THIS")

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("zeitgeist.engine")

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
			 subj_storage INTEGER,
			 CONSTRAINT unique_event UNIQUE (timestamp, interpretation, manifestation, actor, subj_id)
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
				(SELECT value FROM uri WHERE uri.id=event.subj_id)
					AS subj_uri,
				event.subj_interpretation,
				event.subj_manifestation,
				(SELECT value FROM uri WHERE uri.id=event.subj_origin)
					AS subj_origin,
				event.subj_mimetype,
				(SELECT value FROM text WHERE text.id = event.subj_text)
					AS subj_text,
				(SELECT value FROM storage
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
	Mimetype._clear_cache()  # FIXME: Renamings in datamodel module
	Content.bind_database(_interpretation) # FIXME: Renamings in datamodel module
	Source.bind_database(_manifestation) # FIXME: Renamings in datamodel module
	Mimetype.bind_database(_mimetype)
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


class Event(_Event):
	
	@classmethod
	def from_dbrow(cls, row):
		obj = cls()
		# id property is read-only in the public API
		obj[0][cls.Id] = row["id"]
		obj.timestamp = row["timestamp"]
		obj.interpretation = Source.get(
			_interpretation.lookup_by_id(row["interpretation"]).value
		)
		obj.manifestation = Content.get(
			_manifestation.lookup_by_id(row["manifestation"]).value
		)
		obj.actor = row["actor"]
		obj.payload = row["payload"]
		return obj

class Subject(_Subject):
	
	@classmethod
	def from_dbrow(cls, row):
		obj = cls()
		obj.uri = row["subj_uri"]
		obj.interpretation = Content.get(
			_interpretation.lookup_by_id(row["subj_interpretation"]).value
		)
		obj.manifestation = Source.get(
			_manifestation.lookup_by_id(row["subj_manifestation"]).value
		)
		
		obj.origin = row["subj_origin"]
		obj.mimetype = Mimetype.get(
			_mimetype.lookup_by_id(row["subj_mimetype"]).value
		)
		obj.text = row["subj_text"]
		obj.storage = row["subj_storage_state"]
		return obj

# This class is not compatible with the normal Zeitgeist BaseEngine class
class ZeitgeistEngine:
	
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
	
	def close(self):
		global _cursor
		self._cursor.connection.close()
		_cursor = None
		
	
	def is_closed(self):
		return self._cursor is None
	
	def next_event_id (self):
		self._last_event_id += 1
		return self._last_event_id
	
	def get_events(self, ids):
		"""
		Look up a list of events.
		"""
		global _cursor
		# FIXME: Determine if using our caches instead of SQLite subselects
		#        is in fact faster
		
		rows = _cursor.execute("""
			SELECT * FROM event_view
			WHERE id IN (%s)
			""" % ",".join(["?" for id in ids]), ids).fetchall()
		events = {}
		for row in rows:
			# Assumption: all rows of a same event for its different
			# subjects are in consecutive order.
			event = Event.from_dbrow(row)
			if event.id not in events:
				events[event.id] = event
			events[event.id].append_subject(Subject.from_dbrow(row))
		
		# Sort events into the requested order
		sorted_events = []
		for id in ids:
			# if we are not able to get an event by the given id
			# append None instead of raising an Error
			sorted_events.append(events.get(id, None))
		return sorted_events
	
	def insert_events (self, events):
		return map (self.insert_event, events)
	
	def insert_event (self, event):
		global _cursor, _uri, _interpretation, _manifestation, _mimetype, \
			_actor, _text, _payload, _storage, _event
		
		# Transparently wrap DBus event structs as Event objects
		event = self._ensure_event_wrapping(event)
		
		if event.id:
			raise ValueError("Illegal event: Predefined event id")
		
		id = self.next_event_id()
		timestamp = event.timestamp
		inter_id = _interpretation.lookup_or_create(event.interpretation).id
		manif_id = _manifestation.lookup_or_create(event.manifestation).id
		actor_id = _actor.lookup_or_create(event.actor).id
		
		if event.payload:
			payload_id = _payload.add(value=event.payload)
		else:
			payload_id = None	
		
		for subj in event.subjects:
			suri_id = _uri.lookup_or_create(subj.uri).id
			sinter_id = _interpretation.lookup_or_create(subj.interpretation).id
			smanif_id = _manifestation.lookup_or_create(subj.manifestation).id
			sorigin_id = _uri.lookup_or_create(subj.origin).id
			smime_id = _mimetype.lookup_or_create(subj.mimetype).id
			stext_id = _text.lookup_or_create(subj.text).id if subj.text else None
			sstorage_id = _storage.lookup_or_create(subj.storage).id # FIXME: Storage is not an EntityTable
			
			# We store the event here because we need one row per subject
			#_event.set_cursor(EchoCursor())
			try:
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
			except sqlite3.IntegrityError:
				raise KeyError("Duplicate event detected")
		
		
		_cursor.connection.commit()
		
		return id
	
	def delete_events (self, ids):
		_event.delete(_event.id.in_collection(ids))
	
	def _ensure_event_wrapping(self, event):
		"""
		Ensure that 'event' and its subjects are properly
		wrapped in Event and Subject classes.
		
		This is useful for converting DBus input to our Event and
		Subject representations without an actual data marshalling step
		"""
		if not isinstance(event, Event):
			event = Event(event)
		for i in range(len(event.subjects)):
			subj = event.subjects[i]
			if not isinstance(subj, Subject):
				event.subjects[i] = Subject(subj)
		return event
	
	def _build_event_from_template(self, event_template):
		"""
		Convert a tuple with an (event,subject) pair into a real Event.
		The resulting Event is guaranteed to have exactly one Subject.
		If event_template is already an Event instance this method
		does nothing
		
		This is useful for converting DBus input to our Event and
		Subject representations without an actual data marshalling step
		"""
		if isinstance(event_template, Event) : return event_template
		
		ev = Event.new_for_data(event_template[0])
		subj = Subject(event_template[1])
		ev.append_subject(subj)
		
		return ev
	
	def find_eventids (self, time_range, event_templates, storage_state,
		max_events, order):
		"""
		Accepts 'event_templates' as either a real list of Events or as
		a list of tuples (event_data,subject_data) as we do in the
		DBus API
		"""
		
		global _cursor, _interpretation, _manifestation, _mimetype
		
		if storage_state:
			# we don't have any methods to find out about the storage state
			# so it is not implemented yet
			raise NotImplementedError
		
		# Convert the event_templates into proper Events if necessary
		event_templates = map(self._build_event_from_template, event_templates)
		
		where = WhereClause("AND")
		if time_range[0] > 0:
			where.add("timestamp >= ?", time_range[0])
		if time_range[1] > 0:
			where.add("timestamp <= ?", time_range[1])
		where_or = WhereClause("OR")
		for event_template in event_templates:
			# Make sure we have a subject, we might not have that
			# if we received a raw Event in the parameters
			subject_template = event_template.subjects[0] if event_template.subjects else Subject()
			
			subwhere = WhereClause("AND")
			if event_template.interpretation:
				subwhere.add("interpretation = ?",
					_interpretation.lookup(event_template.interpretation).id)
			if event_template.manifestation:
				subwhere.add("manifestation = ?",
					_manifestation.lookup(event_template.manifestation).id)
			if event_template.actor:
				subwhere.add("actor = (SELECT id FROM actor WHERE value=?)",
					int(event_template.actor))
			if subject_template.interpretation:
				subwhere.add("subj_interpretation = ?",
					_interpretation.lookup(subject_template.interpretation).id)
			if subject_template.manifestation:
				subwhere.add("subj_manifestation = ?",
					_manifestation.lookup(subject_template.manifestation).id)
			if subject_template.origin:
				subwhere.add("subj_origin = (SELECT id FROM actor WHERE value=?)",
					int(event_template.origin))
			if subject_template.mimetype:
				subwhere.add("subj_mimetype = ?",
					_mimetype.lookup(subject_template.mimetype).id)
			if subject_template.text:
				subwhere.add("subj_text = (SELECT id FROM text WHERE value=?)",
					int(event_template.text))
			where_or.add(subwhere.generate_condition(), subwhere.arguments)
		where.add(where_or.generate_condition(), where_or.arguments)
		
		events = []
		sql = "SELECT id FROM event_view"
		if where:
			sql += " WHERE " + where.generate_condition()
		
		sql += (" ORDER BY timestamp ASC",
			" ORDER BY timestamp DESC",
			" GROUP BY subj_uri ORDER BY timestamp ASC",
			" GROUP BY subj_uri ORDER BY timestamp DESC",
			" GROUP BY subj_uri ORDER BY COUNT(id), timestamp ASC",
			" GROUP BY subj_uri ORDER BY COUNT(id), timestamp DESC")[order]			
		
		if max_events > 0:
			sql += " LIMIT %d" % max_events
		
		return [row[0] for row in _cursor.execute(sql, where.arguments).fetchall()]
	
	def get_highest_timestamp_for_actor(self, actor):
		query = self._cursor.execute("""
			SELECT timestamp FROM event
			WHERE actor = (SELECT id FROM actor WHERE value = ?)
			ORDER BY timestamp DESC LIMIT 1
			""", (actor,)).fetchone()
		return query["timestamp"] if query else 0

class WhereClause:
	
	def __init__(self, relation):
		self._conditions = []
		self.arguments = []
		self._relation = " " + relation + " "
	
	def __len__(self):
		return len(self._conditions)
	
	def add(self, condition, arguments):
		if not condition:
			return
		self._conditions.append(condition)
		if not hasattr(arguments, "__iter__"):
			self.arguments.append(arguments)
		else:
			self.arguments.extend(arguments)
	
	def generate_condition(self):
		return self._relation.join(self._conditions)
