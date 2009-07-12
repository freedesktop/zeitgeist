#!/usr/bin/python

# Update python path to use local zeitgeist module
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from zeitgeist.datamodel import *

import unittest

class CategoryTest (unittest.TestCase):
	"""
	This class tests that the zeitgeist.datamodel.Category class
	"""
	def setUp (self):
		pass
		
	def tearDown (self):
		pass
	
	def testAbstractClass(self):
		"""Make sure that we can not instantiate a Cateory directly"""
		self.failUnlessRaises(ValueError, Category, "http://example.com/schema#Foo")
		self.failUnlessRaises(ValueError, Category.get, "http://example.com/schema#Foo")

class ContentTest (unittest.TestCase):
	"""
	This class tests that the zeitgeist.datamodel.Content class
	"""
	def setUp (self):
		pass
		
	def tearDown (self):
		Content.CACHE = {}
	
	def testCleanCache(self):
		"""Assert that the cache is clear - for the sake of a clean test env."""
		self.assertEquals(0, len(Content.CACHE))

	def testConstructors(self):
		foo_url = "http://example.com/schema#Foo"
		foo = Content(foo_url)
		self.assertEquals("Foo", foo.name)
		self.assertEquals(foo_url, foo.uri)
	
	def testCache(self):
		foo_url = "http://example.com/schema#Foo"
		foo1 = Content(foo_url)
		foo2 = Content.get(foo_url)
		self.assertEquals(id(foo1), id(foo2))

	def testPredefined(self):
		tag = Content.TAG
		self.assertTrue(tag.name != None)
		self.assertTrue(tag.uri != None)
		self.assertTrue(tag.display_name != None)
		self.assertTrue(tag.doc != None)

class SourceTest (unittest.TestCase):
	"""
	This class tests that the zeitgeist.datamodel.Source class
	"""
	def setUp (self):
		pass
		
	def tearDown (self):
		Source.CACHE = {}

	def testCleanCache(self):
		"""Assert that the cache is clear - for the sake of a clean test env."""
		self.assertEquals(0, len(Source.CACHE))

	def testConstructors(self):
		foo_url = "http://example.com/schema#Foo"
		foo = Source(foo_url)
		self.assertEquals("Foo", foo.name)
		self.assertEquals(foo_url, foo.uri)
	
	def testCache(self):
		foo_url = "http://example.com/schema#Foo"
		foo1 = Source(foo_url)
		foo2 = Source.get(foo_url)
		self.assertEquals(id(foo1), id(foo2))
	
	def testPredefined(self):
		f = Source.FILE
		self.assertTrue(f.name != None)
		self.assertTrue(f.uri != None)
		self.assertTrue(f.display_name != None)
		self.assertTrue(f.doc != None)

if __name__ == '__main__':
	unittest.main()
