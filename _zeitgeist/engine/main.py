# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
# Copyright © 2009-2010 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
# Copyright © 2009-2010 Seif Lotfy <seif@lotfy.com>
# Copyright © 2009 Markus Korn <thekorn@gmx.net>
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

from zeitgeist.datamodel import Event as OrigEvent, StorageState, TimeRange, \
	ResultType, get_timestamp_for_now, Interpretation
from _zeitgeist.engine.datamodel import Event, Subject	
from _zeitgeist.engine.extension import ExtensionsCollection, load_class
from _zeitgeist.engine import constants
from _zeitgeist.engine.sql import get_default_cursor, unset_cursor, \
	TableLookup, WhereClause

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("zeitgeist.engine")

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
		default_extensions = map(load_class, constants.DEFAULT_EXTENSIONS)
		self.__extensions = ExtensionsCollection(self,
			defaults=default_extensions)
		
		self._interpretation = TableLookup(cursor, "interpretation")
		self._manifestation = TableLookup(cursor, "manifestation")
		self._mimetype = TableLookup(cursor, "mimetype")
		self._actor = TableLookup(cursor, "actor")
	
	@property
	def extensions(self):
		return self.__extensions
	
	def close(self):
		self.extensions.unload()
		self._cursor.connection.close()
		self._cursor = None
		unset_cursor()
	
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
	
	def get_events(self, ids=None, rows=None, sender=None):
		"""
		Look up a list of events.
		"""
		
		t = time.time()
		
		if not ids and not rows:
			return []
		
		if ids:
			rows = self._cursor.execute("""
				SELECT * FROM event_view
				WHERE id IN (%s)
				""" % ",".join("%d" % id for id in ids)).fetchall()
		else:
			ids = (row[0] for row in rows)
		
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
			event = self.extensions.apply_get_hooks(event, sender)
			
			sorted_events.append(event)
		
		log.debug("Got %d events in %fs" % (len(sorted_events), time.time()-t))

		return sorted_events
	
	@staticmethod
	def _build_templates(templates):
		for event_template in templates:
			event_data = event_template[0]
			for subject in (event_template[1] or (Subject(),)):
				yield Event((event_data, [], None)), Subject(subject)
	
	def _build_sql_from_event_templates(self, templates):
	
		where_or = WhereClause(WhereClause.OR)
		
		for (event_template, subject_template) in self._build_templates(templates):
			subwhere = WhereClause(WhereClause.AND)
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
				where_or.register_no_result()
				continue
			for key in ("uri", "origin", "text"):
				value = getattr(subject_template, key)
				if value:
					subwhere.add("subj_%s = ?" % key, value)
			where_or.extend(subwhere)
		
		return where_or
	
	def _build_sql_event_filter(self, time_range, templates, storage_state):
		
		# FIXME: We need to take storage_state into account
		if storage_state != StorageState.Any:
			raise NotImplementedError
		
		where = WhereClause(WhereClause.AND)
		where.add("timestamp >= ?", time_range[0])
		where.add("timestamp <= ?", time_range[1])
		
		where.extend(self._build_sql_from_event_templates(templates))
		
		return where
	
	def _find_events(self, return_mode, time_range, event_templates,
		storage_state, max_events, order, sender=None):
		"""
		Accepts 'event_templates' as either a real list of Events or as
		a list of tuples (event_data,subject_data) as we do in the
		DBus API.
		
		Return modes:
		 - 0: IDs.
		 - 1: Events.
		"""
		
		t = time.time()
		
		where = self._build_sql_event_filter(time_range, event_templates,
			storage_state)
		if not where.may_have_results():
			return []
		
		if return_mode == 0:
			sql = "SELECT DISTINCT id FROM event_view"
		else:
			sql = "SELECT * FROM event_view"
		
		if order == ResultType.LeastRecentActor:
			sql += """
				NATURAL JOIN (
					SELECT actor, min(timestamp) AS timestamp
					FROM event_view
					GROUP BY actor)
				"""
		
		if where:
			sql += " WHERE " + where.sql
		
		sql += (" ORDER BY timestamp DESC",
			" ORDER BY timestamp ASC",
			" GROUP BY subj_uri ORDER BY timestamp DESC",
			" GROUP BY subj_uri ORDER BY timestamp ASC",
			" GROUP BY subj_uri ORDER BY COUNT(id) DESC, timestamp DESC",
			" GROUP BY subj_uri ORDER BY COUNT(id) ASC, timestamp ASC",
			" GROUP BY actor ORDER BY COUNT(id) DESC, timestamp DESC",
			" GROUP BY actor ORDER BY COUNT(id) ASC, timestamp ASC",
			" GROUP BY actor", # implicit: ORDER BY max(timestamp) DESC
			" ORDER BY timestamp ASC")[order]
		
		if max_events > 0:
			sql += " LIMIT %d" % max_events
		
		result = self._cursor.execute(sql, where.arguments).fetchall()
		
		if return_mode == 1:
			return self.get_events(rows=result, sender=sender)
		result = [row[0] for row in result]
		
		log.debug("Fetched %d event IDs in %fs" % (len(result), time.time()- t))
		return result
	
	def find_eventids(self, *args):
		return self._find_events(0, *args)
	
	def find_events(self, *args):
		return self._find_events(1, *args)
	
	def find_related_uris(self, timerange, event_templates, result_event_templates,
		result_storage_state, num_results, result_type):
		"""
		Return a list of subject URIs commonly used together with events
		matching the given template, considering data from within the indicated
		timerange.
		
		Only URIs for subjects matching the indicated `result_event_templates`
		and `result_storage_state` are returned.
		
		This currently uses a modified version of the Apriori algorithm, but
		the implementation may vary.
		"""
		
		#templates = event_templates + result_event_templates
		
		events = self.find_events(timerange, result_event_templates, 
											result_storage_state, 0, 1)
		
		subject_uris = []
		for event in event_templates:
			if len(event.subjects) > 0:
				if  not event.subjects[0].uri in subject_uris:
					subject_uris.append(event.subjects[0].uri)
		
		def create_buckets(events):
			"""
			Create buckets where a size of a bucket is limited by 30 minutes
			"""
			t = 0
			buckets = []
			for event in events:
				if int(event.timestamp) - 30*60000 > t:
					t = int(event.timestamp)
					buckets.append({})
				buckets[len(buckets)-1][event.subjects[0].uri] = event
			return buckets
		
		buckets = create_buckets(events)
		
		keys_counter  = {}
		
		for bucket in buckets:
			counter = 0
			for event in event_templates:
				if bucket.has_key(event.subjects[0].uri):
					counter += 1
					break
			if counter > 0:
				for key in bucket.keys():
					if not key in subject_uris:
						if not keys_counter.has_key(key):
							keys_counter[key] = 0
						keys_counter[key] += 1
		
		sets = [[v, k] for k, v in keys_counter.iteritems()]
		sets.sort()
		sets.reverse()
				
		results = []
		if result_type == 0:
			i = 0
			for r in sets:
				results.append(r[1])
				i +=1 
				if i >= num_results:
					break
		else:
			events = []
			for r in sets:
				event = Event()
				subject = Subject()
				subject.uri = r[1]
				event.set_subjects([subject])
				events.append(event)
			events = self.find_events(timerange, events, result_storage_state, num_results, 2)
			for event in events:   
				results.append(event.subjects[0].uri)
		return results
	
	def insert_events(self, events, sender=None):
		t = time.time()
		m = map(lambda e: self._insert_event_without_error(e, sender), events)
		self._cursor.connection.commit()
		log.debug("Inserted %d events in %fs" % (len(m), time.time()-t))
		return m
	
	def _insert_event_without_error(self, event, sender=None):
		try:
			return self._insert_event(event, sender)
		except Exception, e:
			log.exception("error while inserting '%r'" %event)
			return 0
	
	def _insert_event(self, event, sender=None):
		if not issubclass(type(event), OrigEvent):
			raise ValueError("cannot insert object of type %r" %type(event))
		if event.id:
			raise ValueError("Illegal event: Predefined event id")
		if not event.subjects:
			raise ValueError("Illegal event format: No subject")
		if not event.timestamp:
			event.timestamp = get_timestamp_for_now()
		
		event = self.extensions.apply_insert_hooks(event, sender)
		if event is None:
			raise AssertionError("Inserting of event was blocked by an extension")
		elif not issubclass(type(event), OrigEvent):
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
		
		self._cursor.connection.commit()
		
		return id
	
	def delete_events (self, ids):
		# Extract min and max timestamps for deleted events
		self._cursor.execute("""
			SELECT MIN(timestamp), MAX(timestamp)
			FROM event
			WHERE id IN (%s)
		""" % ",".join(["?"] * len(ids)), ids)
		timestamps = self._cursor.fetchone()
		
		if timestamps:
			# FIXME: Delete unused interpretation/manifestation/text/etc.
			self._cursor.execute("DELETE FROM event WHERE id IN (%s)"
				% ",".join(["?"] * len(ids)), ids)
		
		return timestamps
