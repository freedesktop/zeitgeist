#!/usr/bin/python

# Update python path to use local zeitgeist module
import sys
import os
from time import time
import unittest
import logging
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from _zeitgeist.engine import get_default_engine
from zeitgeist.datamodel import *
import _zeitgeist.engine

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("test.benchmarks")

class EngineInsertTest (unittest.TestCase):
	"""
	This class tests the performance of clean inserts in the engine
	"""
	def setUp (self):
		self.tmp_dir = tempfile.mkdtemp()	# Create a directory in /tmp/ with a random name
		_zeitgeist.engine.DB_PATH = "%s/unittest.sqlite" % self.tmp_dir
		self.engine = get_default_engine()
		
	def tearDown (self):		
		self.engine.close()
		shutil.rmtree(self.tmp_dir)
	
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
			"origin" : "http://example.org",
			"bookmark" : False,
			"comment" : "This is a sample comment",
			"tags" : u""
		}
	
	def testInsert1000in200Chunks(self):
		batch = []
		full_start = time()
		for i in range(1,1001):
			batch.append(self.newDummyItem("test://item%s" % i))
			if len(batch) % 200 == 0:
				start = time()
				self.engine.insert_events(batch)
				log.info("Inserted 200 items in: %ss" % (time()-start))
				batch = []
		log.info("Total insertion time for 1000 items: %ss" % (time()-full_start))
	

if __name__ == '__main__':
	unittest.main()
