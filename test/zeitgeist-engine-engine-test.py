#!/usr/bin/python

# Update python path to use local zeitgeist module
import sys, os, tempfile, shutil
from os.path import dirname, join, abspath
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from zeitgeist.engine.base import create_store, set_store
from zeitgeist.engine import base
from zeitgeist.datamodel import *
from zeitgeist.engine.engine import ZeitgeistEngine
from zeitgeist.dbusutils import *

import unittest

# Use this to print sql statements used by Storm to stdout
#from storm.tracer import debug
#debug(True, stream=sys.stdout)

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
		self.tmp_dir = tempfile.mkdtemp()	# Create a directory in /tmp/ with a random name
		storm_url = "sqlite:%s/unittest.sqlite" % self.tmp_dir
		self.store = create_store(storm_url)
		set_store(self.store)
		self.engine = ZeitgeistEngine(self.store)
		
	def tearDown (self):		
		self.store.close()
		shutil.rmtree(self.tmp_dir)
	
	def assertEmptyDB (self):
		# Assert before each test that the db is indeed empty
		self.assertEquals(0, self.store.find(base.URI).count())
		self.assertEquals(0, self.store.find(base.Item).count())
		self.assertEquals(0, self.store.find(base.Annotation).count())
		self.assertEquals(0, self.store.find(base.Event).count())
		
	def testSingleInsertGet(self):
		self.assertEmptyDB()
		orig = {	"uri" : "test://mytest",
					"content" : Content.IMAGE.uri,
					"source" : Source.USER_ACTIVITY.uri,
					"app" : "/usr/share/applications/gnome-about.desktop",
					"timestamp" : 0,
					"text" : "Text",
					"mimetype" : "mime/type",
					"icon" : "stock_left",
					"use" : Content.CREATE_EVENT.uri,
					"origin" : "http://example.org",
					"comment": "",
					"tags": "",
					"bookmark": False, 
					}
		self.engine.insert_item(orig)		
		result = self.engine.get_item("test://mytest")		
		self.assertTrue(result is not None)
		
		# Clean result, from extra data, and add missing data
		result = dictify_data(result)
		result["use"] = Content.CREATE_EVENT.uri
		result["app"] = "/usr/share/applications/gnome-about.desktop"
	
		assert_cmp_dict(orig, result)
		
		content_types = [str(ctype) for ctype in self.engine.get_types()]
		self.assertTrue(Content.IMAGE.uri in content_types)
		self.assertEquals([], list(self.engine.get_all_tags()))
	
	def testBookmark (self):
		self.assertEmptyDB()
		self.assertEquals(0, len(list(self.engine.find_events(0, 0, 0, True,
			False, [(u"", u"", [], [], u"", u"", 1)]))))
		orig = {	"uri" : "test://mytest",
					"content" : Content.IMAGE.uri,
					"source" : Source.USER_ACTIVITY.uri,
					"app" : "/usr/share/applications/gnome-about.desktop",
					"timestamp" : 0,
					"text" : "Text",
					"mimetype" : "mime/type",
					"icon" : "stock_left",
					"use" : Content.CREATE_EVENT.uri,
					"origin" : "http://example.org",
					"bookmark" : True,
					"comment": "",
					"tags": ""
		}
		self.engine.insert_item(orig)
		bookmarks = map(dictify_data, self.engine.find_events(0, 0, 0, True,
			False, [(u"", u"", [], [], u"", u"", 1)]))
		self.assertEquals(1, len(bookmarks))
		self.assertEquals("test://mytest", bookmarks[0]["uri"])
		self.assertEquals([], list(self.engine.get_all_tags()))
	
	def testSameTagOnTwoItems(self):
		self.assertEmptyDB()
		items = (
			{
				"uri" : "test://mytest1",
				"content" : Content.IMAGE.uri,
				"source" : Source.USER_ACTIVITY.uri,
				"app" : "/usr/share/applications/gnome-about.desktop",
				"timestamp" : 0,
				"text" : "Text",
				"mimetype" : "mime/type",
				"icon" : "stock_left",
				"use" : Content.CREATE_EVENT.uri,
				"origin" : "http://example.org",
				"tags" : u"eins",
				"comment": "",
				"bookmark": False
			},
			{
				"uri" : "test://mytest2",
				"content" : Content.IMAGE.uri,
				"source" : Source.USER_ACTIVITY.uri,
				"app" : "/usr/share/applications/gnome-about.desktop",
				"timestamp" : 0,
				"text" : "Text",
				"mimetype" : "mime/type",
				"icon" : "stock_left",
				"use" : Content.CREATE_EVENT.uri,
				"origin" : "http://example.org",
				"tags" : u"eins",
				"comment": "",
				"bookmark": False,
			},
		)
		for item in items:
			self.assertTrue(self.engine.insert_item(item))
		
		tags = list(self.engine.get_all_tags())
		self.assertEquals(["eins"], tags)
		
		i = base.Item.lookup("test://mytest1")
		self.assertTrue(i is not None)
		self.assertEquals(["zeitgeist://tag/eins"],
						  [item.uri.value for item in i.annotations])
		
		i = base.Item.lookup("test://mytest2")
		self.assertTrue(i is not None)
		self.assertEquals(["zeitgeist://tag/eins"],
						  [item.uri.value for item in i.annotations])
				
		eins = base.Annotation.subjects_of("zeitgeist://tag/eins")
		self.assertEquals(["test://mytest1", "test://mytest2"],
						  [item.uri.value for item in eins])
	
	def testThreeTagsOnSameItem(self):		
		self.assertEmptyDB()
		item = {
				"uri" : "test://mytest1",
				"content" : Content.IMAGE.uri,
				"source" : Source.USER_ACTIVITY.uri,
				"app" : "/usr/share/applications/gnome-about.desktop",
				"timestamp" : 0,
				"text" : "Text",
				"mimetype" : "mime/type",
				"icon" : "stock_left",
				"use" : Content.CREATE_EVENT.uri,
				"origin" : "http://example.org",
				"tags" : u"eins,zwei,drei",
				"comment": "",
				"bookmark": False,
		}
		self.assertTrue(self.engine.insert_item(item))
		tags = list(self.engine.get_all_tags())
		self.assertEquals(["eins", "zwei", "drei"], tags)
		
		i = base.Item.lookup("test://mytest1")
		self.assertTrue(i is not None)
		annots = filter(lambda a : a.item.content_id == base.Content.TAG.id,
						i.annotations)
		self.assertEquals(["zeitgeist://tag/eins",
						   "zeitgeist://tag/zwei",
						   "zeitgeist://tag/drei"],
						  [item.uri.value for item in annots])
		
		eins = base.Annotation.lookup("zeitgeist://tag/eins")
		self.assertTrue(eins is not None)
		self.assertEquals(["test://mytest1"],
						  [item.uri.value for item in eins.find_subjects()])
						  
		zwei = base.Annotation.lookup("zeitgeist://tag/zwei")
		self.assertTrue(zwei is not None)
		self.assertEquals(["test://mytest1"],
						  [item.uri.value for item in zwei.find_subjects()])

		drei = base.Annotation.lookup("zeitgeist://tag/drei")
		self.assertTrue(drei is not None)
		self.assertEquals(["test://mytest1"],
						  [item.uri.value for item in drei.find_subjects()])
	
	def testTagAndBookmark(self):
		self.assertEmptyDB()
		item = {
				"uri" : "test://mytest1",
				"content" : Content.IMAGE.uri,
				"source" : Source.USER_ACTIVITY.uri,
				"app" : "/usr/share/applications/gnome-about.desktop",
				"timestamp" : 0,
				"text" : "Text",
				"mimetype" : "mime/type",
				"icon" : "stock_left",
				"use" : Content.CREATE_EVENT.uri,
				"origin" : "http://example.org",
				"tags" : u"boo",
				"bookmark" : True,
				"comment": "",
			}
		self.assertTrue(self.engine.insert_item(item))
		
		item = base.Item.lookup("test://mytest1")
		self.assertTrue(item is not None)
		self.assertEquals(2, item.annotations.count())
		self.assertEquals(["zeitgeist://tag/boo",
						   "zeitgeist://bookmark/test://mytest1"],
						  [item.uri.value for item in item.annotations])
		
		boo = base.Annotation.subjects_of("zeitgeist://tag/boo")
		self.assertTrue(boo is not None)
		self.assertEquals(["test://mytest1"],
						  [item.uri.value for item in boo])

	def testMultipleInsertionAndRetrievals(self):
		self.assertEmptyDB()
		
		# Test insert_items()
		item1 = {
			"uri": u"file:///tmp/test/example.jpg",
			"content": Content.IMAGE.uri,
			"source": Source.USER_ACTIVITY.uri,
			"app": u"/usr/share/applications/eog.desktop",
			"timestamp": 1219324, # keep it lower than in item3!
			"text": u"example.png",
			"mimetype": u"image/jpg",
			"icon": u"",
			"use": Content.CREATE_EVENT.uri,
			"origin": u"",
			"comment": u"",
			"tags": u"",
			"bookmark": False, 
			}
		item2 = {
			"uri": u"http://image.host/cool_pictures/01.png",
			"content": Content.IMAGE.uri,
			"source": Source.USER_ACTIVITY.uri,
			"app": u"/usr/share/applications/firefox.desktop",
			"timestamp": 3563534,
			"text": u"Cool Picture 1",
			"mimetype": u"image/png",
			"icon": u"",
			"use": Content.CREATE_EVENT.uri,
			"origin": u"http://google.com",
			"comment": u"",
			"tags": u"",
			"bookmark": True, 
			}
		item3 = dict(item2) # Create a copy (without dict() we get a reference)
		item3["timestamp"] = 4563534
		last_insertion_app = u"/usr/share/applications/eog.desktop"
		last_insertion_date = 1248324
		item4 = {
			"uri": u"file:///tmp/files/example.png",
			"content": Content.IMAGE.uri,
			"source": Source.USER_ACTIVITY.uri,
			"app": last_insertion_app,
			"timestamp": last_insertion_date,
			"text": u"example.png",
			"mimetype": u"image/png",
			"icon": u"",
			"use": Content.CREATE_EVENT.uri,
			"origin": u"",
			"comment": u"",
			"tags": u"",
			"bookmark": False, 
			}
		items = (item1, item2, item3, item4)
		self.engine.insert_items(items)
		
		# Test get_last_insertion_date()
		result = self.engine.get_last_insertion_date(last_insertion_app)
		self.assertEquals(result, last_insertion_date)
		
		# Test find_events(): bookmarks
		result = self.engine.find_events(0, 0, 0, True, False,
			[(u"", u"", [], [], u"", u"", 1)])
		self.assertEquals(len([x for x in result]), 1)
		
		# Test find_events(): timestamps
		result = self.engine.find_events(1000000, 1250000, 0, True, False, [])
		self.assertEquals(len([x for x in result]), 2)
		
		# Test find_events(): unique
		result = self.engine.find_events(0, 0, 0, True, True, [])
		self.assertEquals(len([x for x in result]), 3)
		
		# Test find_events(): mimetype
		result = self.engine.find_events(0, 0, 0, True, False,
			[(u"", u"", [], [u"image/png"], u"", u"", 0)])
		self.assertEquals(len([x for x in result]), 3)

if __name__ == "__main__":
	unittest.main()
