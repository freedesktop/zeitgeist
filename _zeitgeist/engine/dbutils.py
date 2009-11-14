# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Markus Korn <thekorn@gmx.de>
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

from _zeitgeist.lrucache import *
from _zeitgeist.engine.querymancer import *

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
		self._CACHE = LRUCache(600)
		self._INV_CACHE = LRUCache(600)
	
	def lookup_by_id (self, id):
		"""
		Look up an entity given its id
		"""
		if id is None:
			raise ValueError("Looking up %s without a id" % self)
		
		try:
			return self._INV_CACHE[id]
		except KeyError:
			pass # We didn't have it cached; fall through and handle it below
		
		row = self._cursor.execute("""SELECT value FROM %s WHERE id=?""" % self.get_name(), (id,)).fetchone()
		if row :			
			ent = Entity(id, row[0])
			self._INV_CACHE[id] = ent
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
		
		row = self._cursor.execute("""SELECT id FROM %s WHERE value=?""" % self.get_name(), (value,)).fetchone()
		if row:
			ent = Entity(row[0], value)
			self._CACHE[value] = ent
			return ent
		return None
	
	def lookup_id(self, value):
		"""
		Look up the id of a value. Returns -1 if the value doesn't exist
		"""
		ent = self.lookup(value)
		return ent.id if ent else -1
	
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
		
		row = self.find_one("*", self.value == value)
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


