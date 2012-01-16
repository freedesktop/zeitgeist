# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009-2010 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
# Copyright © 2009 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
# Copyright © 2009-2011 Markus Korn <thekorn@gmx.net>
# Copyright © 2009 Seif Lotfy <seif@lotfy.com>
# Copyright © 2011 J.P. Lacerda <jpaflacerda@gmail.com>
# Copyright © 2011 Collabora Ltd.
#             By Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
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
import logging
import time
import os
import shutil

from constants import constants

log = logging.getLogger("siis.zeitgeist.sql")

TABLE_MAP = {
	"origin": "uri",
	"subj_mimetype": "mimetype",
	"subj_origin": "uri",
	"subj_uri": "uri",
	"subj_current_uri": "uri",
}

def explain_query(cursor, statement, arguments=()):
	plan = ""
	for r in cursor.execute("EXPLAIN QUERY PLAN "+statement, arguments).fetchall():
		plan += str(list(r)) + "\n"
	log.debug("Got query:\nQUERY:\n%s (%s)\nPLAN:\n%s" % (statement, arguments, plan))

class UnicodeCursor(sqlite3.Cursor):
	
	debug_explain = os.getenv("ZEITGEIST_DEBUG_QUERY_PLANS")
	
	@staticmethod
	def fix_unicode(obj):
		if isinstance(obj, (int, long)):
			# thekorn: as long as we are using the unary operator for timestamp
			# related queries we have to make sure that integers are not
			# converted to strings, same applies for long numbers.
			return obj
		if isinstance(obj, str):
			obj = obj.decode("UTF-8")
		# seif: Python’s default encoding is ASCII, so whenever a character with
		# an ASCII value > 127 is in the input data, you’ll get a UnicodeDecodeError
		# because that character can’t be handled by the ASCII encoding.
		try:
			obj = unicode(obj)
		except UnicodeDecodeError, ex:
			pass
		return obj
	
	def execute(self, statement, parameters=()):
		parameters = [self.fix_unicode(p) for p in parameters]
		if UnicodeCursor.debug_explain:
			explain_query(super(UnicodeCursor, self), statement, parameters)
		return super(UnicodeCursor, self).execute(statement, parameters)

	def fetch(self, index=None):
		if index is not None:
			for row in self:
				yield row[index]
		else:
			for row in self:
				yield row

def _get_schema_version (cursor, schema_name):
	"""
	Returns the schema version for schema_name or returns 0 in case
	the schema doesn't exist.
	"""
	try:
		schema_version_result = cursor.execute("""
			SELECT version FROM schema_version WHERE schema=?
		""", (schema_name,))
		result = schema_version_result.fetchone()
		return result[0] if result else 0
	except sqlite3.OperationalError, e:
		# The schema isn't there...
		log.debug ("Schema '%s' not found: %s" % (schema_name, e))
		return 0

def _connect_to_db(file_path):
	conn = sqlite3.connect(file_path)
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor(UnicodeCursor)
	return cursor

_cursor = None
def get_default_cursor():
	global _cursor
	if not _cursor:
		dbfile = constants.DATABASE_FILE
		start = time.time()
		log.info("Using database: %s" % dbfile)
		new_database = not os.path.exists(dbfile)
		_cursor = _connect_to_db(dbfile)
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
			return super(TableLookup, self).__getitem__(name)
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
		
	def remove_id(self, id):
		value = self.value(id)
		del self._inv_dict[id]
		del self[value]
		
def get_right_boundary(text):
	""" returns the smallest string which is greater than `text` """
	if not text:
		# if the search prefix is empty we query for the whole range
		# of 'utf-8 'unicode chars
		return unichr(0x10ffff)
	if isinstance(text, str):
		# we need to make sure the text is decoded as 'utf-8' unicode
		text = unicode(text, "UTF-8")
	charpoint = ord(text[-1])
	if charpoint == 0x10ffff:
		# if the last character is the biggest possible char we need to
		# look at the second last
		return get_right_boundary(text[:-1])
	return text[:-1] + unichr(charpoint+1)

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
	NOT = "NOT "
	
	@staticmethod
	def optimize_glob(column, table, prefix):
		"""returns an optimized version of the GLOB statement as described
		in http://www.sqlite.org/optoverview.html `4.0 The LIKE optimization`
		"""
		if isinstance(prefix, str):
			# we need to make sure the text is decoded as 'utf-8' unicode
			prefix = unicode(prefix, "UTF-8")
		if not prefix:
			# empty prefix means 'select all', no way to optimize this
			sql = "SELECT %s FROM %s" %(column, table)
			return sql, ()
		elif all([i == unichr(0x10ffff) for i in prefix]):
			sql = "SELECT %s FROM %s WHERE value >= ?" %(column, table)
			return sql, (prefix,)
		else:
			sql = "SELECT %s FROM %s WHERE (value >= ? AND value < ?)" %(column, table)
			return sql, (prefix, get_right_boundary(prefix))
	
	def __init__(self, relation, negation=False):
		self._conditions = []
		self.arguments = []
		self._relation = relation
		self._no_result_member = False
		self._negation = negation
	
	def __len__(self):
		return len(self._conditions)
	
	def add(self, condition, arguments=None):
		if not condition:
			return
		self._conditions.append(condition)
		if arguments is not None:
			if not hasattr(arguments, "__iter__"):
				self.arguments.append(arguments)
			else:
				self.arguments.extend(arguments)
			
	def add_text_condition(self, column, value, like=False, negation=False, cache=None):
		if like:
			assert column in ("origin", "subj_uri", "subj_current_uri",
			"subj_origin", "actor", "subj_mimetype"), \
				"prefix search on the %r column is not supported by zeitgeist" % column
			if column == "subj_uri":
				# subj_id directly points to the id of an uri entry
				view_column = "subj_id"
			elif column == "subj_current_uri":
				view_column = "subj_id_current"
			else:
				view_column = column
			optimized_glob, value = self.optimize_glob("id", TABLE_MAP.get(column, column), value)
			sql = "%s %sIN (%s)" %(view_column, self.NOT if negation else "", optimized_glob)
			if negation:
				sql += " OR %s IS NULL" % view_column
		else:
			if column == "origin":
				column ="event_origin_uri"
			elif column == "subj_origin":
				column = "subj_origin_uri"
			sql = "%s %s= ?" %(column, "!" if negation else "")
			if cache is not None:
				value = cache[value]
		self.add(sql, value)
	
	def extend(self, where):
		self.add(where.sql, where.arguments)
		if not where.may_have_results():
			if self._relation == self.AND:
				self.clear()
			self.register_no_result()
	
	@property
	def sql(self):
		if self: # Do not return "()" if there are no conditions
			negation = self.NOT if self._negation else ""
			return "%s(%s)" %(negation, self._relation.join(self._conditions))
	
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
