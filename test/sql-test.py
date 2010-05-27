#! /usr/bin/python
# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2010 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
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
#

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
from _zeitgeist.engine.sql import *

class SQLTest (unittest.TestCase):
	
	def testFlat (self):
		where = WhereClause(WhereClause.AND)
		where.add ("foo = %s", 10)
		where.add ("bar = %s", 27)
		self.assertEquals(where.sql % tuple(where.arguments),
		                  "(foo = 10 AND bar = 27)")
	
	def testNested (self):
		where = WhereClause(WhereClause.AND)
		where.add ("foo = %s", 10)
		
		subwhere = WhereClause(WhereClause.OR)
		subwhere.add ("subfoo = %s", 68)
		subwhere.add ("subbar = %s", 69)
		where.extend(subwhere)
		where.add ("bar = %s", 11)
		
		self.assertEquals(where.sql % tuple(where.arguments),
		                  "(foo = 10 AND (subfoo = 68 OR subbar = 69) AND bar = 11)")
		                  
	def testFlatNegation(self):
		where = WhereClause(WhereClause.OR, negation=True)
		where.add("foo = %s", 7)
		where.add("bar = %s", 77)
		self.assertEquals(where.sql %tuple(where.arguments),
			"NOT (foo = 7 OR bar = 77)")
			
	def testNestedNegation(self):
		where = WhereClause(WhereClause.AND)
		where.add ("foo = %s", 10)
		
		subwhere = WhereClause(WhereClause.OR, negation=True)
		subwhere.add ("subfoo = %s", 68)
		subwhere.add ("subbar = %s", 69)
		where.extend(subwhere)
		where.add ("bar = %s", 11)
		
		self.assertEquals(where.sql % tuple(where.arguments),
		                  "(foo = 10 AND NOT (subfoo = 68 OR subbar = 69) AND bar = 11)")
		                  
	def testAddTextCondition(self):
		where = WhereClause(WhereClause.AND)
		where.add_text_condition("boo", "bar")
		self.assertEquals(where.sql.replace("?", "%s") % tuple(where.arguments),
			"(boo = bar)")
			
		where = WhereClause(WhereClause.AND)
		where.add_text_condition("boo", "bar", negation=True)
		self.assertEquals(where.sql.replace("?", "%s") % tuple(where.arguments),
			"(boo != bar)")
			
		where = WhereClause(WhereClause.AND)
		where.add_text_condition("actor", "bar", like=True)
		self.assertEquals(where.sql.replace("?", "%s") % tuple(where.arguments),
			"(actor IN (SELECT id FROM actor WHERE value GLOB bar*))")
			
		where = WhereClause(WhereClause.AND)
		where.add_text_condition("subj_mimetype", "bar", like=True)
		self.assertEquals(where.sql.replace("?", "%s") % tuple(where.arguments),
			"(subj_mimetype IN (SELECT id FROM mimetype WHERE value GLOB bar*))")
			
		where = WhereClause(WhereClause.AND)
		where.add_text_condition("subj_uri", "bar", like=True)
		self.assertEquals(where.sql.replace("?", "%s") % tuple(where.arguments),
			"(subj_uri IN (SELECT value FROM uri WHERE value GLOB bar*))")
			
		where = WhereClause(WhereClause.AND)
		where.add_text_condition("subj_origin", "bar", like=True)
		self.assertEquals(where.sql.replace("?", "%s") % tuple(where.arguments),
			"(subj_origin IN (SELECT value FROM uri WHERE value GLOB bar*))")
			
		where = WhereClause(WhereClause.AND)
		where.add_text_condition("actor", "bar", like=True, negation=True)
		self.assertEquals(where.sql.replace("?", "%s") % tuple(where.arguments),
			"(actor NOT IN (SELECT id FROM actor WHERE value GLOB bar*))")
		

if __name__ == "__main__":
	unittest.main()
