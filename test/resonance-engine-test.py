#!/usr/bin/python

# Update python path to use local zeitgeist module
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import _zeitgeist.engine
from _zeitgeist.engine import get_default_engine
from zeitgeist.datamodel import *
from zeitgeist.dbusutils import Event, Item, Annotation

import unittest
import tempfile
import shutil


class ZeitgeistEngineTest (unittest.TestCase):
	"""
	This class tests that the zeitgeist.engine.engine.ZeitgeistEngine class
	"""
	def setUp (self):
		self.tmp_dir = tempfile.mkdtemp()	# Create a directory in /tmp/ with a random name
		_zeitgeist.engine.DB_PATH = "%s/unittest.sqlite" % self.tmp_dir
		self.engine = get_default_engine()
		
	def tearDown (self):		
		self.engine.close()
		shutil.rmtree(self.tmp_dir)
	
	def assertEmptyDB (self):
		# Assert before each test that the db is indeed empty
		self.assertEquals((), self.engine.find_events(0, limit=1))		
		
	def testSingleInsertGet(self):
		self.assertEmptyDB()
		uri = u"test://mytest"
		orig_event = {
			"subject": uri,
			"timestamp": 0,
			"source": Source.USER_ACTIVITY,
			"content": Content.CREATE_EVENT,
			"application": "/usr/share/applications/gnome-about.desktop",
			"tags": {},
			"bookmark": False,
		}
		orig_item = {
			"content": Content.IMAGE,
			"source": Source.FILE,
			"mimetype": "mime/type",
			"bookmark": True,
		}
		
		# Insert item and event
		num_inserts = self.engine.insert_event(orig_event, orig_item, [])
		self.assertEquals(1, num_inserts)
		
		# Check the item (get_items)
		result = self.engine.get_items([uri])
		self.assertTrue(result is not None)
		self.assertTrue(uri in result)
		result_item = dict(result[uri])
		result_item["tags"] = {}
		assert_cmp_dict(orig_item, result_item)
		
		# Check the event (find_events)
		result = self.engine.find_events(0, 0, 0, True, "event",
			[{"uri": uri}])
		self.assertTrue(result is not None)
		self.assertEquals(len(result[0]), 1)
		self.assertEquals(len(result[1]), 1)
		result_event = dict(result[0][0])
		result_event["uri"] = "" # we don't know what it'll be
		del orig_event["tags"]
		assert_cmp_dict(orig_event, result_event)
		
		content_types = [str(ctype) for ctype in self.engine.get_types()]
		self.assertTrue(str(Content.IMAGE) in content_types)
	
	

if __name__ == "__main__":
	unittest.main()
