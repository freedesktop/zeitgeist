#! /usr/bin/python
# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2010 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
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
#

import sys, os, shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
WhereClause = None

from _zeitgeist.engine import constants, sql

class SQLTest (unittest.TestCase):
	
	def setUp(self):
		global WhereClause
		if WhereClause is None:
			from _zeitgeist.engine.sql import WhereClause as _WhereClause
			WhereClause = _WhereClause
	
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
			"(actor IN (SELECT id FROM actor WHERE (value >= bar AND value < bas)))")
			
		where = WhereClause(WhereClause.AND)
		where.add_text_condition("subj_mimetype", "bar", like=True)
		self.assertEquals(where.sql.replace("?", "%s") % tuple(where.arguments),
			"(subj_mimetype IN (SELECT id FROM mimetype WHERE (value >= bar AND value < bas)))")
			
		where = WhereClause(WhereClause.AND)
		where.add_text_condition("subj_uri", "bar", like=True)
		self.assertEquals(where.sql.replace("?", "%s") % tuple(where.arguments),
			"(subj_id IN (SELECT id FROM uri WHERE (value >= bar AND value < bas)))")
			
		where = WhereClause(WhereClause.AND)
		where.add_text_condition("subj_origin", "bar", like=True)
		self.assertEquals(where.sql.replace("?", "%s") % tuple(where.arguments),
			"(subj_origin IN (SELECT id FROM uri WHERE (value >= bar AND value < bas)))")
			
		where = WhereClause(WhereClause.AND)
		where.add_text_condition("actor", "bar", like=True, negation=True)
		self.assertEquals(where.sql.replace("?", "%s") % tuple(where.arguments),
			"(actor NOT IN (SELECT id FROM actor " \
			"WHERE (value >= bar AND value < bas)) OR actor IS NULL)")

	def testEarlyUpgradeCorruption(self):
		# Set up the testing environment:
		DATABASE_TEST_FILE = os.environ.get("ZEITGEIST_DATABASE_PATH",
			os.path.join(constants.DATA_PATH, "activity.test.sqlite"))
		DATABASE_TEST_FILE_BACKUP = os.environ.get("ZEITGEIST_DATABASE_PATH",
			os.path.join(constants.DATA_PATH, "activity.test.sqlite.bck"))
		if os.path.exists(constants.DATABASE_FILE): 
			shutil.move(constants.DATABASE_FILE, DATABASE_TEST_FILE)
		if os.path.exists(constants.DATABASE_FILE_BACKUP):
			shutil.move(constants.DATABASE_FILE_BACKUP, DATABASE_TEST_FILE_BACKUP)

		# Ensure we are at version 0:
		cursor = sql._connect_to_db(constants.DATABASE_FILE)
		self.assertEqual(0, sql._get_schema_version(cursor, constants.CORE_SCHEMA))

		# If upgrade core_0_1 fails, we have no backup to restore from:
		self.assertRaises(IOError,
				  sql._do_schema_restore)

		# Solution: let the database structure run through create_db:
		cursor = sql.create_db(constants.DATABASE_FILE)
		self.assertEqual(constants.CORE_SCHEMA_VERSION,
				 sql._get_schema_version(cursor, constants.CORE_SCHEMA))

		# Clean-up after ourselves:
		if os.path.exists(DATABASE_TEST_FILE):
			shutil.move(DATABASE_TEST_FILE, constants.DATABASE_FILE)
		if os.path.exists(DATABASE_TEST_FILE_BACKUP):
			shutil.move(DATABASE_TEST_FILE_BACKUP, constants.DATABASE_FILE_BACKUP)

	def testUpgradeCorruption(self):
		# Set up the testing environment:
		DATABASE_TEST_FILE = os.environ.get("ZEITGEIST_DATABASE_PATH",
			os.path.join(constants.DATA_PATH, "activity.test.sqlite"))
		DATABASE_TEST_FILE_BACKUP = os.environ.get("ZEITGEIST_DATABASE_PATH",
			os.path.join(constants.DATA_PATH, "activity.test.sqlite.bck"))
		if os.path.exists(constants.DATABASE_FILE): 
			shutil.move(constants.DATABASE_FILE, DATABASE_TEST_FILE)
		if os.path.exists(constants.DATABASE_FILE_BACKUP):
			shutil.move(constants.DATABASE_FILE_BACKUP, DATABASE_TEST_FILE_BACKUP)

		# Ensure we are at version 0:
		cursor = sql._connect_to_db(constants.DATABASE_FILE)
		self.assertEqual(0, sql._get_schema_version(cursor, constants.CORE_SCHEMA))

		# Run through a successful upgrade (core_0_1):
		sql._do_schema_upgrade(cursor, constants.CORE_SCHEMA, 0, 1)
		self.assertEquals(1, sql._get_schema_version(cursor, constants.CORE_SCHEMA))
		sql._set_schema_version(cursor, constants.CORE_SCHEMA, 1)
		sql._do_schema_backup()
		self.assertTrue(os.path.exists(constants.DATABASE_FILE_BACKUP))

		# Simulate a failed upgrade:
		sql._set_schema_version(cursor, constants.CORE_SCHEMA, -1)

		# ... and then try to fix it:
		do_upgrade, cursor = sql._check_core_schema_upgrade(cursor)

		# ... and fail again, as a table is missing inbetween core_2_3 and core_3_4:
		self.assertFalse(do_upgrade)
		self.assertEqual(-1, sql._get_schema_version(cursor, constants.CORE_SCHEMA))

		# ... we then let the database structure run through create_db:
		cursor = sql.create_db(constants.DATABASE_FILE)

		# ... it is now well-structured:
		self.assertEquals(constants.CORE_SCHEMA_VERSION,
			sql._get_schema_version(cursor, constants.CORE_SCHEMA))

		# Clean-up after ourselves:
		if os.path.exists(DATABASE_TEST_FILE):
			shutil.move(DATABASE_TEST_FILE, constants.DATABASE_FILE)
		if os.path.exists(DATABASE_TEST_FILE_BACKUP):
			shutil.move(DATABASE_TEST_FILE_BACKUP, constants.DATABASE_FILE_BACKUP)

if __name__ == "__main__":
	unittest.main()
