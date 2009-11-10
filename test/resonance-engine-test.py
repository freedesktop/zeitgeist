#!/usr/bin/python

# Update python path to use local zeitgeist module
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import _zeitgeist.engine
from _zeitgeist.engine import get_default_engine
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
		self.engine = get_default_engine()
		
	def tearDown (self):		
		shutil.rmtree(self.tmp_dir)
	
	def assertEmptyDB (self):
		# Assert before each test that the db is indeed empty
		self.assertEquals((), self.engine.find_events(0))		
		
	def testSingleInsertGet(self):
		uri = u"test://mytest"
		
		event = Event()
		event[Event.Timestamp] = 0
		event[Event.Interpretation] = Source.USER_ACTIVITY
		event[Event.Manifestation] = Content.CREATE_EVENT
		event[Event.Actor] = "/usr/share/applications/gnome-about.desktop"
		
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
		resulting_event[Event.Timestamp] = event[Event.Timestamp]
		resulting_event[Event.Interpretation] = event[Event.Interpretation]
		resulting_event[Event.Manifestation] = event[Event.Manifestation]
		resulting_event[Event.Actor] = event[Event.Actor]
	

if __name__ == "__main__":
	unittest.main()
