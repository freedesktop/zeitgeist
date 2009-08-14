#!/usr/bin/python

# Update python path to use local zeitgeist module
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import _zeitgeist.engine
from _zeitgeist.engine import get_default_engine
from zeitgeist.datamodel import *

import unittest
import tempfile
import shutil

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
		_zeitgeist.engine.DB_PATH = "%s/unittest.sqlite" % self.tmp_dir
		self.engine = get_default_engine()
		
	def tearDown (self):		
		self.engine.close()
		shutil.rmtree(self.tmp_dir)
	
	def assertEmptyDB (self):
		# Assert before each test that the db is indeed empty
		self.assertEquals([], self.engine.find_events(0, limit=1))		
		
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
					"tags": u"example, test, tagtest",
					"bookmark": False, 
					}
		num_inserts = self.engine.insert_event(orig)
		self.assertEquals(1, num_inserts)
		result = self.engine.get_item("test://mytest")
		self.assertTrue(result is not None)
		
		# Clean result, from extra data, and add missing data,
		# we clone the result because we can not assume it is writable
		result = dict(result)
		result["use"] = Content.CREATE_EVENT.uri
		result["app"] = "/usr/share/applications/gnome-about.desktop"
		
		assert_cmp_dict(orig, result)
		
		content_types = [str(ctype) for ctype in self.engine.get_types()]
		self.assertTrue(Content.IMAGE.uri in content_types)
		self.assertEquals([(u"example", 1), (u"test", 1), (u"tagtest", 1)],
			list(self.engine.get_tags()))
	
	def testBookmark (self):
		self.assertEmptyDB()
		self.assertEquals(0, len(list(self.engine.find_events(0, 0, 0, True,
			"event", [{"bookmarked": True}]))))
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
		self.engine.insert_event(orig)
		bookmarks = self.engine.find_events(0, 0, 0, True,
						"event", [{"bookmarked": True}])
		self.assertEquals(1, len(bookmarks))
		self.assertEquals("test://mytest", bookmarks[0]["uri"])
		self.assertEquals([], list(self.engine.get_tags()))
	
	def testSameTagOnTwoItems(self):
		self.assertEmptyDB()
		items = (
			{
				"uri" : "test://mytest1",
				"content" : Content.IMAGE.uri,
				"source" : Source.USER_ACTIVITY.uri,
				"app" : "/usr/share/applications/gnome-about.desktop",
				"timestamp" : 100,
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
				"timestamp" : 1000,
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
			self.assertTrue(self.engine.insert_event(item))
		
		tags = list(self.engine.get_tags())
		self.assertEquals([("eins", 2)], tags)
		
		i = self.engine.get_item("test://mytest1")
		self.assertTrue(i is not None)
		self.assertEquals("eins", i["tags"])
		
		i = self.engine.get_item("test://mytest2")
		self.assertTrue(i is not None)
		self.assertEquals("eins", i["tags"])
				
		eins = self.engine.find_events(filters=[{"tags" : ["eins"]}])
		self.assertEquals(2, len(eins))
		self.assertEquals("test://mytest1", eins[0]["uri"])
		self.assertEquals("test://mytest2", eins[1]["uri"])
	
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
		self.assertTrue(self.engine.insert_event(item))
		tags = self.engine.get_tags()
		self.assertEquals([(u"eins", 1), (u"zwei", 1), (u"drei", 1)], tags)
		
		i = self.engine.get_item("test://mytest1")
		self.assertTrue(i is not None)
		self.assertEquals("eins, zwei, drei",
						  i["tags"])		
		
		self.assertEquals([("eins", 1), ("zwei", 1), ("drei", 1)],
						  self.engine.get_tags())				
				
	
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
		self.assertTrue(self.engine.insert_event(item))
		
		item = self.engine.get_item("test://mytest1")
		self.assertTrue(item is not None)
		self.assertEquals("boo", item["tags"])
		self.assertTrue(item["bookmark"])
		
		
		boo = self.engine.find_events(filters=[{"tags" : ["boo"]}])
		self.assertEquals(1, len(boo))
		self.assertEquals("test://mytest1",
						  boo[0]["uri"])

	def _init_with_various_events(self):
		self.assertEmptyDB()
		
		item1 = {
			"uri": u"file:///tmp/test/example.jpg",
			"content": Content.IMAGE.uri,
			"source": Source.USER_ACTIVITY.uri,
			"app": u"/usr/share/applications/eog.desktop",
			"timestamp": 1219324, # keep it lower than in item4!
			"text": u"example.jpg",
			"mimetype": u"image/jpg",
			"icon": u"",
			"use": Content.CREATE_EVENT.uri,
			"origin": u"",
			"comment": u"",
			"tags": u"test, examples, filtertest",
			"bookmark": False,
			}
		item2 = {
			"uri": u"http://image.host/cool_pictures/01.png",
			"content": Content.IMAGE.uri,
			"source": Source.WEB_HISTORY.uri,
			"app": u"/usr/share/applications/firefox.desktop",
			"timestamp": 3563534,
			"text": u"Cool Picture 1",
			"mimetype": u"image/png",
			"icon": u"",
			"use": Content.CREATE_EVENT.uri,
			"origin": u"http://google.com",
			"comment": u"",
			"tags": u"cool_pictures, examples",
			"bookmark": True,
			}
		item3 = dict(item2) # Create a copy (without dict() we get a reference)
		item3["timestamp"] = 4563534
		self.last_insertion_app = u"/usr/share/applications/eog.desktop"
		self.last_insertion_date = 1248324
		item4 = {
			"uri": u"file:///tmp/files/example.png",
			"content": Content.IMAGE.uri,
			"source": Source.USER_ACTIVITY.uri,
			"app": self.last_insertion_app,
			"timestamp": self.last_insertion_date,
			"text": u"example.png",
			"mimetype": u"image/png",
			"icon": u"",
			"use": Content.CREATE_EVENT.uri,
			"origin": u"",
			"comment": u"",
			"tags": u"files, examples",
			"bookmark": False,
			}
		item5 = {
			"uri": u"file:///home/foo/images/holidays/picture.png",
			"content": Content.VIDEO.uri,
			"source": Source.USER_ACTIVITY.uri,
			"app": u"/usr/share/applications/eog.desktop",
			"timestamp": 1219335,
			"text": u"picture.png",
			"mimetype": u"image/png",
			"icon": u"",
			"use": Content.CREATE_EVENT.uri,
			"origin": u"",
			"comment": u"",
			"tags": u"images, holidays",
			"bookmark": True,
			}
		items = (item1, item2, item3, item4, item5)
		self.engine.insert_events(items)
	
	def testGetLastInsertionDate(self):
		self._init_with_various_events()
		result = self.engine.get_last_insertion_date(self.last_insertion_app)
		self.assertEquals(result, self.last_insertion_date)
	
	def testFindEventsBookmarks(self):
		self._init_with_various_events()
		result = self.engine.find_events(0, 0, 0, True, "event",
			[{"bookmarked": True}])
		self.assertEquals(len([x for x in result]), 3)
	
	def testFindEventsTimestamp(self):
		self._init_with_various_events()
		result = self.engine.find_events(1000000, 1250000, 0, True, "event", [])
		self.assertEquals(len([x for x in result]), 3)
	
	def testFindEventsUnique(self):
		self._init_with_various_events()
		result = self.engine.find_events(0, 0, 0, True, "item", [])
		self.assertEquals(len([x for x in result]), 4)
	
	def testFindEventsMostUsed(self):
		self._init_with_various_events()
		result = self.engine.find_events(0, 0, 0, False, "mostused", [])
		self.assertEquals(result[0]["text"], u"Cool Picture 1")
	
	def testFindEventsUriAsString(self): # Deprecated (to be removed in 0.3)
		self._init_with_various_events()
		result = self.engine.find_events(0, 0, 0, False, "item",
			[{"uri": u"file:///tmp/test/%"}])
		self.assertEquals(len(result), 1)
	
	def testFindEventsUri(self):
		self._init_with_various_events()
		result = self.engine.find_events(0, 0, 0, False, "item",
			[{"uri": [u"file:///tmp/test/%", u"%/example.png"]}])
		self.assertEquals(len(result), 2)
	
	def testFindEventsNameAsString(self): # Deprecated (to be removed in 0.3)
		self._init_with_various_events()
		result = self.engine.find_events(0, 0, 0, False, "item",
			[{"name": u"%.png"}])
		self.assertEquals(len(result), 2)
	
	def testFindEventsName(self):
		self._init_with_various_events()
		result = self.engine.find_events(0, 0, 0, False, "item",
			[{"name": [u"e%.png", u"cool picture 1"]}])
		self.assertEquals(len(result), 2)
	
	def testFindEventsMimetype(self):
		self._init_with_various_events()
		result = self.engine.find_events(0, 0, 0, True, "event",
			[{"mimetypes": [u"image/png"]}])
		self.assertEquals(len([x for x in result]), 4)
	
	def testFindEventsMimetypeWithWildcard(self):
		self._init_with_various_events()
		result = self.engine.find_events(0, 0, 0, True, "event",
			[{"mimetypes": [u"image/j%", u"image/_n_"]}])
		self.assertEquals(set([x["mimetype"] for x in result]),
			set([u"image/jpg", u"image/png"]))
	
	def testFindEventsMimetypeAndBookmarks(self):
		self._init_with_various_events()
		result = self.engine.find_events(0, 0, 0, True, "event",
			[{"mimetypes": [u"image/jpg"], "bookmarked": True}])
		self.assertEquals(len([x for x in result]), 0)
	
	def testFindEventsUniqueAndNotBookmarked(self):
		self._init_with_various_events()
		result = self.engine.find_events(0, 0, 0, True, "item",
			[{"bookmarked": False}])
		self.assertEquals(len([x for x in result]), 2)
	
	def testFindEventsWithTags(self):
		self._init_with_various_events()
		result1 = [x["uri"] for x in self.engine.find_events(0, 0, 0, True, "event",
			[{"tags": [u"files"]}])]
		result2 = [x["uri"] for x in self.engine.find_events(0, 0, 0, True, "event",
			[{"tags": [u"files", u"examples"]}])]
		self.assertEquals(result1, result2)
		self.assertEquals(result1, [u"file:///tmp/files/example.png"])
	
	def testFindEventsWithContent(self):
		self._init_with_various_events()
		result1 = self.engine.find_events(0, 0, 0, True, "event",
			[{"content": [Content.IMAGE.uri]}])
		result2 = self.engine.find_events(0, 0, 0, True, "event",
			[{"content": [Content.IMAGE.uri, Content.MUSIC.uri]}])
		result3 = self.engine.find_events(0, 0, 0, True, "event",
			[{"content": [Content.VIDEO.uri]}])
		result4 = self.engine.find_events(0, 0, 0, True, "event",
			[{"content": [Content.MUSIC.uri]}])
		self.assertEquals(result1, result2)
		self.assertEquals([x["content"] for x in result1], [Content.IMAGE.uri] * 4)
		self.assertEquals(result3[0]["text"],  u"picture.png")
		self.assertEquals(len(result3), 1)
		self.assertEquals(len(result4), 0)
	
	def testFindEventsWithSource(self):
		self._init_with_various_events()
		result1 = self.engine.find_events(0, 0, 0, True, "event",
			[{"source": [Source.USER_ACTIVITY.uri, Source.FILE.uri]}])
		result2 = self.engine.find_events(0, 0, 0, True, "event",
			[{"source": [Source.WEB_HISTORY.uri]}])
		result3 = self.engine.find_events(0, 0, 0, True, "event",
			[{"source": [Source.USER_NOTIFICATION.uri]}])
		self.assertEquals(len(result1), 3)
		self.assertEquals(set(x["source"] for x in result2),
			set([Source.WEB_HISTORY.uri]))
		self.assertEquals(len(result2), 2)
		self.assertEquals(len(result3), 0)
	
	def testFindEventsWithApplication(self):
		self._init_with_various_events()
		result1 = self.engine.find_events(0, 0, 0, True, "event",
			[{"application": [u"/usr/share/applications/eog.desktop"]}])
		result2 = self.engine.find_events(0, 0, 0, True, "event",
			[{"application": [u"/usr/share/applications/firefox.desktop"]}])
		result3 = self.engine.find_events(0, 0, 0, True, "event",
			[{"application": [u"/usr/share/applications/gedit.desktop"]}])
		self.assertEquals(len(result1), 3)
		self.assertEquals(len(result2), 2)
		self.assertEquals(len(result3), 0)
	
	def testCountEventsMimetype(self):
		self._init_with_various_events()
		result = self.engine.find_events(0, 0, 0, True, "event",
			[{"mimetypes": [u"image/png"]}], True)
		self.assertEquals(result, 4)
	
	def testCountEventsItemsContent(self):
		self._init_with_various_events()
		result = self.engine.find_events(0, 0, 0, True, "item",
			[{"content": [Content.IMAGE.uri]}], True)
		self.assertEquals(result, 3)
	
	def testFindApplications(self):
		self._init_with_various_events()
		result = self.engine.find_events(0, 0, 0, True, u"event", [],
			return_mode=2)
		self.assertEquals(result, [(u"/usr/share/applications/eog.desktop", 3),
			(u"/usr/share/applications/firefox.desktop", 2)])
	
	def testFindApplications(self):
		self._init_with_various_events()
		result = self.engine.find_events(0, 0, 0, False, u"event",
			[], return_mode=2)
		self.assertEquals(result, [(u"/usr/share/applications/eog.desktop", 3),
			(u"/usr/share/applications/firefox.desktop", 2)])
	
	def testFindApplicationsTimestampMimetypeTags(self):
		self._init_with_various_events()
		result = self.engine.find_events(1219325, 4563533, 0, True, u"event",
			[{"mimetypes": [u"image/png"], "tags": [u"examples"]}],
			return_mode=2)
		self.assertEquals(result, [(u"/usr/share/applications/eog.desktop", 1),
			(u"/usr/share/applications/firefox.desktop", 1)])
	
	def testGetTagsNameFilter(self):
		self._init_with_various_events()
		result = self.engine.get_tags(0, 0, 0, u"f%")
		self.assertEquals(result, [(u"filtertest", 1),
			(u"files", 1)])
	
	def testGetTagsLimit(self):
		self._init_with_various_events()
		result = self.engine.get_tags(0, 0, 1, u"")
		self.assertEquals(result[0][0], u"examples")
	
	def testGetTagsTimestamp(self):
		self._init_with_various_events()
		result = self.engine.get_tags(1219330, 4000000, 0, u"")
		self.assertEquals([x[0] for x in result], [u"examples",
			u"cool_pictures", u"files", u"images", u"holidays"])
	
	def testDeleteItem(self):
		self._init_with_various_events()
		result = self.engine.find_events(0, 0, 0, True, "event", [], True)
		self.assertEquals(result, 5)
		result = self.engine.get_tags()
		self.assertEquals(len(result), 7)
		self.assertTrue(u"filtertest" in (x[0] for x in result))
		# Delete one item
		self.engine.delete_items([u"file:///tmp/test/example.jpg"])
		result = self.engine.find_events(0, 0, 0, True, "event", [], False)
		self.assertEquals(len(result), 4)
		self.assertFalse([x for x in result if x["text"] == u"example.jpg"])
		result = self.engine.get_tags()
		self.assertEquals(len(result), 5)
		self.assertFalse(u"filtertest" in (x[0] for x in result))
	
	def testDeleteItems(self):
		self.testDeleteItem()
		# Delete two items more
		uris = [u"http://image.host/cool_pictures/01.png",
			u"file:///home/foo/images/holidays/picture.png"]
		self.engine.delete_items(uris)
		result = self.engine.find_events(0, 0, 0, True, "event", [], False)
		self.assertEquals(len(result), 1)
		self.assertFalse([x for x in result if x["text"] in uris])
		result = self.engine.get_tags()
		self.assertEquals(set([x[0] for x in result]).intersection(
			set(["holidays", "cool_pictures", "examples"])), set(["examples"]))
	
	def testModifyItem(self):
		self._init_with_various_events()
		result = self.engine.find_events(0, 0, 0, True, "event",
			[{"uri": u"file:///tmp/test/example.jpg"}], False)
		self.assertEquals(len(result), 1)
		item = result[0]
		self.assertEquals(item["uri"], u"file:///tmp/test/example.jpg")
		self.assertEquals(item["tags"], u"test, examples, filtertest")
		taglist = [x for x in item["tags"].split(", ") if x != "examples"]
		item["tags"] = ", ".join(taglist + [u"modification test"])
		self.engine.update_items([item])
		result = self.engine.find_events(0, 0, 0, True, "event",
			[{"tags": [u"modification test"]}], False)
		self.assertEquals(len(result), 1)
		self.assertEquals(item, result[0])
	
	def testFindEventsInvalidFilterValues(self):
		self.assertRaises(KeyError,
			self.engine.find_events, 0, 0, 0, False, "event",
			[{"mimetype": [u"image/jpg"], "bookmarke": False}]
		)

if __name__ == "__main__":
	unittest.main()
