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
		"""Make sure that we can not instantiate a Category directly"""
		self.failUnlessRaises(ValueError, Category, "http://example.com/schema#Foo")
		self.failUnlessRaises(ValueError, Category.get, "http://example.com/schema#Foo")

class InterpretationTest (unittest.TestCase):
	"""
	This class tests that the zeitgeist.datamodel.Interpretation class
	"""
	def setUp (self):
		pass
		
	def tearDown (self):
		Interpretation.CACHE = {}
	
	def testCleanCache(self):
		"""Assert that the cache is clear - for the sake of a clean test env."""
		self.assertEquals(0, len(Interpretation.CACHE))

	def testConstructors(self):
		foo_url = "http://example.com/schema#Foo"
		foo = Interpretation(foo_url)
		self.assertEquals("Foo", foo.name)
		self.assertEquals(foo_url, foo.uri)
	
	def testCache(self):
		foo_url = "http://example.com/schema#Foo"
		foo1 = Interpretation(foo_url)
		foo2 = Interpretation.get(foo_url)
		self.assertEquals(id(foo1), id(foo2))

	def testPredefined(self):
		tag = Interpretation.TAG
		self.assertTrue(tag.name != None)
		self.assertTrue(tag.uri != None)
		self.assertTrue(tag.display_name != None)
		self.assertTrue(tag.doc != None)

class ManifestationTest (unittest.TestCase):
	"""
	This class tests that the zeitgeist.datamodel.Manifestation class
	"""
	def setUp (self):
		pass
		
	def tearDown (self):
		Manifestation.CACHE = {}

	def testCleanCache(self):
		"""Assert that the cache is clear - for the sake of a clean test env."""
		self.assertEquals(0, len(Manifestation.CACHE))

	def testConstructors(self):
		foo_url = "http://example.com/schema#Foo"
		foo = Manifestation(foo_url)
		self.assertEquals("Foo", foo.name)
		self.assertEquals(foo_url, foo.uri)
	
	def testCache(self):
		foo_url = "http://example.com/schema#Foo"
		foo1 = Manifestation(foo_url)
		foo2 = Manifestation.get(foo_url)
		self.assertEquals(id(foo1), id(foo2))
	
	def testPredefined(self):
		f = Manifestation.FILE
		self.assertTrue(f.name != None)
		self.assertTrue(f.uri != None)
		self.assertTrue(f.display_name != None)
		self.assertTrue(f.doc != None)

class EventTest (unittest.TestCase):
	def setUp(self):
		pass
	
	def tearDown(self):
		pass
	
	def testSimple(self):
		ev = Event()
		
		ev.id = 1
		self.assertEquals(1, ev.id)
		
		ev.timestamp = 10
		self.assertEquals(10, ev.timestamp)

if __name__ == '__main__':
	unittest.main()
