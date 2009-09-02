#!/usr/bin/python

# Update python path to use local zeitgeist module
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest

from zeitgeist.dbusutils import Event

class EventTest(unittest.TestCase):
	
	incomplete_valid_dict = {"timestamp": 1, "source": "bar",
		"subject": "file:///foo", "content": "boo", "uri": "foo"}
	complete_valid_dict = {"tags": {}, "bookmark": False, "app": u"",
		"uri": u"foo", "subject": "file:///foo", "content": u"boo",
		"source": u"bar", "timestamp": 1}
	
	def test_missing_items(self):
		self.assertRaises(KeyError, Event.check_missing_items, {})
		self.assertRaises(KeyError, Event.check_missing_items, {"timestamp": 1})
		self.assertRaises(KeyError, Event.check_missing_items, {"timestamp": 1, "content": "boo"})
		self.assertRaises(KeyError, Event.check_missing_items, {"timestamp": 1, "content": "boo", "source": "bar"})
		self.assertRaises(KeyError, Event.check_missing_items, {"timestamp": 1, "content": "boo", "uri": "foo"})
		self.assertRaises(KeyError, Event.check_missing_items, {"source": "bar", "content": "boo", "uri": "foo"})
		self.assertEqual(
			Event.check_missing_items(self.incomplete_valid_dict),
			self.complete_valid_dict
		)
		# invalid key
		self.assertRaises(
			KeyError,
			Event.check_missing_items, {"timestamp": 1, "source": "bar", "content": "boo", "uri": "foo", "booo": "bar"},
		)
		# invalid type of one item
		self.assertRaises(
			ValueError,
			Event.check_missing_items, {"timestamp": "sometext", "source": "bar", "content": "boo", "uri": "foo", "subject": "file:///foo"},
		)
	
	def test_missing_items_inplace(self):
		d = dict(self.incomplete_valid_dict)
		self.assertEqual(None, Event.check_missing_items(d, True))
		self.assertEqual(
			d,
			self.complete_valid_dict
		)
	
	def test_check_dict(self):
		self.assertRaises(ValueError, Event.check_dict, {"timestamp": "boo"})

if __name__ == '__main__':
	unittest.main()
