#!/usr/bin/python

# Update python path to use local xesam module
import sys, os
from os.path import dirname, join, abspath
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from zeitgeist.engine.base import create_store, set_store
from zeitgeist.datamodel import *
from zeitgeist.engine.engine import ZeitgeistEngine
from zeitgeist.dbusutils import *

import unittest

def assert_cmp_dict(a, b, cross_check=True):	
	for k,v in a.items():
		if not b.has_key(k) : raise AssertionError("Dict b does not contain '%s'" % k)
		if not v == b[k] : raise AssertionError("Dict values differ: a[%s]=%s and b[%s]=%s" % (k, v, k, b[k]))
	if cross_check:
		assert_cmp_dict(b,a, cross_check=False)

class ZeitgeistEngineTest (unittest.TestCase):
	"""
	This class tests that the zeitgeist.engine.engine.ZeitgeistEngine class
	"""
	def setUp (self):
		storm_url = "sqlite:/tmp/unittest.sqlite"
		db_file = storm_url.split(":")[1]
		if os.path.exists(db_file):
			os.remove(db_file)
		self.store = create_store(storm_url)
		set_store(self.store)
		self.engine = ZeitgeistEngine(self.store)
		
	def tearDown (self):
		self.store.close()
	
	def testSingleInsertGet(self):
		orig = {	"uri" : "test://mytest",
					"content" : Content.IMAGE.uri,
					"source" : Source.USER_ACTIVITY.uri,
					"app" : "/usr/share/applications/gnome-about.desktop",
					"timestamp" : 0,
					"text" : "Text",
					"mimetype" : "mime/type",
					"icon" : "stock_left",
					"use" : Content.CREATE_EVENT.uri,
					"origin" : "http://example.org" }
		self.engine.insert_item(orig)		
		result = self.engine.get_item("test://mytest")		
		self.assertTrue(result is not None)
		
		# Clean result, from extra data, and add missing data
		result = dictify_data(result)
		result["use"] = Content.CREATE_EVENT.uri
		result["app"] = "/usr/share/applications/gnome-about.desktop"
		result.pop("tags")
		result.pop("bookmark")
	
		assert_cmp_dict(orig, result)
		
		content_types = [str(ctype) for ctype in self.engine.get_types()]
		self.assertTrue(Content.IMAGE.uri in content_types)
	
if __name__ == '__main__':
	unittest.main()
