#!/usr/bin/python

# Update python path to use local zeitgeist module
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import _zeitgeist.engine
from _zeitgeist.engine import create_engine
from zeitgeist.datamodel import *
from _zeitgeist.engine.resonance_engine import Event, Subject


import unittest
import tempfile
import shutil


class ZeitgeistEngineTest (unittest.TestCase):
	"""
	This class tests that the zeitgeist.engine.engine.ZeitgeistEngine class
	"""
	def setUp (self):
		self.tmp_dir = tempfile.mkdtemp()	# Create a directory in /tmp/ with a random name
		_zeitgeist.engine.DB_PATH = "%s/unittest.sqlite" % self.tmp_dir
		self.engine = create_engine()
		
	def tearDown (self):
		self.engine.close()
		shutil.rmtree(self.tmp_dir)
		_zeitgeist.engine._engine = None
	
	def assertEmptyDB (self):
		# Assert before each test that the db is indeed empty
		self.assertEquals((), self.engine.find_events(0))		
		
	def assertEventsEqual(self, event1, event2, msg=None):
		for attribute in Event.Fields[:-1]:
			self.assertEquals(
				event1[attribute],
				event2[attribute],
				"failed at offset %i, is: %r / expected %r" %(
					attribute, event1[attribute], event2[attribute]
				)
			)
			if isinstance(event2[attribute], Category):
				self.assertTrue(isinstance(event1[attribute], Category))
		# now to the subjects
		subjects1 = event1[Event.Fields[-1]]
		subjects2 = event2[Event.Fields[-1]]
		self.assertEquals(len(subjects1), len(subjects2))
		
		for subject1, subject2 in zip(subjects1, subjects2):
			for subject1_attr, subject2_attr in zip(subject1, subject2):
				self.assertEquals(
					subject1_attr, subject2_attr,
					"%r != %r, %s || %s" %(
						subject1_attr, subject2_attr,subject1, subject2
					)
				)
				if isinstance(subject2_attr, Category):
					self.assertTrue(subject1_attr, Category)		
		
	def testSingleInsertGet(self):
		uri = u"test://mytest"
		
		event = Event()
		event[Event.Timestamp] = 0
		event[Event.Interpretation] = Source.USER_ACTIVITY
		event[Event.Manifestation] = Content.CREATE_EVENT
		event[Event.Actor] = "/usr/share/applications/gnome-about.desktop"
		
		self.assertEquals(len(event), len(Event.Fields))
		
		subject = Subject()
		subject[Subject.Uri] = uri
		subject[Subject.Manifestation] = "lala"
		subject[Subject.Interpretation] = "tinky winky"
		subject[Subject.Origin]  = "test://"
		subject[Subject.Mimetype] = "YOMAMA"
		subject[Subject.Text] = "SUCKS"
		subject[Subject.Storage] = "MyStorage"
		
		event.append_subject(subject)
		
		# Insert item and event
		ids = self.engine.insert_events([event])
		result = self.engine.get_events(ids)
		
		self.assertEquals(1, len(result))
		resulting_event = result.pop()
		self.assertEquals(len(resulting_event), len(event))
		
		# fixing id, the initial event does not have any id set
		event[Event.Id] = 1
		
		self.assertEventsEqual(resulting_event, event)
	
	def testDeleteSingle(self):
		self.testSingleInsertGet()
		self.engine.delete_events([1])
		result = self.engine.get_events([1])
		self.assertEquals(0, len(filter(None, result)))
	
	def testIllegalPredefinedEventId(self):
		event = Event()
		event[Event.Id] = 23 # This is illegal, we assert the erro later
		event[Event.Timestamp] = 0
		event[Event.Interpretation] = Source.USER_ACTIVITY
		event[Event.Manifestation] = Content.CREATE_EVENT
		event[Event.Actor] = "/usr/share/applications/gnome-about.desktop"
		
		subject = Subject()
		subject[Subject.Uri] = "file:///tmp/file.txt"
		subject[Subject.Manifestation] = Source.FILE
		subject[Subject.Interpretation] = Content.DOCUMENT
		subject[Subject.Origin]  = "test://"
		subject[Subject.Mimetype] = "text/plain"
		subject[Subject.Text] = "This subject has no text"
		subject[Subject.Storage] = "368c991f-8b59-4018-8130-3ce0ec944157" # UUID of home partition
		
		event.append_subject(subject)
		
		# Insert item and event
		self.assertRaises(ValueError, self.engine.insert_events, [event])
		
	def testGetNonExisting(self):
		events = self.engine.get_events([23,45,65])
		self.assertEquals(3, len(events))
		for ev in events : self.assertEquals(None, ev)
		
	def testFindEventsId(self):
		self.testSingleInsertGet()
		result = self.engine.find_eventids(
			(0, 100),
			[],
			0,
			5,
			0,)
		print result

if __name__ == "__main__":
	unittest.main()
