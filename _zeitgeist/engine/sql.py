# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009-2010 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
# Copyright © 2009 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
# Copyright © 2009 Markus Korn <thekorn@gmx.net>
# Copyright © 2009 Seif Lotfy <seif@lotfy.com>
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
import logging

from _zeitgeist.engine import constants

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("zeitgeist.sql")

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
	
	# actor
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
		CREATE TABLE IF NOT EXISTS event (
			id INTEGER,
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
			CONSTRAINT interpretation_fk FOREIGN KEY(interpretation)
				REFERENCES interpretation(id) ON DELETE CASCADE,
			CONSTRAINT manifestation_fk FOREIGN KEY(manifestation)
				REFERENCES manifestation(id) ON DELETE CASCADE,
			CONSTRAINT actor_fk FOREIGN KEY(actor)
				REFERENCES actor(id) ON DELETE CASCADE,
			CONSTRAINT payload_fk FOREIGN KEY(payload)
				REFERENCES payload(id) ON DELETE CASCADE,
			CONSTRAINT subj_id_fk FOREIGN KEY(subj_id)
				REFERENCES uri(id) ON DELETE CASCADE,
			CONSTRAINT subj_interpretation_fk FOREIGN KEY(subj_interpretation)
				REFERENCES interpretation(id) ON DELETE CASCADE,
			CONSTRAINT subj_manifestation_fk FOREIGN KEY(subj_manifestation)
				REFERENCES manifestation(id) ON DELETE CASCADE,
			CONSTRAINT subj_origin_fk FOREIGN KEY(subj_origin)
				REFERENCES uri(id) ON DELETE CASCADE,
			CONSTRAINT subj_mimetype_fk FOREIGN KEY(subj_mimetype)
				REFERENCES mimetype(id) ON DELETE CASCADE,
			CONSTRAINT subj_text_fk FOREIGN KEY(subj_text)
				REFERENCES text(id) ON DELETE CASCADE,
			CONSTRAINT subj_storage_fk FOREIGN KEY(subj_storage)
				REFERENCES storage(id) ON DELETE CASCADE,
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

	# Foreign key constraints don't work in SQLite. Yay!
	for table, columns in (
	('interpretation', ('interpretation', 'subj_interpretation')),
	('manifestation', ('manifestation', 'subj_manifestation')),
	('actor', ('actor',)),
	('payload', ('payload',)),
	('mimetype', ('subj_mimetype',)),
	('text', ('subj_text',)),
	('storage', ('subj_storage',)),
	):
		for column in columns:
			cursor.execute("""
				CREATE TRIGGER IF NOT EXISTS fkdc_event_%(column)s
				BEFORE DELETE ON event
				WHEN ((SELECT COUNT(*) FROM event WHERE %(column)s=OLD.%(column)s) < 2)
				BEGIN
					DELETE FROM %(table)s WHERE id=OLD.%(column)s;
				END;
				""" % {'column': column, 'table': table})

	# ... special cases
	cursor.execute("""
		CREATE TRIGGER IF NOT EXISTS fkdc_event_uri_1
		BEFORE DELETE ON event
		WHEN ((SELECT COUNT(*) FROM event WHERE subj_id=OLD.subj_id OR subj_origin=OLD.subj_id) < 2)
		BEGIN
			DELETE FROM uri WHERE id=OLD.subj_id;
		END;
		""" % {'column': column, 'table': table})
	cursor.execute("""
		CREATE TRIGGER IF NOT EXISTS fkdc_event_uri_2
		BEFORE DELETE ON event
		WHEN ((SELECT COUNT(*) FROM event WHERE subj_id=OLD.subj_origin OR subj_origin=OLD.subj_origin) < 2)
		BEGIN
			DELETE FROM uri WHERE id=OLD.subj_origin;
		END;
		""" % {'column': column, 'table': table})

	# TODO: Make the DROP conditional to version upgrades. How?
	cursor.execute("DROP VIEW IF EXISTS event_view")
	cursor.execute("""
		CREATE VIEW IF NOT EXISTS event_view AS
			SELECT event.id,
				event.timestamp,
				event.interpretation,
				event.manifestation,
				event.actor,
				(SELECT value FROM payload WHERE payload.id=event.payload)
					AS payload,
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
		dbfile = constants.DATABASE_FILE
		_cursor = create_db(dbfile)
	return _cursor
def unset_cursor():
	global _cursor
	_cursor = None

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

class WhereClause:
	"""
	This class provides a convenient representation a SQL `WHERE' clause,
	composed of a set of conditions joined together.
	
	The relation between conditions can be either of type *AND* or *OR*, but
	not both. To create more complex clauses, use several :class:`WhereClause`
	instances and joining them together using :meth:`extend`.
	
	Instances of this class can then be used to obtain a line of SQL code and
	a list of arguments, for use with the SQLite3 module, accessing the
	appropriate properties:
		>>> where.sql, where.arguments
	"""
	
	AND = " AND "
	OR = " OR "
	
	def __init__(self, relation):
		self._conditions = []
		self.arguments = []
		self._relation = relation
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
	
	def extend(self, where):
		self.add(where.sql, where.arguments)
		if not where.may_have_results():
			if self._relation == self.AND:
				self.clear()
			self.register_no_result()
	
	@property
	def sql(self):
		if self: # Do not return "()" if there are no conditions
			return "(" + self._relation.join(self._conditions) + ")"
	
	def register_no_result(self):
		self._no_result_member = True
	
	def may_have_results(self):
		"""
		Return False if we know from our cached data that the query
		will give no results.
		"""
		return len(self._conditions) > 0 or not self._no_result_member
	
	def clear(self):
		"""
		Reset this WhereClause to the state of a newly created one.
		"""
		self._conditions = []
		self.arguments = []
		self._no_result_member = False
