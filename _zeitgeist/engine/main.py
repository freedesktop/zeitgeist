# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
# Copyright © 2009-2010 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
# Copyright © 2009-2011 Seif Lotfy <seif@lotfy.com>
# Copyright © 2009 Markus Korn <thekorn@gmx.net>
# Copyright © 2011 Collabora Ltd.
# 		      By Seif Lotfy <seif@lotfy.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 2.1 of the License, or
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
import logging
from collections import defaultdict

from zeitgeist.datamodel import Event as OrigEvent, StorageState, TimeRange, \
	ResultType, get_timestamp_for_now, Interpretation, Symbol, NEGATION_OPERATOR, WILDCARD
from _zeitgeist.engine.datamodel import Event, Subject
from _zeitgeist.engine.extension import ExtensionsCollection, get_extensions
from _zeitgeist.engine import constants
from _zeitgeist.engine.sql import get_default_cursor, unset_cursor, \
	TableLookup, WhereClause
from _zeitgeist.lrucache import LRUCache

log = logging.getLogger("zeitgeist.engine")

# we only allow replacement of half of the cache at once.
MAX_CACHE_BATCH_SIZE = constants.CACHE_SIZE/2

class NegationNotSupported(ValueError):
	pass

class WildcardNotSupported(ValueError):
	pass

def parse_negation(kind, field, value, parse_negation=True):
	"""checks if value starts with the negation operator,
	if value starts with the negation operator but the field does
	not support negation a ValueError is raised.
	This function returns a (value_without_negation, negation)-tuple
	"""
	negation = False
	if parse_negation and value.startswith(NEGATION_OPERATOR):
		negation = True
		value = value[len(NEGATION_OPERATOR):]
	if negation and field not in kind.SUPPORTS_NEGATION:
		raise NegationNotSupported("This field does not support negation")
	return value, negation
	
def parse_wildcard(kind, field, value):
	"""checks if value ends with the a wildcard,
	if value ends with a wildcard but the field does not support wildcards
	a ValueError is raised.
	This function returns a (value_without_wildcard, wildcard)-tuple
	"""
	wildcard = False
	if value.endswith(WILDCARD):
		wildcard = True
		value = value[:-len(WILDCARD)]
	if wildcard and field not in kind.SUPPORTS_WILDCARDS:
		raise WildcardNotSupported("This field does not support wildcards")
	return value, wildcard
	
def parse_operators(kind, field, value):
	"""runs both (parse_negation and parse_wildcard) parser functions
	on query values, and handles the special case of Subject.Text correctly.
	returns a (value_without_negation_and_wildcard, negation, wildcard)-tuple
	"""
	try:
		value, negation = parse_negation(kind, field, value)
	except ValueError:
		if kind is Subject and field == Subject.Text:
			# we do not support negation of the text field,
			# the text field starts with the NEGATION_OPERATOR
			# so we handle this string as the content instead
			# of an operator
			negation = False
		else:
			raise
	value, wildcard = parse_wildcard(kind, field, value)
	return value, negation, wildcard


class ZeitgeistEngine:
	
	def __init__ (self):
		self._cursor = cursor = get_default_cursor()
		
		# Find the last event id we used, and start generating
		# new ids from that offset
		max_id = cursor.execute("SELECT MAX(id) FROM event").fetchone()[0]
		min_id = cursor.execute("SELECT MIN(id) FROM event").fetchone()[0]
		self._last_event_id = max_id or 0
		if min_id == 0:
			# old database version raise an error for now,
			# maybe just change the id to self._last_event_id + 1
			# looking closer at the old code, it seems like
			# no event ever got an id of 0, but we should leave this check
			# to be 100% sure.
			raise RuntimeError("old database version")
		
		# Load extensions
		default_extensions = get_extensions()
		self.__extensions = ExtensionsCollection(self,
		                                         defaults=default_extensions)
		
		self._interpretation = TableLookup(cursor, "interpretation")
		self._manifestation = TableLookup(cursor, "manifestation")
		self._mimetype = TableLookup(cursor, "mimetype")
		self._actor = TableLookup(cursor, "actor")
		self._event_cache = LRUCache(constants.CACHE_SIZE)
	
	@property
	def extensions(self):
		return self.__extensions
	
	def close(self):
		log.debug("Closing down the zeitgeist engine...")
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
			# Try to get event attributes from row using the attributed field id
			# If attribute does not exist we break the attribute fetching and return
			# None instead of of crashing
			try:
				setattr(event, field, getattr(self, "_" + field).value(row[field]))
			except KeyError, e:
				log.error("Event %i broken: Table %s has no id %i" \
						%(row["id"], field, row[field]))
				return None
		event.payload = row["payload"] or "" # default payload: empty string
		return event
	
	def _get_subject_from_row(self, row):
		subject = Subject()
		for field in ("uri", "text", "storage", "current_uri"):
			setattr(subject, field, row["subj_" + field])
		setattr(subject, "origin", row["subj_origin_uri"])
		for field in ("interpretation", "manifestation", "mimetype"):
			# Try to get subject attributes from row using the attributed field id
			# If attribute does not exist we break the attribute fetching and return
			# None instead of crashing
			try:
				setattr(subject, field,
					getattr(self, "_" + field).value(row["subj_" + field]))
			except KeyError, e:
				log.error("Event %i broken: Table %s has no id %i" \
						%(row["id"], field, row["subj_" + field]))
				return None
		return subject
	
	def get_events(self, ids, sender=None):
		"""
		Look up a list of events.
		"""
		
		t = time.time()
		
		if not ids:
			return []
		
		# Split ids into cached and uncached
		uncached_ids = []
		cached_ids = []
		
		# If ids batch greater than MAX_CACHE_BATCH_SIZE ids ignore cache
		use_cache = True
		if len(ids) > MAX_CACHE_BATCH_SIZE:
			use_cache = False
		if not use_cache:
			uncached_ids = ids
		else:
			for id in ids:
				if id in self._event_cache:
					cached_ids.append(id)
				else:
					uncached_ids.append(id)
		
		id_hash = defaultdict(list)
		for n, id in enumerate(ids):
			# the same id can be at multible places (LP: #673916)
			# cache all of them
			id_hash[id].append(n)
		
		# If we are not able to get an event by the given id
		# append None instead of raising an Error. The client
		# might simply have requested an event that has been
		# deleted
		events = {}
		sorted_events = [None]*len(ids)
		
		for id in cached_ids:
			event = self._event_cache[id]
			if event:
				event = self.extensions.apply_get_hooks(event, sender)
				if event is not None:
					for n in id_hash[event.id]:
						# insert the event into all necessary spots (LP: #673916)
						sorted_events[n] = event
		
		# Get uncached events
		rows = self._cursor.execute("""
			SELECT * FROM event_view
			WHERE id IN (%s)
			""" % ",".join("%d" % id for id in uncached_ids)).fetchall()
		
		log.debug("Got %d raw events in %fs" % (len(rows), time.time()-t))
		t = time.time()
		
		t_get_event = 0
		t_get_subject = 0
		t_apply_get_hooks = 0
		
		for row in rows:
			# Assumption: all rows of a same event for its different
			# subjects are in consecutive order.
			t_get_event -= time.time()
			event = self._get_event_from_row(row)
			t_get_event += time.time()
			
			if event:
				# Check for existing event.id in event to attach 
				# other subjects to it
				if event.id not in events:
					events[event.id] = event
				else:
					event = events[event.id]
					
				t_get_subject -= time.time()
				subject = self._get_subject_from_row(row)
				t_get_subject += time.time()
				# Check if subject has a proper value. If none than something went
				# wrong while trying to fetch the subject from the row. So instead
				# of failing and raising an error. We silently skip the event.
				if subject:
					event.append_subject(subject)
					if use_cache and not event.payload:
						self._event_cache[event.id] = event
					t_apply_get_hooks -= time.time()
					event = self.extensions.apply_get_hooks(event, sender)
					t_apply_get_hooks += time.time()
					if event is not None:
						for n in id_hash[event.id]:
							# insert the event into all necessary spots (LP: #673916)
							sorted_events[n] = event
					# Avoid caching events with payloads to have keep the cache MB size 
					# at a decent level
					

		log.debug("Got %d events in %fs" % (len(sorted_events), time.time()-t))
		log.debug("    Where time spent in _get_event_from_row in %fs" % (t_get_event))
		log.debug("    Where time spent in _get_subject_from_row in %fs" % (t_get_subject))
		log.debug("    Where time spent in apply_get_hooks in %fs" % (t_apply_get_hooks))
		return sorted_events
	
	@staticmethod
	def _build_templates(templates):
		for event_template in templates:
			event_data = event_template[0]
			for subject in (event_template[1] or (Subject(),)):
				yield Event((event_data, [], None)), Subject(subject)
	
	def _build_sql_from_event_templates(self, templates):
	
		where_or = WhereClause(WhereClause.OR)
		
		for template in templates:
			event_template = Event((template[0], [], None))
			if template[1]:
				subject_templates = [Subject(data) for data in template[1]]
			else:
				subject_templates = None
			
			subwhere = WhereClause(WhereClause.AND)
			
			if event_template.id:
				subwhere.add("id = ?", event_template.id)
			
			try:
				value, negation, wildcard = parse_operators(Event, Event.Interpretation, event_template.interpretation)
				# Expand event interpretation children
				event_interp_where = WhereClause(WhereClause.OR, negation)
				for child_interp in (Symbol.find_child_uris_extended(value)):
					if child_interp:
						event_interp_where.add_text_condition("interpretation",
						                       child_interp, like=wildcard, cache=self._interpretation)
				if event_interp_where:
					subwhere.extend(event_interp_where)
				
				value, negation, wildcard = parse_operators(Event, Event.Manifestation, event_template.manifestation)
				# Expand event manifestation children
				event_manif_where = WhereClause(WhereClause.OR, negation)
				for child_manif in (Symbol.find_child_uris_extended(value)):
					if child_manif:
						event_manif_where.add_text_condition("manifestation",
						                      child_manif, like=wildcard, cache=self._manifestation)
				if event_manif_where:
					subwhere.extend(event_manif_where)
				
				value, negation, wildcard = parse_operators(Event, Event.Actor, event_template.actor)
				if value:
					subwhere.add_text_condition("actor", value, wildcard, negation, cache=self._actor)
				
				if subject_templates is not None:
					for subject_template in subject_templates:
						value, negation, wildcard = parse_operators(Subject, Subject.Interpretation, subject_template.interpretation)
						# Expand subject interpretation children
						su_interp_where = WhereClause(WhereClause.OR, negation)
						for child_interp in (Symbol.find_child_uris_extended(value)):
							if child_interp:
								su_interp_where.add_text_condition("subj_interpretation",
													child_interp, like=wildcard, cache=self._interpretation)
						if su_interp_where:
							subwhere.extend(su_interp_where)
						
						value, negation, wildcard = parse_operators(Subject, Subject.Manifestation, subject_template.manifestation)
						# Expand subject manifestation children
						su_manif_where = WhereClause(WhereClause.OR, negation)
						for child_manif in (Symbol.find_child_uris_extended(value)):
							if child_manif:
								su_manif_where.add_text_condition("subj_manifestation",
												   child_manif, like=wildcard, cache=self._manifestation)
						if su_manif_where:
							subwhere.extend(su_manif_where)
						
						# FIXME: Expand mime children as well.
						# Right now we only do exact matching for mimetypes
						# thekorn: this will be fixed when wildcards are supported
						value, negation, wildcard = parse_operators(Subject, Subject.Mimetype, subject_template.mimetype)
						if value:
							subwhere.add_text_condition("subj_mimetype",
										 value, wildcard, negation, cache=self._mimetype)
				
						for key in ("uri", "origin", "text"):
							value = getattr(subject_template, key)
							if value:
								value, negation, wildcard = parse_operators(Subject, getattr(Subject, key.title()), value)
								subwhere.add_text_condition("subj_%s" %key, value, wildcard, negation)
						
						if subject_template.storage:
							subwhere.add_text_condition("subj_storage", subject_template.storage)
						
			except KeyError, e:
				# Value not in DB
				log.debug("Unknown entity in query: %s" % e)
				where_or.register_no_result()
				continue
			where_or.extend(subwhere) 
		return where_or
	
	def _build_sql_event_filter(self, time_range, templates, storage_state):
		
		# FIXME: We need to take storage_state into account
		if storage_state != StorageState.Any:
			raise NotImplementedError
		
		# thekorn: we are using the unary operator here to tell sql to not use
		# the index on the timestamp column at the first place. This `fix` for
		# (LP: #672965) is based on some benchmarks, which suggest a performance
		# win, but we might not oversee all implications.
		# (see http://www.sqlite.org/optoverview.html section 6.0)
		where = WhereClause(WhereClause.AND)
		min_time, max_time = time_range
		if min_time != 0:
			where.add("+timestamp >= ?", min_time)
		if max_time != sys.maxint:
			where.add("+timestamp <= ?", max_time)
		
		where.extend(self._build_sql_from_event_templates(templates))
		
		return where
	
	def _find_events(self, return_mode, time_range, event_templates,
		storage_state, max_events, order, sender=None):
		"""
		Accepts 'event_templates' as either a real list of Events or as
		a list of tuples (event_data, subject_data) as we do in the
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
		elif return_mode == 1:
			sql = "SELECT id FROM event_view"
		else:
			raise NotImplementedError, "Unsupported return_mode."
		
		if order == ResultType.OldestActor:
			sql += """
				NATURAL JOIN (
					SELECT actor, min(timestamp) AS timestamp
					FROM event_view %s
					GROUP BY actor)
				""" % ("WHERE " + where.sql if where.sql else "")
		elif where:
			sql += " WHERE " + where.sql
		
		sql += (" ORDER BY timestamp DESC",
			" ORDER BY timestamp ASC",
			# thekorn: please note, event.subj_id == uri.id, as in
			# the subj_id points directly to an entry in the uri table,
			# so we are in fact grouping by subj_uris here
			" GROUP BY subj_id ORDER BY timestamp DESC",
			" GROUP BY subj_id ORDER BY timestamp ASC",
			" GROUP BY subj_id ORDER BY COUNT(subj_id) DESC, timestamp DESC",
			" GROUP BY subj_id ORDER BY COUNT(subj_id) ASC, timestamp ASC",
			" GROUP BY actor ORDER BY COUNT(actor) DESC, timestamp DESC", 
			" GROUP BY actor ORDER BY COUNT(actor) ASC, timestamp ASC",
			" GROUP BY actor ORDER BY timestamp DESC",
			" GROUP BY actor ORDER BY timestamp ASC",
			" GROUP BY subj_origin ORDER BY timestamp DESC",
			" GROUP BY subj_origin ORDER BY timestamp ASC",
			" GROUP BY subj_origin ORDER BY COUNT(subj_origin) DESC, timestamp DESC",
			" GROUP BY subj_origin ORDER BY COUNT(subj_origin) ASC, timestamp ASC",
			" GROUP BY actor ORDER BY timestamp ASC",
			" GROUP BY subj_interpretation ORDER BY timestamp DESC",
			" GROUP BY subj_interpretation ORDER BY timestamp ASC",
			" GROUP BY subj_interpretation ORDER BY COUNT(subj_interpretation) DESC",
			" GROUP BY subj_interpretation ORDER BY COUNT(subj_interpretation) ASC",
			" GROUP BY subj_mimetype ORDER BY timestamp DESC",
			" GROUP BY subj_mimetype ORDER BY timestamp ASC",
			" GROUP BY subj_mimetype ORDER BY COUNT(subj_mimetype) DESC",
			" GROUP BY subj_mimetype ORDER BY COUNT(subj_mimetype) ASC")[order]
		
		if max_events > 0:
			sql += " LIMIT %d" % max_events
		
		result = self._cursor.execute(sql, where.arguments).fetchall()
		
		if return_mode == 0:
			log.debug("Found %d event IDs in %fs" % (len(result), time.time()- t))
			result = [row[0] for row in result]
		elif return_mode == 1:
			log.debug("Found %d events IDs in %fs" % (len(result), time.time()- t))
			result = self.get_events(ids=[row[0] for row in result], sender=sender)	
		else:
			raise Exception("%d" % return_mode)
		
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
		"""
		
		if result_type in (0, 1):
			# Instead of using sliding windows we will be using a graph representation

			t1 = time.time()
			
			# We pick out the ids for relational event so we can set them as roots
			# the ids are taken from the events that match the events_templates
			ids = self._find_events(0, timerange, event_templates,
					result_storage_state, 0, ResultType.LeastRecentEvents)
			
			# Pick out the result_ids for the filtered results we would like to take into account
			# the ids are taken from the events that match the result_event_templates
			# if no result_event_templates are set we consider all results as allowed
			result_ids = []
			if len(result_event_templates) > 0:
				result_ids = self._find_events(0, timerange, result_event_templates,
						result_storage_state, 0, ResultType.LeastRecentEvents)
			
			# From here we create several graphs with the maximum depth of 2
			# and push all the nodes and vertices (events) in one pot together
			# FIXME: the depth should be adaptable 
			pot = []
			for id in ids:
				for x in xrange(id-2,id+3):
					if len(result_ids) == 0 or x in result_ids:
						pot.append(x)
			
			# Out of the pot we get all respected events and count which uris occur most
			rows = self._cursor.execute("""
				SELECT id, timestamp, subj_uri FROM event_view
				WHERE id IN (%s)
				""" % ",".join("%d" % id for id in pot)).fetchall()
			
			subject_uri_counter = defaultdict(int)
			latest_uris = defaultdict(int)
			for id, timestamp, uri in rows:
				if id not in ids:
					subject_uri_counter[uri] += 1
					if latest_uris[uri] < timestamp:
						latest_uris[uri] = timestamp
							
			log.debug("FindRelatedUris: Finished ranking subjects %fs." % \
				(time.time()-t1))
			
			if result_type == 0:
				sets = subject_uri_counter.iteritems()
			elif result_type == 1:
				sets = ((k, latest_uris[k]) for k in subject_uri_counter)
				
			sets = sorted(sets, reverse=True, key=lambda x: x[1])[:num_results]
			return map(lambda result: result[0], sets)
		else:
			raise NotImplementedError, "Unsupported ResultType."
			

	def insert_events(self, events, sender=None):
		t = time.time()
		m = map(lambda e: self._insert_event_without_error(e, sender), events)
		self._cursor.connection.commit() 
		log.debug("Inserted %d events out of %d in %fs"\
				 % (len([e for e in m if e>0]), len(m), time.time()-t))
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
		if not event.interpretation == Interpretation.MOVE_EVENT:
			for subject in event.subjects:
				if not subject.uri == subject.current_uri:
					raise ValueError("Illegal event: unless event.interpretation is 'MOVE_EVENT' \
						then subject.uri and subject.current_uri have to be the same")
		if event.interpretation == Interpretation.MOVE_EVENT:
			for subject in event.subjects:
				if subject.uri == subject.current_uri:
					raise ValueError("Redundant event: event.interpretation indicates the uri has \
						been moved yet the subject.uri and subject.current_uri are identical")
			
		id = self.next_event_id()
		event[0][Event.Id] = id		
		event = self.extensions.apply_pre_insert(event, sender)
		if event is None:
			raise AssertionError("Inserting of event was blocked by an extension")
		elif not issubclass(type(event), OrigEvent):
			raise ValueError("cannot insert object of type %r" %type(event))		
		
		payload_id = self._store_payload (event)
		
		# Make sure all URIs are inserted
		_origin = [subject.origin for subject in event.subjects if subject.origin]
		_current_uri = [subject.current_uri
			for subject in event.subjects if subject.current_uri]
		self._cursor.execute("INSERT OR IGNORE INTO uri (value) %s"
			% " UNION ".join(["SELECT ?"] * (len(event.subjects) +
				len(_origin) + len(_current_uri))),
			[subject.uri for subject in event.subjects] + _origin + _current_uri)
		
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
					INSERT INTO event (
						id, timestamp, interpretation, manifestation, actor,
						origin, payload, subj_id, subj_id_current,
						subj_interpretation, subj_manifestation, subj_origin,
						subj_mimetype, subj_text, subj_storage
					) VALUES (
						?, ?, ?, ?, ?, ?, ?,
						(SELECT id FROM uri WHERE value=?),
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
						None, # event origin
						payload_id,
						subject.uri,
						subject.current_uri,
						self._interpretation[subject.interpretation],
						self._manifestation[subject.manifestation],
						subject.origin,
						self._mimetype[subject.mimetype],
						subject.text,
						subject.storage))
			
			self.extensions.apply_post_insert(event, sender)
			
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
		
		if event.interpretation == Interpretation.MOVE_EVENT:
			for subject in event.subjects:
				self._cursor.execute("""
					UPDATE event
					SET subj_id_current=(SELECT id FROM uri WHERE value=?)
					WHERE subj_id_current=(SELECT id FROM uri WHERE value=?)
						AND interpretation!=?
						""", (subject.current_uri, subject.uri,
							self._interpretation[Interpretation.MOVE_EVENT]))
			# The cache has to be updated
			for id, c_event in self._event_cache:
				for i, c_subject in enumerate(c_event.subjects):
					if c_subject.current_uri == subject.uri and \
						not c_event.interpretation == Interpretation.MOVE_EVENT:
						self._event_cache[id].subjects[i].current_uri = subject.current_uri
						
		return id
	
	def _store_payload (self, event):
		# TODO: Rigth now payloads are not unique and every event has its
		# own one. We could optimize this to store those which are repeated
		# for different events only once, especially considering that
		# events cannot be modified once they've been inserted.
		if event.payload:
			# TODO: For Python >= 2.6 bytearray() is much more efficient
			# than this hack...
			# We need binary encoding that sqlite3 will accept, for
			# some reason sqlite3 can not use array.array('B', event.payload)
			payload = sqlite3.Binary("".join(map(str, event.payload)))
			self._cursor.execute(
				"INSERT INTO payload (value) VALUES (?)", (payload,))
			return self._cursor.lastrowid
		else:
			# Don't use None here, as that'd be inserted literally into the DB
			return ""

	def delete_events (self, ids, sender=None):
		ids = self.extensions.apply_pre_delete(ids, sender)
		# Extract min and max timestamps for deleted events
		self._cursor.execute("""
			SELECT MIN(timestamp), MAX(timestamp)
			FROM event
			WHERE id IN (%s)
		""" % ",".join(str(int(_id)) for _id in ids))
		timestamps = self._cursor.fetchone()

		# Remove events from cache
		for id in ids:
			if id in self._event_cache:
				del self._event_cache[id]
		
		# Make sure that we actually found some events with these ids...
		# We can't do all(timestamps) here because the timestamps may be 0
		if timestamps and timestamps[0] is not None and timestamps[1] is not None:
			self._cursor.execute("DELETE FROM event WHERE id IN (%s)"
				% ",".join(["?"] * len(ids)), ids)
			self._cursor.connection.commit()
			log.debug("Deleted %s" % map(int, ids))
			
			self.extensions.apply_post_delete(ids, sender)
			return timestamps
		else:
			log.debug("Tried to delete non-existing event(s): %s" % map(int, ids))
			return None
