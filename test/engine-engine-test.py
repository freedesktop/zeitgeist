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
		assert_cmp_dict(orig_event, result_event)
		
		content_types = [str(ctype) for ctype in self.engine.get_types()]
		self.assertTrue(Content.IMAGE in content_types)
		self.assertEquals([(u"example", 1), (u"test", 1), (u"tagtest", 1)],
			list(self.engine.get_tags()))
	
	def testBookmark (self):
		self.assertEmptyDB()
		self.assertEquals(0, len(list(self.engine.find_events(0, 0, 0, True,
			"event", [{"bookmarked": True}]))))
		orig_event = Event(
			subject = "test://mytest",
			timestamp = 0,
			source = Source.USER_ACTIVITY,
			content = Content.CREATE_EVENT,
			application = "/usr/share/applications/gnome-about.desktop",
			bookmark = False,
		)
		orig_item = Item(
			content = Content.IMAGE,
			source = Source.FILE,
			mimetype = u"mime/type",
			bookmark = True,
		)
		self.engine.insert_event(orig_event, orig_item)
		bookmarks = self.engine.find_events(0, 0, 0, True,
						"event", [{"bookmarked": True}])
		self.assertTrue(bookmarks)
		events, items = bookmarks
		self.assertEquals(1, len(items))
		self.assertEquals("test://mytest", items.keys().pop())
		tags = self.engine.get_tags()
		self.assertEquals([], list(tags))
	
	def testSameTagOnTwoItems(self):
		self.assertEmptyDB()
		events = [
			Event(
				subject = u"test://mytest1",
				timestamp = 100,
				source = Source.USER_ACTIVITY,
				content = Content.CREATE_EVENT,
				application = u"/usr/share/applications/gnome-about.desktop",
				bookmark = False),
			Event(
				subject = u"test://mytest2",
				timestamp = 1000,
				source = Source.USER_ACTIVITY,
				content = Content.CREATE_EVENT,
				application = u"/usr/share/applications/gnome-about.desktop",
				bookmark = False),
			]
		items = {
			u"test://mytest1": Item(
				content = Content.IMAGE,
				source = Source.FILE,
				test = u"Text",
				mimetype = u"mime/type",
				bookmark = False),
			u"test://mytest2": Item(
				content = Content.IMAGE,
				source = Source.FILE,
				text = "Text",
				mimetype = "mime/type",
				icon = "stock_left",
				origin = "http://example.org",
				bookmark = False),
			}
		annotations = [
			Annotation(subject = "test://mytest2", content = Content.TAG,
				source = Source.HEURISTIC_ACTIVITY, text = "eins"),
			]
		self.assertTrue(self.engine.insert_events(items, events, annotations))
		
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
		events = [Event(
			subject = "test://mytest1",
			timestamp = 0,
			source = Source.USER_ACTIVITY,
			content = Content.CREATE_EVENT,
			application = "/usr/share/applications/gnome-about.desktop"
			)]
		items = {"test://mytest1": Item(
			content = Content.IMAGE,
			source = Source.USER_ACTIVITY,
			text = "Text",
			mimetype = "mime/type",
			icon = "stock_left",
			origin = "http://example.org",
			bookmark = False
			)}
		annotations = [
			Annotation(subject = "test://mytest1", content = Content.TAG,
				source = Source.HEURISTIC_ACTIVITY, text = "eins"),
			Annotation(subject = "test://mytest1", content = Content.TAG,
				source = Source.HEURISTIC_ACTIVITY, text = "zwei"),
			Annotation(subject = "test://mytest1", content = Content.TAG,
				source = Source.HEURISTIC_ACTIVITY, text = "drei"),
			]
		self.assertTrue(self.engine.insert_events(events, items, annotations))
		tags = self.engine.get_tags()
		self.assertEquals([(u"eins", 1), (u"zwei", 1), (u"drei", 1)], tags)
		
		i = self.engine.get_items(["test://mytest1"])
		self.assertTrue(i is not None)
		self.assertEquals([u"eins", u"zwei", u"drei"],
			i["test://mytest1"]["tags"]["UserTags"])
		self.assertEquals([("eins", 1), ("zwei", 1), ("drei", 1)],
			self.engine.get_tags())
	
	def testTagAndBookmark(self):
		self.assertEmptyDB()
		item = {
				"uri" : "test://mytest1",
				"content" : Content.IMAGE,
				"source" : Source.USER_ACTIVITY,
				"app" : "/usr/share/applications/gnome-about.desktop",
				"timestamp" : 0,
				"text" : "Text",
				"mimetype" : "mime/type",
				"icon" : "stock_left",
				"use" : Content.CREATE_EVENT,
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
		
		def _utag(tag, subject): # Create UserTag
			return Annotation(subject = subject, content = Content.TAG,
				source = Source.HEURISTIC_ACTIVITY, text = tag)
		
		events = []
		items = {}
		annotations = []
		
		items["file:///tmp/test/example.jpg"] = Item(
			content = Content.IMAGE,
			source = Source.FILE,
			text = u"example.jpg",
			mimetype = u"image/jpg",
			bookmark = False
			)
		
		annotations.append(_utag("test", "file:///tmp/test/example.jpg"))
		annotations.append(_utag("examples", "file:///tmp/test/example.jpg"))
		annotations.append(_utag("filterset", "file:///tmp/test/example.jpg"))
		events.append(Event(
			subject = u"file:///tmp/test/example.jpg",
			timestamp = 1219324, # keep it lower than in item4!
			content = Content.VISIT_EVENT,
			source = Source.USER_ACTIVITY,
			application = u"/usr/share/applications/eog.desktop"
			))
		items["http://image.host/cool_pictures/01.png"] = Item(
			content = Content.IMAGE,
			source = Source.WEB_HISTORY,
			text = u"Cool Picture 1",
			mimetype = u"image/png",
			origin = u"http://google.com",
			bookmark = True
			)
		annotations.append(_utag("cool_pictures", "http://image.host/cool_pictures/01.png"))
		annotations.append(_utag("examples", "http://image.host/cool_pictures/01.png"))
		
		event2 = Event(
			subject = u"http://image.host/cool_pictures/01.png",
			timestamp = 3563534,
			content = Content.CREATE_EVENT,
			source = Source.USER_ACTIVITY,
			application = u"/usr/share/applications/firefox.desktop"
		)
		
		events.append(event2)
		# event3 is another event on http://image.host/cool_pictures/01.png
		event3 = dict(event2) # Create a copy (without dict() we get a reference)
		event3["timestamp"] = 4563534
		events.append(event3)
		self.last_insertion_app = u"/usr/share/applications/eog.desktop"
		self.last_insertion_date = 1248324
		items["file:///tmp/files/example.png"] = Item(
			content = Content.IMAGE,
			source = Source.FILE,
			text = u"example.png",
			mimetype = u"image/png",
			bookmark = False
			)
		annotations.append(_utag("examples", "file:///tmp/files/example.png"))
		annotations.append(_utag("files", "file:///tmp/files/example.png"))
		events.append(Event(
			subject = u"file:///tmp/files/example.png",
			timestamp = self.last_insertion_date,
			content = Content.CREATE_EVENT,
			source = Source.USER_ACTIVITY,
			application = self.last_insertion_app
			))
		items["file:///home/foo/images/holidays/picture.png"] = Item(
			content = Content.VIDEO,
			source = Source.FILE,
			text = u"picture.png",
			mimetype = u"image/png",
			bookmark = True
			)
		annotations.append(_utag("images", "file:///home/foo/images/holidays/picture.png"))
		annotations.append(_utag("holidays", "file:///home/foo/images/holidays/picture.png"))
		events.append(Event(
			subject = u"file:///home/foo/images/holidays/picture.png",
			timestamp = 1219335,
			content = Content.CREATE_EVENT,
			source = Source.USER_ACTIVITY,
			application = u"/usr/share/applications/eog.desktop",
			))
		self.engine.insert_events(events, items, annotations)
	
	def testGetLastInsertionDate(self):
		self._init_with_various_events()
		result = self.engine.get_last_insertion_date(self.last_insertion_app)
		self.assertEquals(result, self.last_insertion_date)
	
	def testFindEventsBookmarks(self):
		self._init_with_various_events()
		result = self.engine.find_events(0, 0, 0, True, "event",
			[{"bookmarked": True}])
		
		self.assertEquals(len([x for x in result[0]]), 3)
	
	def testFindEventsTimestamp(self):
		self._init_with_various_events()
		result = self.engine.find_events(1000000, 1250000, 0, True, "event", ())
		self.assertEquals(len([x for x in result[0]]), 3)
	
	def testFindEventsUnique(self):
		self._init_with_various_events()
		result = self.engine.find_events(0, 0, 0, True, "item", ())
		self.assertEquals(len([x for x in result[0]]), 4)
	
	def testFindEventsMostUsed(self):
		self._init_with_various_events()
		result = self.engine.find_events(0, 0, 0, False, "mostused", ())
		uri = result[0][0]["subject"]
		
		self.assertEquals(result[1][uri]["text"], u"Cool Picture 1")
	
	def testFindEventsUriAsString(self): # Deprecated (to be removed in 0.3)
		self._init_with_various_events()
		result = self.engine.find_events(0, 0, 0, False, "item",
			[{"uri": u"file:///tmp/test/%"}])
		self.assertEquals(len(result[0]), 1)
	
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
		self.assertEquals(len([x for x in result][0]), 4)
	
	def testFindEventsMimetypeWithWildcard(self):
		self._init_with_various_events()
		result = self.engine.find_events(0, 0, 0, True, "event",
			[{"mimetypes": [u"image/j%", u"image/_n_"]}])
		self.assertEquals(set([x["mimetype"] for x in result[1].values()]),
			set([u"image/jpg", u"image/png"]))
	
	def testFindEventsMimetypeAndBookmarks(self):
		self._init_with_various_events()
		result = self.engine.find_events(0, 0, 0, True, "event",
			[{"mimetypes": [u"image/jpg"], "bookmarked": True}])
		self.assertEquals(len(result), 0)
	
	def testFindEventsUniqueAndNotBookmarked(self):
		self._init_with_various_events()
		result = self.engine.find_events(0, 0, 0, True, "item",
			[{"bookmarked": False}])
		self.assertEquals(len([x for x in result[0]]), 2)
	
	def testFindEventsWithTags(self):
		self._init_with_various_events()
		result1 = self.engine.find_events(0, 0, 0, True, "event",
			[{"tags": [u"files"]}])
		result2 = self.engine.find_events(0, 0, 0, True, "event",
			[{"tags": [u"files", u"examples"]}])
		self.assertEquals(result1, result2)
		self.assertEquals(result1, [u"file:///tmp/files/example.png"])
	
	def testFindEventsWithContent(self):
		self._init_with_various_events()
		result1 = self.engine.find_events(0, 0, 0, True, "event",
			[{"content": [Content.IMAGE]}])
		result2 = self.engine.find_events(0, 0, 0, True, "event",
			[{"content": [Content.IMAGE, Content.MUSIC]}])
		result3 = self.engine.find_events(0, 0, 0, True, "event",
			[{"content": [Content.VIDEO]}])
		result4 = self.engine.find_events(0, 0, 0, True, "event",
			[{"content": [Content.MUSIC]}])
		self.assertEquals(result1, result2)
		self.assertEquals([x["content"] for x in result1[1].values()], [Content.IMAGE] * 3)
		self.assertEquals(result3[1][result3[0][0]["subject"]]["text"],  u"picture.png")
		self.assertEquals(len(result3[1]), 1)
		self.assertEquals(len(result4), 0)
	
	def testFindEventsWithSource(self):
		self._init_with_various_events()
		result1 = self.engine.find_events(0, 0, 0, True, "event",
			[{"source": [Source.USER_ACTIVITY, Source.FILE]}])
		result2 = self.engine.find_events(0, 0, 0, True, "event",
			[{"source": [Source.WEB_HISTORY]}])
		result3 = self.engine.find_events(0, 0, 0, True, "event",
			[{"source": [Source.USER_NOTIFICATION]}])
		self.assertEquals(len(result1[0]), 3)
		self.assertEquals(len(result1[1]), 3)
		self.assertEquals(set(result2[1][x]["source"] for x in result2[1]),
			set([Source.WEB_HISTORY]))
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
		self.assertEquals(len(result1[0]), 3)
		self.assertEquals(len(result2[0]), 2)
		self.assertEquals(len(result3), 0)
	
	def testCountEventsMimetype(self):
		self._init_with_various_events()
		result = self.engine.find_events(0, 0, 0, True, "event",
			[{"mimetypes": [u"image/png"]}], True)
		self.assertEquals(result, 4)
	
	def testCountEventsItemsContent(self):
		self._init_with_various_events()
		result = self.engine.find_events(0, 0, 0, True, "item",
			[{"content": [Content.IMAGE]}], True)
		self.assertEquals(result, 3)
	
	def testFindApplications(self):
		self._init_with_various_events()
		result = self.engine.find_events(0, 0, 0, True, u"event", [],
			return_mode=2)
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
		self.assertEquals(result, [(u"filterset", 1),
			(u"files", 1)])
	
	def testGetTagsLimit(self):
		self._init_with_various_events()
		result = self.engine.get_tags(0, 0, 1, u"")
		self.assertEquals(result[0][0], u"examples")
	
	def testGetTagsTimestamp(self):
		self._init_with_various_events()
		result = self.engine.get_tags(1219330, 4000000, 0, u"")
		expected = [("examples", 3),
					("cool_pictures", 1),
					("files", 1),
					("images", 1),
					("holidays", 1)]
		result.sort()
		expected.sort()		
		self.assertEquals(result, expected)
	
	def testDeleteItem(self):
		self._init_with_various_events()
		events, items = self.engine.find_events(0, 0, 0, True, "event", [], 0)
		self.assertEquals(len(items), 4)
		self.assertEquals(len(events), 5)
		result = self.engine.get_tags()
		expected = [("test", 1),
					("examples", 3),
					("filterset", 1),
					("files", 1),
					("images", 1),
					("holidays", 1),
					("cool_pictures", 1)]
		expected.sort()
		result.sort()
		self.assertEquals(len(result), 7)
		self.assertEquals(result, expected)
		# Delete one item
		self.engine.delete_items([u"file:///tmp/test/example.jpg"])
		events, items = self.engine.find_events(0, 0, 0, True, "event", [], 0)
		self.assertEquals(len(items), 3)
		self.assertEquals(len(events), 4)
		self.assertFalse(items.has_key(u"file:///tmp/test/example.jpg"))
		result = self.engine.get_tags()
		self.assertEquals(len(result), 5)
		expected = [("examples", 2),
					("files", 1),
					("images", 1),
					("holidays", 1),
					("cool_pictures", 1)]
		expected.sort()
		result.sort()
		self.assertEquals(result, expected)
	
	def testDeleteItems(self):
		self.testDeleteItem()
		# Delete two items more
		uris = [u"http://image.host/cool_pictures/01.png",
			u"file:///home/foo/images/holidays/picture.png"]
		self.engine.delete_items(uris)
		events, items = self.engine.find_events(0, 0, 0, True, "event", [], 0)
		self.assertEquals(len(items), 1)
		self.assertEquals(len(events), 1)
		self.assertTrue(items.has_key("file:///tmp/files/example.png"))
		result = self.engine.get_tags()
		expected = [("examples", 1), ("files",1)]
		result.sort()
		self.assertEquals(expected, result)
	
	def testModifyItem(self):
		self._init_with_various_events()
		events, items = self.engine.find_events(0, 0, 0, True, "event",
			[{"uri": u"file:///tmp/test/example.jpg"}], False)
		
		self.assertEquals(len(events), 1, "%s" % events)
		self.assertEquals(len(items), 1, "%s" % items)
		item = items["file:///tmp/test/example.jpg"]
		self.assertEquals(item["tags"]["UserTags"], [u'test', u'examples', u'filterset'])
		# FIXME: Is this tes obsolete? The engine doesn't expose any way
		#        to update item metadata directly // kamstrup
		#taglist = [x for x in item["tags"].split(", ") if x != "examples"]
		#item["tags"]["UserTags"].append("modification test")
		#self.engine.update_items([item])
		#result = self.engine.find_events(0, 0, 0, True, "event",
		#	[{"tags": [u"modification test"]}], False)
		#self.assertEquals(len(result), 1)
		#self.assertEquals(item, result[0])
	
	def testFindEventsInvalidFilterValues(self):
		self.assertRaises(KeyError,
			self.engine.find_events, 0, 0, 0, False, "event",
			[{"mimetype": [u"image/jpg"], "bookmarke": False}]
		)

if __name__ == "__main__":
	unittest.main()
