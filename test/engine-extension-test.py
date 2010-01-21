#!/usr/bin/python
# -.- coding: utf-8 -.-

# Update python path to use local zeitgeist module
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import _zeitgeist.engine
from _zeitgeist.engine import constants
from _zeitgeist.engine import get_engine
from _zeitgeist.engine.extension import Extension

import unittest
from testutils import import_events

class _Extension1(Extension):
	PUBLIC_METHODS = ["return_hallo", "return_engine"]
		
	def return_hallo(self):
		return "Hallo"
		
	def return_boo(self):
		return "boo"
		
	def return_engine(self):
		return self.engine


class _engineTestClass(unittest.TestCase):
	
	def setUp (self):
		constants.DATABASE_FILE = ":memory:"
		constants.DEFAULT_EXTENSIONS = []
		self.engine = get_engine()
		
	def tearDown (self):
		self.engine.close()
		_zeitgeist.engine._engine = None


class TestExtensions(_engineTestClass):
	
	def testCreateEngine(self):
		engine = get_engine()
		self.assertEqual(len(engine.extensions), 0)
		self.assertRaises(AttributeError, engine.extensions.__getattr__, "return_hallo")
		engine.extensions.load(_Extension1)
		self.assertEqual(engine.extensions.return_hallo(), "Hallo")
		self.assertRaises(AttributeError, engine.extensions.__getattr__, "return_boo")
		self.assertEqual(engine.extensions.return_engine(), engine)

class TestExtensionHooks(_engineTestClass):
	
	def testInsertHook(self):
		
		class BlockAllInsertExtension(Extension):
			PUBLIC_METHODS = []
				
			def insert_event_hook(self, event, sender):
				return None
				
		self.engine.extensions.load(BlockAllInsertExtension)
		ids = import_events("test/data/five_events.js", self.engine)
		# all inserts where blocked, so each id is 0 to indicate this
		self.assertEquals(filter(None, ids), [])

if __name__ == "__main__":
	unittest.main()
