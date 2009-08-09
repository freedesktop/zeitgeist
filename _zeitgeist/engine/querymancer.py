# -.- encoding: utf-8 -.-

# Querymancer - Super simple lightweight ORM inspired by Storm
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

"""
This module contains a very simple and light query builder for SQL databases,
primarily SQLite. It is written to be mostly compatible with the nice syntax of
the full featured Storm ORM.

The premise of Querymancer is to only provide syntactic sugar and explicitly
not do any caching or hidden tricks. That is left for the consumer. Another
high priority goal is to keep it light. This means that we try to avoid object
allocations where ever possible, and that some nice validations (like type
safety) are omitted.

The primary class for utilizing Querymancer is the L{Table} class - which
also provides a good point to start learning about Querymancer.
"""

#
# TODO:
#
# * Use qmark substitution in query building to enabled prepared statements
# * Fix SQL injection (will be fixed implicitly by the point above)
#

class ColumnType:
	"""
	Base class for all data types held in a L{Table}. This class is an abstract
	class and can not be instantiated directly.
	"""
	__eq_template__ = "%s = %s"
	__ne_template__ = "%s != %s"
	__gt_template__ = "%s > %s"
	__ge_template__ = "%s >= %s"
	__lt_template__ = "%s < %s"
	__le_template__ = "%s <= %s"
	__like_template__ = "%s LIKE %s"
	
	def __init__ (self):
		if self.__class__ == ColumnType:
			raise TypeError("ColumnType is an abstract class and can not be "
							"instantiated directly")
		
		self._table = None
		self._name = None
	
	def __eq__(self, other):
		return self.__class__.__eq_template__ % (self,
												 self.__class__.format(other))

	def __ne__(self, other):
		return self.__class__.__ne_template__ % (self,
												 self.__class__.format(other))

	def __gt__(self, other):
		return self.__class__.__gt_template__ % (self,
												 self.__class__.format(other))

	def __ge__(self, other):
		return self.__class__.__ge_template__ % (self,
												 self.__class__.format(other))

	def __lt__(self, other):
		return self.__class__.__lt_template__ % (self,
												 self.__class__.format(other))

	def __le__(self, other):
		return self.__class__.__le_template__ % (self,
												 self.__class__.format(other))
	
	def _set_table (self, table):
		self._table = table
	
	def _set_colname (self, name):
		self._name = name
	
	def __str__ (self):
		return "%s.%s" % (self._table, self._name)
	
	def like (self, other):
		return self.__class__.__like_template__ % (self,
												   self.__class__.format(other))
	
	@classmethod
	def format (klass, value):
		"""
		Format a data type of this class for inclusion in a query. For strings
		this means adding quotes around it, integers needs conversion to strings
		etc.
		"""
		return str(value)
	
class Integer(ColumnType):
	"""
	Basic data type for an integer
	"""

class String(ColumnType):
	"""
	Basic data type for a string
	"""
	@classmethod
	def format(klass, value):
		# Escape quotes to avoid SQL injection
		return "'%s'" % value.replace("'", "\\'")
	
class EchoCursor:
	"""
	Dummy cursor used when no cursor has been installed on a L{Table} via
	L{Table.set_cursor}.
	"""
	def execute(self, stmt):
		print "EchoCursor:", stmt

class Table:
	"""
	Primary class which everything revolves about. You declare a
	table with a name and the columns that you want to use. Assume you have
	earlier created a table 'customers' like:
	
	    CREATE TABLE customers (name VARCHAR, debt INT)
	
	To create a C{Table} instance for this table use:
	
	    customers = Table("customers", name = String(), debt = Integer())
	
	Before you can start using the C{customers} instance you need to install
	a cursor for it using L{set_cursor}. It is an explicit goal of Querymancer
	not to do this automagically.
	
	You can now query or update the C{customers} table via the methods
	L{find}, L{update}, and {add}.
	"""
	def __init__ (self, name, **colspecs):
		"""
		Create a new C{Table} instance for the table given by C{name}.
		The columns to use on this table are given by C{colname = DataType()}
		pairs, like:
		
		    Table("customers", name = String(), debt = Integer())
		
		Before you can use a C{Table} you need to install a C{Cursor} for it
		by calling L{set_cursor}.
		
		The registered columns can be accessed like attributes on the table
		instance like:
		
		    customers.name
		    customers.debt
		
		@param name: The table name as given in the SQL
		@param colspecs: A list of keyword arguments setting each column name
		    to the relevant L{ColumnType}
		"""
		self._cols = {}
		self._cursor = EchoCursor()
		
		if not isinstance(name,str):
			raise ValueError("Table name must be a string, got %s" % type(name))
		self._name = name
		
		for colname, coltype in colspecs.items():
			coltype._set_table(self)
			coltype._set_colname(colname)
			self._cols[colname] = coltype		
	
	def set_cursor (self, cursor):
		"""
		Install a cursor for use by C{Table} instance. The cursor may be changed
		and used externally at any later point in time.
		
		@param cursor: The cursor to use
		"""
		self._cursor = cursor
	
	def get_cursor(self):
		"""
		Return the cursor currently in use by this table
		
		@return: The cursor currently in use by this table. Note that the
		    default cursor is the L{EchoCursor} used for debugging
		"""
		if isinstance(self._cursor, EchoCursor):
			return None
		
		return self._cursor
	
	def find(self, resultspec, *where):
		"""
		Execute a SELECT statement on the table. The C{resultspec} argument
		signifies the returned columns and may be a free form string, a
		column from the table instance (eg. C{customers.debt}), a C{Table}
		instance, or a list or tuple of any of these. Where ever a C{Table}
		instance is given all columns defined for that table will be returned.
		
		To find full data for all customers who own more than 100 bucks:
		
		    customers.find(customers, customers.debt > 100)
		
		The same, but only those whose name is "Bob":
		
		    customers.find(customers,
		                    customers.debt > 100,
		                    customers.name == "Bob")
		
		Or doing an implicit join on the C{employees} table, to find only the
		name of the customers who has a name similar to an employee:
		
		    customers.find(customers.name,
		                    customers.name == employees.name)
		
		- or the same query returning the full data for both the custormer and
		the employee:
		
		    customers.find((customers, employees),
		                    customers.name == employees.name)
		
		@param resultspec: Signifies the returned columns and may specified
		    in one of four ways. A free form string naming the table columns, a
		    column from the table instance (eg. C{customers.debt}), a C{Table}
		    instance, or a list or tuple of any of these
		@param where: A list of boolean comparisons between table columns and
		    target values
		@return: A result set directly from the installed cursor
		"""
		self._cursor.execute(self.SELECT(resultspec, *where))
		return self._cursor
	
	def find_one(self, resultspec, *where):
		"""
		Like L{find} but return the first element from the result set
		"""
		res = self.find(resultspec, *where)
		return res.fetchone()
	
	def add(self, **rowspec):
		"""
		Execute an INSERT statement on the table and return the row id of the
		inserted row
		
		To insert a new custormer with a zero debt:
		
		    customers.add(name="John Doe", debt=0)
		
		@param rowspec: A list of keyword arguments C{column=value}
		@return: The row id of the inserted row
		"""
		self._cursor.execute(self.INSERT(**rowspec))
		return self._cursor.lastrowid
	
	def update(self, *where, **rowspec):
		"""
		Execute an UPDATE statement on the table.
		
		To update the custormer "Bob"s debt to 200, issue:
		
		    customers.update(customers.name == "Bob", debt=200)
		
		@param where: A where clause as provided to the L{find} method
		@param rowspec: A list of keyword arguments C{column=value}
		@return: A result set directly from the installed cursor
		"""
		return self._cursor.execute(self.UPDATE(*where, **rowspec))
	
	def delete(self, *where):
		"""
		Execute a DELETE statement on the table. To delete all custormers
		named "Bob" issue:
		
		    customers.delete(customers.name == "Bob")
		
		@param where: A where clause as provided to the L{find} method
		@return: The cursor used for executing the statement
		"""
		return self._cursor.execute(self.DELETE(*where))
		
	def SELECT(self, resultspec, *where):
		"""
		Create an SQL statement as defined in L{find} and return it as a string.
		
		This method will not touch the database in any way.
		"""
		stmt = "SELECT %s FROM %s"
		
		# Calc result columns
		result_part = self._expand_result_spec(resultspec)
		
		# Calc where clause
		if where:
			stmt += " " + self.WHERE(*where)
		
		return stmt % (result_part, self)
	
	def INSERT(self, **rowspec):
		"""
		Create an SQL statement as defined in L{add} and return it as a string.
		
		This method will not touch the database in any way.
		"""
		if not rowspec:
			raise ValueError("Expected non-empty col=value sequence, got %s"
																	% rowspec)
		stmt = "INSERT INTO %s (%s) VALUES (%s)"
		cols = None
		vals = None
		
		for name, value in rowspec.iteritems():
			if not name in self._cols:
				raise AttributeError("No such row in table '%s': '%s'" \
																% (self,name))
			coltype = self._cols[name]
			if cols:
				cols += ", " + name
				vals += ", " + coltype.__class__.format(value)
			else:
				cols = name
				vals = coltype.__class__.format(value)
		
		return stmt % (self, cols, vals)
	
	def UPDATE(self, *where, **rowspec):
		"""
		Create an SQL statement as defined in L{update} and return it as a
		string.
		
		This method will not touch the database in any way.
		"""
		if not rowspec:
			raise ValueError("Expected non-empty col=value sequence, got %s"
																	% rowspec)		
		
		stmt = "UPDATE %s SET %s " + self.WHERE(*where)
		values = None
		
		for col, value in rowspec.iteritems():
			if not col in self._cols:
				raise AttributeError("No such row in table '%s': '%s'" \
																% (self,col))
			
			coltype = self._cols[col]
			if values:
				values += ", %s=%s" % (col, coltype.__class__.format(value))
			else:
				values = "%s=%s" % (col, coltype.__class__.format(value))
		
		return stmt % (self, values)
	
	def DELETE(self, *where):
		"""
		Create an SQL DELETE statement and return it as a string.
		
		This method will not touch the database in any way.
		"""
		if not where:
			raise ValueError("No WHERE clause specified for DELETE")
					
		return "DELETE FROM %s %s" % (self, self.WHERE(*where))
	
	def WHERE(self, *where):
		"""
		Create an SQL WHERE clause and return it as a string. Used internally
		by methods such as L{SELECT} and L{UPDATE}.
		
		This method will not touch the database in any way.
		"""
		return "WHERE " + " AND ".join(where)
	
	def __str__ (self):
		return self._name
	
	def get_name(self):
		"""
		Return the SQL table name for this instance
		"""
		return self._name
	
	def columns(self):
		"""
		Return an iterator over the columns defined when creating this table
		"""
		return self._cols.iterkeys()
		
	def __getattr__ (self, name):
		if name in self._cols:
			return self._cols[name]
		else:
			raise AttributeError("No such row '%s'" % name)
	
	def _expand_result_spec (self, resultspec):
		"""
		Takes a result spec as accepted by the L{find} method and converts it
		to valid SQL that can be used in SELECTs like:
		
		    "SELECT %s WHERE foo.bar=27" % table._expand_result_spec(spec)
		"""
		if isinstance(resultspec, (str, unicode)):
			return resultspec
		elif isinstance(resultspec, ColumnType):
			return str(resultspec)
		elif isinstance(resultspec, Table):
			return ", ".join((str(col)
									 for col in resultspec._cols.itervalues()))
		elif isinstance(resultspec, (list,tuple)):
			return ", ".join((self._expand_result_spec(sub) 
									 for sub in resultspec))
		else:
			raise ValueError("Malformed result spec: %s" % resultspec)
		
