# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
# Copyright © 2009 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
# Copyright © 2009 Seif Lotfy <seif@lotfy.com>
# Copyright © 2009 Markus Korn <thekorn@gmx.net>
# Copyright © 2009 Alexander Gabriel <einalex@mayanna.org>

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

from extension import ExtensionsCollection

from zeitgeist.datamodel import Subject, Event, StorageState, TimeRange
import _zeitgeist.engine

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("zeitgeist.engine")

class UnicodeCursor(sqlite3.Cursor):
	
	@staticmethod
	def fix_unicode(obj):
		if isinstance(obj, str):
			obj = obj.decode("UTF-8")
		return unicode(obj)		
	
	def execute(self, statement, parameters=None):
		if parameters is not None:
			parameters = [self.fix_unicode(p) for p in parameters]
			return super(UnicodeCursor, self).execute(statement, parameters)
		else:
			return super(UnicodeCursor, self).execute(statement)

def create_db(file_path):
	"""Create the database and return a default cursor for it"""
	log.info("Using database: %s" % file_path)
	conn = sqlite3.connect(file_path)
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor(UnicodeCursor)
	
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
	# timestamps are integers (for now), if you would like to change it
	# please start a bugreport for it. In case we agree on this change
	# remember to also fix our unittests to reflect this change
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
	
	#cursor.execute("DROP VIEW event_view")
	cursor.execute("""
		CREATE VIEW IF NOT EXISTS event_view AS
			SELECT event.id,
				event.timestamp,
				event.interpretation,
				event.manifestation,
				event.actor,
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
					WHERE storage.id=event.subj_storage) AS subj_storage,
				(SELECT state FROM storage
					WHERE storage.id=event.subj_storage) AS subj_storage_state
			FROM event
		""")
	
	return cursor

_cursor = None
def get_default_cursor():
	global _cursor
	if not _cursor:
		dbfile = _zeitgeist.engine.DB_PATH
		_cursor = create_db(dbfile)
	return _cursor

class TableLookup(dict):
	
	# We are not using an LRUCache as pressumably there won't be thousands
	# of manifestations/interpretations/mimetypes/actors on most
	# installations, so we can save us the overhead of tracking their usage.
	
	def __init__(self, cursor, table):
		
		self._cursor = cursor
		self._table = table
		
		for row in cursor.execute("SELECT id, value FROM %s" % table):
			self[row["value"]] = row["id"]
		
		self._inv_dict = dict((value, key) for key, value in self.iteritems())
	
	def __getitem__(self, name):
		# Use this for inserting new properties into the database
		if name in self:
			super(TableLookup, self).__getitem__(name)
		try:
			self._cursor.execute(
			"INSERT INTO %s (value) VALUES (?)" % self._table, (name,))
			id = self._cursor.lastrowid
		except sqlite3.IntegrityError:
			# This shouldn't happen, but just in case
			# FIXME: Maybe we should remove it?
			id = self._cursor.execute("SELECT id FROM %s WHERE value=?"
				% self._table, (name,)).fetchone()[0]
		# If we are here it's a newly inserted value, insert it into cache
		self[name] = id
		self._inv_dict[id] = name
		return id
	
	def value(self, id):
		# When we fetch an event, it either was already in the database
		# at the time Zeitgeist started or it was inserted later -using
		# Zeitgeist-, so here we always have the data in memory already.
		return self._inv_dict[id]
	
	def id(self, name):
		# Use this when fetching values which are supposed to be in the
		# database already. Eg., in find_eventids.
		return super(TableLookup, self).__getitem__(name)

class ZeitgeistEngine:
	
	def __init__ (self):
		self._cursor = cursor = get_default_cursor()
		
		# Find the last event id we used, and start generating
		# new ids from that offset
		row = cursor.execute("SELECT MIN(id), MAX(id) FROM event").fetchone()
		self._last_event_id = row[1] if row[1] else 0
		if row[0] == 0:
			# old database version raise an error for now,
			# maybe just change the id to self._last_event_id + 1
			# looking closer at the old code, it seems like
			# no event ever got an id of 0, but we should leave this check
			# to be 100% sure.
			raise RuntimeError("old database version")
		
		# Load extensions
		# Right now we don't load any default extension
		self.__extensions = ExtensionsCollection(self)
		
		self._interpretation = TableLookup(cursor, "interpretation")
		self._manifestation = TableLookup(cursor, "manifestation")
		self._mimetype = TableLookup(cursor, "mimetype")
		self._actor = TableLookup(cursor, "actor")
	
	@property
	def extensions(self):
		return self.__extensions
	
	def close(self):
		global _cursor
		self._cursor.connection.close()
		self._cursor = _cursor = None
	
	def is_closed(self):
		return self._cursor is None
	
	def next_event_id (self):
		self._last_event_id += 1
		return self._last_event_id
	
	def _get_event_from_row(self, row):
		event = Event()
		event[0][Event.Id] = row["id"] # Id property is read-only in the public API
		event.timestamp = row["timestamp"]
		for field in ("interpretation", "manifestation", "actor"):
			setattr(event, field, getattr(self, "_" + field).value(row[field]))
		event.payload = row["payload"] or "" # default payload: empty string
		return event
	
	def _get_subject_from_row(self, row):
		subject = Subject()
		for field in ("uri", "origin", "text", "storage"):
			setattr(subject, field, row["subj_" + field])
		for field in ("interpretation", "manifestation", "mimetype"):
			setattr(subject, field,
				getattr(self, "_" + field).value(row["subj_" + field]))
		return subject
	
	def get_events(self, ids):
		"""
		Look up a list of events.
		"""
		
		t = time.time()
		
		rows = self._cursor.execute("""
			SELECT * FROM event_view
			WHERE id IN (%s)
			""" % ",".join("%d" % id for id in ids)).fetchall()
		events = {}
		for row in rows:
			# Assumption: all rows of a same event for its different
			# subjects are in consecutive order.
			event = self._get_event_from_row(row)
			if event.id not in events:
				events[event.id] = event
			events[event.id].append_subject(self._get_subject_from_row(row))
		
		# Sort events into the requested order
		sorted_events = []
		for id in ids:
			# if we are not able to get an event by the given id
			# append None instead of raising an Error. The client
			# might simply have requested an event that has been
			# deleted
			event = events.get(id, None)
			event = self.extensions.apply_get_hooks(event)
			
			sorted_events.append(event)
		
		log.debug("Got %d events in %fs" % (len(sorted_events), time.time()-t))

		return sorted_events
	
	@staticmethod
	def get_timestamp_for_now():
		"""
		Return the current time in milliseconds since the Unix Epoch
		"""
		return int(time.time() * 1000)
	
	def insert_events(self, events):
		t = time.time()
		m = map(self._insert_event_without_error, events)
		_cursor.connection.commit()
		log.debug("Inserted %d events in %fs" % (len(m), time.time()-t))
		return m
		
	def _insert_event_without_error(self, event):
		try:
			return self._insert_event(event)
		except Exception, e:
			log.exception("error while inserting '%r'" %event)
			return 0
	
	def _insert_event(self, event):
		if not isinstance(event, Event):
			raise ValueError("cannot insert object of type %r" %type(event))
		if event.id:
			raise ValueError("Illegal event: Predefined event id")
		if not event.subjects:
			raise ValueError("Illegal event format: No subject")
		if not event.timestamp:
			event.timestamp = self.get_timestamp_for_now()
		
		event = self.extensions.apply_insert_hooks(event)
		if event is None:
			raise AssertionError("Inserting of event was blocked by an extension")
		elif not isinstance(event, Event):
			raise ValueError("cannot insert object of type %r" %type(event))
		
		id = self.next_event_id()
		
		if event.payload:
			# TODO: Rigth now payloads are not unique and every event has its
			# own one. We could optimize this to store those which are repeated
			# for different events only once, especially considering that
			# events cannot be modified once they've been inserted.
			payload_id = self._cursor.execute(
				"INSERT INTO payload (value) VALUES (?)", event.payload)
			payload_id = self._cursor.lastrowid
		else:
			# Don't use None here, as that'd be inserted literally into the DB
			payload_id = ""
		
		# Make sure all URIs are inserted
		_origin = [subject.origin for subject in event.subjects if subject.origin]
		self._cursor.execute("INSERT OR IGNORE INTO uri (value) %s"
			% " UNION ".join(["SELECT ?"] * (len(event.subjects) + len(_origin))),
			[subject.uri for subject in event.subjects] + _origin)
		
		# Make sure all mimetypes are inserted
		_mimetype = [subject.mimetype for subject in event.subjects \
			if subject.mimetype and not subject.mimetype in self._mimetype]
		if len(_mimetype) > 1:
			self._cursor.execute("INSERT OR IGNORE INTO mimetype (value) %s"
				% " UNION ".join(["SELECT ?"] * len(_mimetype)), _mimetype)
		
		# Make sure all texts are inserted
		_text = [subject.text for subject in event.subjects if subject.text]
		if _text:
			self._cursor.execute("INSERT OR IGNORE INTO text (value) %s"
				% " UNION ".join(["SELECT ?"] * len(_text)), _text)
		
		# Make sure all storages are inserted
		_storage = [subject.storage for subject in event.subjects if subject.storage]
		if _storage:
			self._cursor.execute("INSERT OR IGNORE INTO storage (value) %s"
				% " UNION ".join(["SELECT ?"] * len(_storage)), _storage)
		
		try:
			for subject in event.subjects:	
				self._cursor.execute("""
					INSERT INTO event VALUES (
						?, ?, ?, ?, ?, ?,
						(SELECT id FROM uri WHERE value=?),
						?, ?,
						(SELECT id FROM uri WHERE value=?),
						?,
						(SELECT id FROM text WHERE value=?),
						(SELECT id from storage WHERE value=?)
					)""", (
						id,
						event.timestamp,
						self._interpretation[event.interpretation],
						self._manifestation[event.manifestation],
						self._actor[event.actor],
						payload_id,
						subject.uri,
						self._interpretation[subject.interpretation],
						self._manifestation[subject.manifestation],
						subject.origin,
						self._mimetype[subject.mimetype],
						subject.text,
						subject.storage))
		except sqlite3.IntegrityError:
			# The event was already registered.
			# Rollback _last_event_id and return the ID of the original event
			self._last_event_id -= 1
			self._cursor.execute("""
				SELECT id FROM event
				WHERE timestamp=? AND interpretation=? AND manifestation=?
					AND actor=?
				""", (event.timestamp,
					self._interpretation[event.interpretation],
					self._manifestation[event.manifestation],
					self._actor[event.actor]))
			return self._cursor.fetchone()[0]
		
		_cursor.connection.commit()
		
		return id
	
	def delete_events (self, ids):
		# Extract min and max timestamps for deleted events
		self._cursor.execute("""
			SELECT MIN(timestamp), MAX(timestamp)
			FROM event
			WHERE id IN (%s)
		""" % ",".join(["?"] * len(ids)), ids)
		min_stamp, max_stamp = self._cursor.fetchone()
	
		# FIXME: Delete unused interpretation/manifestation/text/etc.
		self._cursor.execute("DELETE FROM event WHERE id IN (%s)"
			% ",".join(["?"] * len(ids)), ids)
		
		return min_stamp, max_stamp
	
	def _build_templates(self, templates):
		for event_template in templates:
			event_data = event_template[0]
			for subject in (event_template[1] or (Subject(),)):
				yield Event((event_data, [], None)), Subject(subject)
	
	def find_eventids (self, time_range, event_templates, storage_state,
		max_events, order):
		"""
		Accepts 'event_templates' as either a real list of Events or as
		a list of tuples (event_data,subject_data) as we do in the
		DBus API
		"""
		
		t = time.time()
		
		# FIXME: We need to take storage_state into account
		if storage_state != StorageState.Any:
			raise NotImplementedError
		
		event_templates = list(self._build_templates(event_templates))
		
		where = WhereClause("AND")
		if time_range[0] > 0:
			where.add("timestamp >= ?", time_range[0])
		if time_range[1] > 0:
			where.add("timestamp <= ?", time_range[1])
		where_or = WhereClause("OR")

		for (event_template, subject_template) in event_templates:
			subwhere = WhereClause("AND")
			try:
				for key in ("interpretation", "manifestation", "actor"):
					value = getattr(event_template, key)
					if value:
						subwhere.add("%s = ?" % key,
							getattr(self, "_" + key).id(value))
				for key in ("interpretation", "manifestation", "mimetype"):
					value = getattr(subject_template, key)
					if value:
						subwhere.add("subj_%s = ?" % key,
							getattr(self, "_" + key).id(value))
			except KeyError:
				# Value not in DB
				where.register_no_result()
				continue
			for key in ("uri", "origin", "text"):
				value = getattr(subject_template, key)
				if value:
					subwhere.add("subj_%s = ?" % key, value)
			where_or.add(subwhere.generate_condition(), subwhere.arguments)
		where.add(where_or.generate_condition(), where_or.arguments)
		
		if not where.may_have_results():
			# We know from our cached data that the query will give no results
			return []
		
		sql = "SELECT DISTINCT id FROM event_view"
		if where:
			sql += " WHERE " + where.generate_condition()
		
		sql += (" ORDER BY timestamp DESC",
			" ORDER BY timestamp ASC",
			" GROUP BY subj_uri ORDER BY timestamp DESC",
			" GROUP BY subj_uri ORDER BY timestamp ASC",
			" GROUP BY subj_uri ORDER BY COUNT(id) DESC, timestamp DESC",
			" GROUP BY subj_uri ORDER BY COUNT(id) ASC, timestamp ASC")[order]
		
		if max_events > 0:
			sql += " LIMIT %d" % max_events
		log.debug(sql)
		log.debug("SQL args: %s" % where.arguments)
		
		result = [row[0] for row in self._cursor.execute(sql, where.arguments).fetchall()]
		
		log.debug("Fetched %d event IDs in %fs" % (len(result), time.time()- t))
		return result

class WhereClause:
	
	def __init__(self, relation):
		self._conditions = []
		self.arguments = []
		self._relation = " " + relation + " "
		self._no_result_member = False
	
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
		if self: # Do not return "()" if there are no conditions
			return "(" + self._relation.join(self._conditions) + ")"
	
	def register_no_result(self):
		self._no_result_member = True
	
	def may_have_results(self):
		return len(self._conditions) > 0 or not self._no_result_member
