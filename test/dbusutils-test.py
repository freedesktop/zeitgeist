#!/usr/bin/python

# Update python path to use local zeitgeist module
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest

from zeitgeist.dbusutils import EventDict

class EventDictTest(unittest.TestCase):
	
	def test_missing_items(self):
		self.assertRaises(KeyError, EventDict.check_missing_items, {})
		self.assertRaises(KeyError, EventDict.check_missing_items, {"timestamp": 1})
		self.assertRaises(KeyError, EventDict.check_missing_items, {"timestamp": 1, "content": "boo"})
		self.assertRaises(KeyError, EventDict.check_missing_items, {"timestamp": 1, "content": "boo", "source": "bar"})
		self.assertRaises(KeyError, EventDict.check_missing_items, {"timestamp": 1, "content": "boo", "uri": "foo"})
		self.assertRaises(KeyError, EventDict.check_missing_items, {"source": "bar", "content": "boo", "uri": "foo"})
		self.assertEqual(
			EventDict.check_missing_items({"timestamp": 1, "source": "bar", "content": "boo", "uri": "foo"}),
			{'comment': u'', 'origin': u'', 'use': u'', 'tags': u'', 'bookmark': False, 'text': u'', 'app': u'', 'uri': u'foo', 'content': u'boo', 'source': u'bar', 'mimetype': u'', 'timestamp': 1, 'icon': u''}
		)
		
	def test_check_dict(self):
		self.assertRaises(ValueError, EventDict.check_dict, {"timestamp": "boo"})


if __name__ == '__main__':
	unittest.main()
