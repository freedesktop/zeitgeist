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
		self.engine.close()
		shutil.rmtree(self.tmp_dir)
	
	def assertEmptyDB (self):
		# Assert before each test that the db is indeed empty
		self.assertEquals((), self.engine.find_events(0))		
		
	def testSingleInsertGet(self):
		uri = u"test://mytest"
		'''
		orig_event = {
			"subject": uri,
			"timestamp": 0,
			"source": Source.USER_ACTIVITY,
			"content": Content.CREATE_EVENT,
			"application": "/usr/share/applications/gnome-about.desktop",
			"tags": {},
			"bookmark": False,
		}
		orig_item = {
			"content": Content.IMAGE,
			"source": Source.FILE,
			"mimetype": "mime/type",
			"bookmark": True,
		}
		'''
		event = Event()
		event[Event.Timestamp] = 0,
		event[Event.Interpretation] = Source.USER_ACTIVITY,
		event[Event.Manifestation] = Content.CREATE_EVENT,
		event[Event.Actor] = "/usr/share/applications/gnome-about.desktop",
		event[Event.Origin]  = "zg:lala"
		
		subject = Subject()
		subject[Subject.Uri] = uri
		subject[Subject.Manifestation] = "lala"
		subject[Subject.Interpretation] = "tinky winky"
		subject[Subject.Mimetype] = "YOMAMA"
		subject[Subject.Text] = "SUCKS"
		
		event.append_subject(subject)
		
		# Insert item and event
		ids = self.engine.insert_events([event])
		result = self.engine.get_events(ids)
		
		#self.assertEquals(1, num_inserts)

if __name__ == "__main__":
	unittest.main()
