#!/usr/bin/python

# Update python path to use local zeitgeist module
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from _zeitgeist.lrucache import LRUCache

import unittest

class LRUCacheTest(unittest.TestCase):
	
	def testPutGetOne(self):
		"""Test that we can cache and then retrieve one single item"""
		cache = LRUCache(10)
		cache["foo"] = "bar"
		self.assertEquals("bar", cache["foo"])
		self.assertRaises(KeyError, lambda : cache["nosuchelement"])
	
	def testPutGetTwo(self):
		"""Test that we can cache and then retrieve two items"""
		cache = LRUCache(10)
		cache["foo1"] = "bar1"
		cache["foo2"] = "bar2"
		self.assertEquals("bar1", cache["foo1"])
		self.assertEquals("bar2", cache["foo2"])
		self.assertRaises(KeyError, lambda : cache["nosuchelement"])
		
	def testExceedMaxSize(self):
		"""Test that we can restrict the cache size to one element, and that
		   this one element is the latest one we've added"""
		cache = LRUCache(1)
		cache["foo1"] = "bar1"
		cache["foo2"] = "bar2"
		self.assertRaises(KeyError, lambda : cache["foo1"])
		self.assertEquals("bar2", cache["foo2"])
		self.assertEquals(1, len(cache))
		
	def testInKeyword(self):
		"""Make sure we can do 'if "foo" in cache' type of statements"""
		cache = LRUCache(5)
		cache["foo1"] = "bar1"
		self.assertFalse("bork" in cache)
		self.assertTrue("foo1" in cache)
	
	def testIteration(self):
		"""Make sure that iteration is in the correct order; oldest to newest"""
		cache = LRUCache(4)
		cache["foo1"] = "bar1"
		cache["foo2"] = "bar2"
		cache["foo3"] = "bar3"
		cache["foo4"] = "bar4"
		cache["foo1"] = "bar1" # "foo1" should now be newest
		
		l = []
		for key_val in cache : l.append(key_val)
		self.assertEquals([("foo2", "bar2"),
		                   ("foo3", "bar3"),
		                   ("foo4", "bar4"),
		                   ("foo1", "bar1")], l)
		                   
	def testDeleteItem(self):
		cache = LRUCache(4)
		cache["foo1"] = "bar1"
		cache["foo2"] = "bar2"
		cache["foo3"] = "bar3"
		cache["foo4"] = "bar4"
		self.assertTrue("foo2" in cache)
		del cache["foo2"] # delete item in the middle of the cache
		self.assertTrue("foo2" not in cache)
		self.assertEquals(
			[("foo1", "bar1"), ("foo3", "bar3"), ("foo4", "bar4")],
			list(cache)
		)
		self.assertTrue("foo1" in cache)
		del cache["foo1"] # delete first item
		self.assertTrue("foo1" not in cache)
		self.assertEquals(
			[("foo3", "bar3"), ("foo4", "bar4")],
			list(cache)
		)
		self.assertTrue("foo4" in cache)
		del cache["foo4"] # delete last item
		self.assertTrue("foo4" not in cache)
		self.assertEquals(
			[("foo3", "bar3")],
			list(cache)
		)
		del cache["foo3"]
		self.assertTrue("foo3" not in cache)
		self.assertEquals([], list(cache))
		self.assertTrue(cache._list_start is None)
		self.assertTrue(cache._list_end is None)
		
		
if __name__ == '__main__':
	unittest.main()