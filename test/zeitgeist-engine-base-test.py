#!/usr/bin/python

# Update python path to use local zeitgeist module
import sys, os, tempfile, shutil
from os.path import dirname, join, abspath
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from zeitgeist.engine.base import *
from storm.locals import *
import unittest

class SymbolTest(unittest.TestCase):
	"""
	This class tests that the zeitgeist.engine.base.Symbol class
	"""
	# Since the symbols in the Source and Content are defined in class
	# scope they will not be reloaded even if we nuke the test environment
	# Therefore we need to use custom instances of the symbols in the tests
	def setUp (self):
		storm_url = "sqlite:/tmp/unittest.sqlite"
		db_file = storm_url.split(":")[1]
		if os.path.exists(db_file):
			os.remove(db_file)
		self.store = create_store(storm_url)
		set_store(self.store)
		
	def tearDown (self):
		self.store.close()
	
	def testSingleSymbol(self):
		s = Symbol(Source, Source.WEB_HISTORY.value)
		self.assertEquals(Source.WEB_HISTORY.value, s.value)
		self.assertEquals(1, Source.WEB_HISTORY.id)
		self.assertEquals("WebHistory", Source.WEB_HISTORY.name)
	
	def testContentSourceSymbols(self):
		s = Symbol(Source, Source.WEB_HISTORY.value)
		c = Symbol(Content, Content.TAG.value)
		
		self.assertEquals(Source.WEB_HISTORY.value, s.value)
		self.assertEquals(1, s.id) # First element in the source table
		self.assertEquals("WebHistory", s.name)
		
		self.assertEquals(Content.TAG.value, c.value)
		self.assertEquals(1, c.id) # First element in the content table
		self.assertEquals("Tag", c.name)
	
	def testTwoSourceSymbols(self):
		web = Symbol(Source, Source.WEB_HISTORY.value)
		act = Symbol(Source, Source.USER_ACTIVITY.value)
		
		self.assertEquals("WebHistory", web.name)
		self.assertEquals(Source.WEB_HISTORY.value, web.value)
		self.assertEquals(1, web.id) # First element in the source table
		
		self.assertEquals("UserActivity", act.name)
		self.assertEquals(Source.USER_ACTIVITY.value, act.value)
		self.assertEquals(2, act.id) # Second element in the source table
		

class SourceTest (unittest.TestCase):
	"""
	This class tests that the zeitgeist.engine.base.Source class
	"""
	def setUp (self):
		storm_url = "sqlite:/tmp/unittest.sqlite"
		db_file = storm_url.split(":")[1]
		if os.path.exists(db_file):
			os.remove(db_file)
		self.store = create_store(storm_url)
		set_store(self.store)
		
	def tearDown (self):
		self.store.close()
	
	def testSingleSource(self):
		s = Source.lookup_or_create(Source.WEB_HISTORY)
		self.assertEquals(Source.WEB_HISTORY.value, s.value)
	
	def testTwoSources(self):		
		s1 = Source.lookup_or_create(Source.WEB_HISTORY)
		s2 = Source.lookup_or_create(Source.USER_ACTIVITY)
		s1.resolve()
		s2.resolve()
		
		self.assertEquals(Source.WEB_HISTORY.value, s1.value)
		self.assertEquals(Source.USER_ACTIVITY.value, s2.value)
		self.assertEquals(1, s1.id)
		self.assertEquals(2, s2.id)

class URITest (unittest.TestCase):
	"""
	This class tests that the zeitgeist.engine.base.URI class
	"""
	def setUp (self):
		storm_url = "sqlite:/tmp/unittest.sqlite"
		db_file = storm_url.split(":")[1]
		if os.path.exists(db_file):
			os.remove(db_file)
		self.store = create_store(storm_url)
		set_store(self.store)
		
	def tearDown (self):
		self.store.close()
	
	def testCreateUnFlushedWithLookup(self):
		u = URI("u1")
		uu = URI.lookup("u1")	
		self.assertEquals(u.id, uu.id)
		self.assertEquals(u.value, uu.value)
	
	def testCreateFlushedWithLookup(self):
		u = URI("u1")
		self.store.flush()
		uu = URI.lookup("u1")
		self.assertEquals(u.id, uu.id)
		self.assertEquals(u.value, uu.value)
		
	def testLookupOrCreateTwo(self):
		u1 = URI.lookup_or_create("u1")
		u2 = URI.lookup_or_create("u2")
		u3 = URI("u3")
		
		self.assertEquals(id(u1), id(URI.lookup_or_create("u1")))
		self.assertEquals(id(u2), id(URI.lookup_or_create("u2")))
		self.assertEquals(id(u3), id(URI.lookup_or_create("u3")))
		self.assertTrue(id(u2) != id(u1))
		self.assertEquals(1, u1.id)
		self.assertEquals(2, u2.id)
		self.assertEquals(3, u3.id)

class ItemTest (unittest.TestCase):
	"""
	This class tests that the zeitgeist.engine.base.Item class
	"""	
	def setUp (self):
		self.tmp_dir = tempfile.mkdtemp()	# Create a directory in /tmp/ with a random name
		storm_url = "sqlite:%s/unittest.sqlite" % self.tmp_dir
		self.store = create_store(storm_url)
		set_store(self.store)
		
	def tearDown (self):		
		self.store.close()
		shutil.rmtree(self.tmp_dir)
	
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
		self.assertTrue(i is Item.lookup("i1"))

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
	
	def testLookupNoFlush(self):
		i = Item("i1")
		ii = Item.lookup("i1")
		
		self.assertEquals("i1", i.uri.value)
		self.assertEquals("i1", ii.uri.value)
		self.assertEquals(1, i.uri.id)
		self.assertEquals(1, ii.uri.id)
	
	def testResetLookup(self):
		i = Item("i1")
		self.store.flush()
		self.store.close()
		self.setUp()
		i = Item.lookup_or_create("i1")
		self.assertEquals("i1", i.uri.value)
	
	def testLookupOrCreateTwo(self):
		i1 = Item.lookup_or_create("i1")
		i2 = Item.lookup_or_create("i2")
		
		self.assertEquals(id(i1), id(Item.lookup_or_create("i1")))
		self.assertEquals(id(i2), id(Item.lookup_or_create("i2")))

class EventTest (unittest.TestCase):
	"""
	This class tests that the zeitgeist.engine.base.Event class
	"""
	def setUp (self):
		storm_url = "sqlite:/tmp/unittest.sqlite"
		db_file = storm_url.split(":")[1]
		if os.path.exists(db_file):
			os.remove(db_file)
		self.store = create_store(storm_url)
		set_store(self.store)
		
	def tearDown (self):
		self.store.close()
	
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
	
	def testCreateThreeEventsNoFlush (self):
		i = Item("it1")
		e1 = Event("ev1", i.uri) # Create by direct ref
		e2 = Event("ev2", i.uri.value) # Create by indirect lookup via uri
		e3 = Event("ev3", i.uri) # Create by direct ref
		
		self.assertTrue(e1.subject is i)
		self.assertTrue(e2.subject is i)
		self.assertTrue(e3.subject is i)
	
	def testLookupNoFlush (self):
		i = Item("it1")
		e = Event("ev1", i.uri) # Create by direct ref
		ee = Event.lookup("ev1")

		self.assertEquals(i.uri.value, e.subject.uri.value)
		self.assertTrue(i.uri.value, ee.subject.uri.value)

	def testCreateManyEventsOnSameSubjectNoFlush(self):
		subj = Item("subj1")
		app = App("myApp")
		# Insert a lot of items
		for i in range(100):
			e = Event("ev%s" % i, subj.uri)
			e.app = app
			e.start = 0
			e.end = 1
		
		# Read them again, with store.find()
		count = 0
		for ev in self.store.find(Event).order_by(Event.item_id):
			self.assertEquals(u"ev%s" % count, ev.item.uri.value)
			self.assertTrue(ev.subject is subj)
			self.assertTrue(ev.app is app)
			count += 1
			
			# Offset is +1 because of initial 'subj' Item and 'app' App
			self.assertEquals(count + 2, ev.item.uri.id)
		
		self.assertEquals(100, count)
		
		# Now try and read them with lookup()
		count = 0
		for i in range(100):
			ev = Event.lookup("ev%s" % i)
			self.assertEquals(u"ev%s" % count, ev.item.uri.value)
			self.assertTrue(ev.subject is subj)
			self.assertTrue(ev.app is app)
			count += 1
			
			# Offset is +1 because of initial 'subj' Item and 'app' App
			self.assertEquals(count + 2, ev.item.uri.id)

	def testCreateManyEventsOnDifferentSubjectsNoFlush(self):		
		app = App("myApp")
		# Insert a lot of items
		for i in range(100):
			subj = Item("subj%s" % i)
			e = Event("ev%s" % i, subj.uri)			
			e.app = app
			e.start = 0
			e.end = 1
		
		# Read them again, with store.find()
		count = 0
		for ev in self.store.find(Event).order_by(Event.item_id):
			self.assertEquals(u"ev%s" % count, ev.item.uri.value)
			self.assertEquals(u"subj%s" % count, ev.subject.uri.value)			
			self.assertTrue(ev.app is app)
			count += 1
			
			# Offset is +1 because of initial and 'app' App, and then 
			#every other object is an Item, so *2
			self.assertEquals((2*count) +1, ev.item.uri.id)
			self.assertEquals((2*count), ev.subject.uri.id)
		
		self.assertEquals(100, count)
		
		# Now try and read them with lookup()
		count = 0
		for i in range(100):
			ev = Event.lookup("ev%s" % i)
			self.assertEquals(u"ev%s" % count, ev.item.uri.value)
			self.assertTrue(u"subj%s" % count, ev.subject.uri.value)
			self.assertTrue(ev.app is app)
			count += 1
			
			# Offset is +1 because of initial and 'app' App, and then 
			#every other object is an Item, so *2
			self.assertEquals((2*count) +1, ev.item.uri.id)
			self.assertEquals((2*count), ev.subject.uri.id)


class AnnotationTest (unittest.TestCase):
	"""
	This class tests that the zeitgeist.engine.base.Annotation class
	"""
	def setUp (self):
		storm_url = "sqlite:/tmp/unittest.sqlite"
		db_file = storm_url.split(":")[1]
		if os.path.exists(db_file):
			os.remove(db_file)
		self.store = create_store(storm_url)
		set_store(self.store)
		
	def tearDown (self):
		self.store.close()
	
	def testCreateAnnotation (self):
		i = Item("it1")
		a = Annotation("an1", i.uri)
		
		self.assertTrue(a.subject is i)
		self.assertEquals("an1", a.uri.value)
		self.assertTrue("i1", i.uri.value)
	
	def testCreateTwoAnnotationsNoFlush (self):
		i = Item("it1")
		a1 = Annotation("an1", i.uri) # Create by direct ref
		a2 = Annotation("an2", i.uri.value) # Create by indirect lookup via uri

		self.assertEquals(i.uri.value, a1.subject.uri.value)
		self.assertEquals(i.uri.value, a2.subject.uri.value)
	
	def testLookupNoFlush (self):
		i = Item("it1")
		a = Annotation("an1", i.uri) # Create by direct ref
		aa = Annotation.lookup("an1")

		self.assertEquals(i.uri.value, a.subject.uri.value)
		self.assertTrue(i.uri.value, aa.subject.uri.value)
		
		self.assertEquals("an1", a.uri.value)
		self.assertEquals("an1", aa.uri.value)
	
	def testLookupOrCreate(self):
		i = Item("it1")
		a = Annotation.lookup_or_create("an1")
		a.subject = i
		self.store.flush()
		aa = Annotation.lookup("an1")
		self.assertEquals("an1", aa.uri.value)
		self.assertEquals(1, i.id)
		self.assertEquals(1, a.subject_id)
		self.assertEquals(1, aa.subject_id)
		
	
if __name__ == "__main__":
	unittest.main()
