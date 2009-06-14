#!/usr/bin/python

# Update python path to use local zeitgeist module
import sys, os
from os.path import dirname, join, abspath
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

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

if __name__ == '__main__':
	unittest.main()
