#!/usr/bin/python
# -.- coding: utf-8 -.-

# Update python path to use local zeitgeist module
import sys
import os
import weakref
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
		self.save_default_ext = os.environ.get("ZEITGEIST_DEFAULT_EXTENSIONS")
		self.save_extra_ext = os.environ.get("ZEITGEIST_EXTRA_EXTENSIONS")
		os.environ["ZEITGEIST_DEFAULT_EXTENSIONS"] = ""
		os.environ["ZEITGEIST_EXTRA_EXTENSIONS"] = ""
		self.engine = get_engine()
		
	def tearDown (self):
		if self.save_default_ext is not None:
			os.environ["ZEITGEIST_DEFAULT_EXTENSIONS"] = self.save_default_ext
		else:
			del os.environ["ZEITGEIST_DEFAULT_EXTENSIONS"]
		if self.save_extra_ext is not None:
			os.environ["ZEITGEIST_EXTRA_EXTENSIONS"] = self.save_extra_ext
		else:
			del os.environ["ZEITGEIST_EXTRA_EXTENSIONS"]
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
		self.assertEqual(engine.extensions.return_engine(), weakref.proxy(engine))

class TestExtensionHooks(_engineTestClass):
	
	def testInsertHook(self):
		
		class BlockAllInsertExtension(Extension):
			PUBLIC_METHODS = []
				
			def pre_insert_event(self, event, sender):
				return None
				
		self.engine.extensions.load(BlockAllInsertExtension)
		ids = import_events("test/data/five_events.js", self.engine)
		# all inserts where blocked, so each id is 0 to indicate this
		self.assertEquals(filter(None, ids), [])
	
	def testDeleteHook(self):
		
		class DeleteAllInsertExtension(Extension):
			PUBLIC_METHODS = []
			del_ids = []
			
			@classmethod
			def post_delete_events(self, del_ids, sender):
				self.del_ids = del_ids
				
		self.engine.extensions.load(DeleteAllInsertExtension)
		ids = import_events("test/data/five_events.js", self.engine)
		# all inserts where blocked, so each id is 0 to indicate this
		self.engine.delete_events([ids[1]])
		self.assertEquals(DeleteAllInsertExtension.del_ids, [ids[1]])

if __name__ == "__main__":
	unittest.main()
