#!/usr/bin/python

# Update python path to use local zeitgeist module
import sys, os
from os.path import dirname, join, abspath
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

import unittest
from zeitgeist._lrucache import LRUCache

class LRUCacheTest (unittest.TestCase):
	"""
	This class tests that the zeitgeist.datamodel.Category class
	"""
	def setUp (self):
		pass
		
	def tearDown (self):
		pass
	
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
	
	
	

if __name__ == '__main__':
	unittest.main()
