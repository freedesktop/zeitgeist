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

from _zeitgeist.engine import get_engine
from zeitgeist.datamodel import *
from _zeitgeist.engine import constants

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("test.benchmarks")

#
# NOTE: Some of the below "random" values are purposely left unset,
# and the order of the items are significant because we select in the
# range (0, randonmess)!
#

CONTENTS = [Interpretation.DOCUMENT, Interpretation.TAG, Interpretation.BOOKMARK, Interpretation.MUSIC,
			Interpretation.EMAIL, Interpretation.IMAGE]
SOURCES = [Manifestation.FILE, Manifestation.WEB_HISTORY, Manifestation.SYSTEM_RESOURCE,
			Manifestation.USER_ACTIVITY]

USES = [Manifestation.USER_ACTIVITY, Manifestation.USER_NOTIFICATION]

APPS = ["foo.desktop", "bar.desktop", "bleh.desktop"]

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
		"use" : USES[randint(0, randomness) % len(USES)],
		"origin" : ORIGINS[randint(0, randomness) % len(ORIGINS)],
		"bookmark" : 0 if randomness == 0 else randint(0,1),
		"tags" : TAGS[randint(0, randomness) % len(TAGS)]
	}

class EngineBenchmark (unittest.TestCase):
	"""
	Base class for benchmarks
	"""
	
	def setUp (self):
		self.tmp_dir = tempfile.mkdtemp() # Create a directory in /tmp/ with a random name
		constants.DATABASE_FILE = "%s/unittest.sqlite" % self.tmp_dir
		constants.DEFAULT_EXTENSIONS = []
		self.engine = get_engine()
	
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
		log.info("*** TEST: Insert with Randomness = 0")
		self.do5ChunksOf200(0)
		
	def test5ChunksOf200Random1(self):
		log.info("*** TEST: Insert with Randomness = 1")
		self.do5ChunksOf200(1)
	
	def test5ChunksOf200Random5(self):
		log.info("*** TEST: Insert with Randomness = 5")
		self.do5ChunksOf200(5)

class FindEvents (EngineBenchmark):
	"""
	This class tests the performance of the find_events method
	"""	
	def prepare_items(self, num, randomness):
		"""
		Helper method to insert 'num' items with a given randomness
		"""
		inserted_items = []
		batch = []
		full_start = time()
		for i in range(1,num+1):
			batch.append(new_dummy_item("test://item%s" % i, randomness=randomness, timestamp=i))
			if len(batch) % 400 == 0:
				self.engine.insert_events(batch)
				inserted_items.extend(batch)
				batch = []
		if batch :
			# Clear any pending batches that didn't fit in the buffer
			self.engine.insert_events(batch)
			inserted_items.extend(batch)
		log.info("Total insertion time for %s items: %ss" % (num, time()-full_start))
		return inserted_items		
	
	def do_find(self, expected_items, page_size, **kwargs):
		"""
		Helper method to find a set of items with page size of 'page_size'
		passin 'kwargs' directly to the engine.find_events() method.
		"""
		total = len(expected_items)
		results = []
		next_timestamp = 0
		page_time = time()
		full_time = page_time	
		page = self.engine.find_events(min=next_timestamp,
										limit=page_size,
										**kwargs)
		log.info("Found %s items in %ss" % (page_size, time()- page_time))
		while page:
			dummy = page[len(page) - 1]["timestamp"]
			if dummy == next_timestamp:
				self.fail("Too many items found")
			if len(results) > total:
				self.fail("More results retrieved than was inserted in " +
							"the first place. Expected %s, found %s" %
							(total, len(results)))
			next_timestamp = dummy + 1
			results += page
			page_time = time()
			page = self.engine.find_events(min=next_timestamp,
											limit=page_size,
											**kwargs)
			log.info("Found %s items in %ss" % (len(page), time()- page_time))
		
		log.info("Full retrieval of %s items in %ss" % (total, time()- full_time))
		
		for i in range(total):
			self.assertEquals(expected_items[i]["uri"],
								results[i]["uri"],
								"Mismatch at position %s:\n%s\n != \n%s" % 
								(i, expected_items[i]["uri"], results[i]["uri"]))
		
		self.assertEquals(len(expected_items), len(results),
				"All inserted items should be found again, %s != %s" %
				(len(expected_items), len(results)))
	
	def testFindAny(self):
		log.info("*** TEST: Find Any In Chunks Of 200")
		items = self.prepare_items(1000, 5)
		self.do_find(items, 200)

	def testFindDocuments(self):
		log.info("*** TEST: Find Documents In Chunks Of 20")
		items = self.prepare_items(1000, 5)
		doc_items = filter(lambda i : i["content"] == Interpretation.DOCUMENT.uri, items)
		self.do_find(doc_items, 20,
					filters=[{"content" : [Interpretation.DOCUMENT.uri]}])

if __name__ == '__main__':
	unittest.main()
