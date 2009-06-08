#!/usr/bin/python

# Update python path to use local xesam module
import sys, os
from os.path import dirname, join, abspath
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)+"/.."))

from zeitgeist.engine.base import *
from storm.locals import *
import unittest

class EventTest (unittest.TestCase):
	"""
	This class tests that the zeitgeist.engine.base.Event class
	"""
	def setUp (self):
		self.store = reset_store("sqlite:unittest.sqlite")		
		
	def tearDown (self):
		pass
	
	def testCreateEvent (self):
		i = Item("it1")
		e = Event("ev1", i.uri.value)
		
		self.assertTrue(e.subject is i)
		self.assertEquals("ev1", e.item.uri.value)
		self.assertTrue("i1", i.uri.value)
	
	def testCreateTwoEventsNoFlush (self):
		i = Item("it1")
		e1 = Event("ev1", i.uri) # Create by direct ref
		e2 = Event("ev2", i.uri.value) # Create by indirect lookup via uri

		self.assertTrue(e1.subject is i)
		self.assertTrue(e2.subject is i)

class ItemTest (unittest.TestCase):
	"""
	This class tests that the zeitgeist.engine.base.Item class
	"""
	def setUp (self):
		self.store = reset_store("sqlite:unittest.sqlite")
		
	def tearDown (self):
		pass
	
	def testCreateItem(self):
		i = Item("i1")
		self.assertEquals("i1", i.uri.value)
		self.assertEquals(1, i.uri.id)

	def testCreateTwoItems(self):
		i1 = Item("i1")
		i2 = Item("i2")
		self.assertEquals("i1", i1.uri.value)
		self.assertEquals(1, i1.uri.id)
		self.assertEquals("i2", i2.uri.value)
		self.assertEquals(2, i2.uri.id)
	
	def testFindOneItemNoFlush(self):
		i = Item("i1")
		ii = self.store.find(Item, Item.id == URI.id, URI.value == u"i1").one()
		self.assertTrue(i is ii)

	def testCreateManyItemNoFlush(self):
		# Insert a lot of items
		for i in range(100):
			Item("i%s" % i)		
				
		# Read them again
		count = 0
		for i in self.store.find(Item).order_by(Item.id):
			self.assertEquals(u"i%s" % count, i.uri.value)
			count += 1
			self.assertEquals(count, i.uri.id)			
		
		self.assertEquals(100, count)
		
	
if __name__ == '__main__':
	unittest.main()


