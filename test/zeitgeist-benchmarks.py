#!/usr/bin/python

# Update python path to use local xesam module
import sys, os
from os.path import dirname, join, abspath
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from zeitgeist.engine.base import create_store, set_store
from zeitgeist.engine import base
from zeitgeist.datamodel import *
from zeitgeist.engine.engine import ZeitgeistEngine
from zeitgeist.dbusutils import *

import unittest

class EngineInsertTest (unittest.TestCase):
	"""
	This class tests the performance of clean inserts in the engine
	"""
	def setUp (self):
		storm_url = "sqlite:/tmp/benchmark.sqlite"
		db_file = storm_url.split(":")[1]
		if os.path.exists(db_file):
			os.remove(db_file)
		self.store = create_store(storm_url)
		set_store(self.store)
		self.engine = ZeitgeistEngine(self.store)
		
		# Assert before each test that the db is indeed empty
		self.assertEquals(0, self.store.find(base.URI).count())
		self.assertEquals(0, self.store.find(base.Item).count())
		self.assertEquals(0, self.store.find(base.Annotation).count())
		self.assertEquals(0, self.store.find(base.Event).count())
		
	def tearDown (self):
		self.store.close()
	
	def newDummyItem(self, uri):
		return {
			"uri" : uri,
			"content" : Content.DOCUMENT.uri,
			"source" : Source.FILE.uri,
			"app" : "/usr/share/applications/gnome-about.desktop",
			"timestamp" : 0,
			"text" : "Text",
			"mimetype" : "mime/type",
			"icon" : "stock_left",
			"use" : Content.CREATE_EVENT.uri,
			"origin" : "http://example.org"
		}
	
	def testInsert1000in200Chunks(self):
		batch = []
		for i in range(1,1001):
			batch.append(self.newDummyItem("test://item%s" % i))
			if len(batch) % 200 == 0:
				self.engine.insert_items(batch)
				batch = []

if __name__ == '__main__':
	unittest.main()
