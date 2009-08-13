#!/usr/bin/python

# Update python path to use local zeitgeist module
import sys
import os
from time import time
import unittest
import logging
import tempfile
import shutil
import random
from random import randint


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Hardcode random seed to make reproducible tests
random.seed(0)

from _zeitgeist.engine import get_default_engine
from zeitgeist.datamodel import *
import _zeitgeist.engine

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("test.benchmarks")

#
# NOTE: Some of the below "random" values are purposely left unset,
# and the order of the items are significant because we select in the
# range (0, randonmess)!
#

CONTENTS = [Content.DOCUMENT, Content.TAG, Content.BOOKMARK, Content.MUSIC,
			Content.EMAIL, Content.IMAGE]
SOURCES = [Source.FILE, Source.WEB_HISTORY, Source.SYSTEM_RESOURCE,
			Source.USER_ACTIVITY]

USES = [Source.USER_ACTIVITY, Source.USER_NOTIFICATION]

APPS = ["foo.desktop", "bar.desktop", "bleh.desktop"]

ICONS = ["stock_sword", "", "stock_dragon", "", "stock_beholder",
			"stock_princess", "", ""]

ORIGINS = ["~/", "http://example.org", "sftp://127.0.0.1/data", "~/Pictures", ""]

MIMES = ["application/pdf", "application/xml", "text/plain",
			"image/png", "image/jpeg"]

TAGS = ["puppies", "", "kittens", "", "ponies", "", "", ""]

def new_dummy_item(uri, randomness=0, timestamp=0):		
	return {
		"uri" : uri,
		"content" : CONTENTS[randint(0, randomness) % len(CONTENTS)],
		"source" : SOURCES[randint(0, randomness) % len(SOURCES)],
		"app" : APPS[randint(0, randomness) % len(APPS)],
		"timestamp" : timestamp,
		"text" : "Text",
		"mimetype" : MIMES[randint(0, randomness) % len(MIMES)],
		"icon" : ICONS[randint(0, randomness) % len(ICONS)],
		"use" : USES[randint(0, randomness) % len(USES)],
		"origin" : ORIGINS[randint(0, randomness) % len(ORIGINS)],
		"bookmark" : 0 if randomness == 0 else randint(0,1),
		"comment" : "This is a sample comment",
		"tags" : TAGS[randint(0, randomness) % len(TAGS)]
	}

class EngineBenchmark (unittest.TestCase):
	"""
	Base class for benchmarks
	"""
	
	def setUp (self):
		self.tmp_dir = tempfile.mkdtemp()	# Create a directory in /tmp/ with a random name
		_zeitgeist.engine.DB_PATH = "%s/unittest.sqlite" % self.tmp_dir
		self.engine = get_default_engine()
		
	def tearDown (self):		
		self.engine.close()
		shutil.rmtree(self.tmp_dir)

class Insert (EngineBenchmark):
	"""
	This class tests the performance of clean inserts in the engine
	"""			
	
	def do5ChunksOf200(self, randomness):
		batch = []
		full_start = time()
		for i in range(1,1001):
			batch.append(new_dummy_item("test://item%s" % i, randomness=randomness, timestamp=i))
			if len(batch) % 200 == 0:
				start = time()
				self.engine.insert_events(batch)
				log.info("Inserted 200 items in: %ss" % (time()-start))
				batch = []
		log.info("Total insertion time for 1000 items: %ss" % (time()-full_start))
	
	def test5ChunksOf200Random0(self):
		log.info("RANDOMNESS = 0")
		self.do5ChunksOf200(0)
		
	def test5ChunksOf200Random1(self):
		log.info("RANDOMNESS = 1")
		self.do5ChunksOf200(1)
	
	def test5ChunksOf200Random5(self):
		log.info("RANDOMNESS = 5")
		self.do5ChunksOf200(5)

class FindEvents (EngineBenchmark):
	"""
	This class tests the performance of the find_events method
	"""	
	pass

	

if __name__ == '__main__':
	unittest.main()

