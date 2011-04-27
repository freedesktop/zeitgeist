#!/usr/bin/python
# -.- coding: utf-8 -.-

# Update python path to use local zeitgeist module
import sys
import os
import weakref
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
from testutils import import_events

Extension = None

class _engineTestClass(unittest.TestCase):
	
	def setUp (self):
		global Extension
		
		from _zeitgeist.engine import constants
		from _zeitgeist.engine import get_engine
		
		if Extension is None:
			from _zeitgeist.engine.extension import Extension as _Extension
			Extension = _Extension
		
		constants.DATABASE_FILE = ":memory:"
		self.save_default_ext = os.environ.get("ZEITGEIST_DEFAULT_EXTENSIONS")
		self.save_extra_ext = os.environ.get("ZEITGEIST_EXTRA_EXTENSIONS")
		os.environ["ZEITGEIST_DEFAULT_EXTENSIONS"] = ""
		os.environ["ZEITGEIST_EXTRA_EXTENSIONS"] = ""
		self.engine = get_engine()
		
	def tearDown (self):
		import _zeitgeist.engine
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

		class _Extension1(Extension):
			PUBLIC_METHODS = ["return_hallo", "return_engine"]
				
			def return_hallo(self):
				return "Hallo"
				
			def return_boo(self):
				return "boo"
				
			def return_engine(self):
				return self.engine
		
		engine = self.engine
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
			insert_count = 0
			do_insert = True
			
			@classmethod
			def pre_insert_event(cls, event, sender):
				if cls.do_insert:
					cls.do_insert = False
					return event
				return None
				
			@classmethod
			def post_insert_event(cls, event, sender):
				cls.insert_count += 1
				
		self.engine.extensions.load(BlockAllInsertExtension)
		ids = import_events("test/data/five_events.js", self.engine)
		
		# all but the first one events are blocked
		self.assertEquals(filter(None, ids), [1])
		self.assertEquals(BlockAllInsertExtension.insert_count, 1)
	
	def testDeleteHook(self):
		
		class DeleteAllInsertExtension(Extension):
			PUBLIC_METHODS = []
			del_ids = []
			
			@classmethod
			def pre_delete_events(cls, ids, sender):
				return ids[:1]
			
			@classmethod
			def post_delete_events(cls, del_ids, sender):
				cls.del_ids = del_ids
				
		self.engine.extensions.load(DeleteAllInsertExtension)
		ids = import_events("test/data/five_events.js", self.engine)
		
		# we try to delete the first two events, but the engine will
		# block the deletion of the seconds one
		self.engine.delete_events(ids[:2])
		self.assertEquals(DeleteAllInsertExtension.del_ids, ids[:1])
		
	def testGetHook(self):
		
		class BlockGetExtension(Extension):
			PUBLIC_METHODS = []
			
			@classmethod
			def get_event(self, event, sender):
				if event is not None and int(event.timestamp) > 130:
					return None
				return event
				
		self.engine.extensions.load(BlockGetExtension)
		ids = import_events("test/data/five_events.js", self.engine)
		
		# request all events, but only the first event object
		# will be returned, the other events are blocked by the extension
		# and presented as `None`
		events = self.engine.get_events(ids)
		self.assertEqual(len(filter(lambda x: x is not None, events)), 1)
		
		
class TestExtensionsCollection(_engineTestClass):
		
	def testIterNames(self):
		SampleExtension1 = type("SampleExtension1", (Extension,), dict(Extension.__dict__))
		SampleExtension2 = type("SampleExtension2", (Extension,), dict(Extension.__dict__))
		
		self.engine.extensions.load(SampleExtension1)
		self.assertEquals(list(self.engine.extensions.iter_names()), ["SampleExtension1"])
		
		self.engine.extensions.load(SampleExtension2)
		self.assertEquals(
			sorted(self.engine.extensions.iter_names()),
			["SampleExtension1", "SampleExtension2"]
		)
		

if __name__ == "__main__":
	unittest.main()
