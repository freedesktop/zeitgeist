#!/usr/bin/python
# -.- coding: utf-8 -.-

# Update python path to use local zeitgeist module
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest

from zeitgeist.client import ZeitgeistClient
from zeitgeist import datamodel

import testutils
from testutils import parse_events

class EventAndSubjectOverrides (testutils.RemoteTestCase):
	"""
	This class tests the functionality allowing users to override the
	Event and Subject types instantiated by ZeitgeistClient (LP: #799199).
	"""

	class CustomEvent(datamodel.Event):
		pass
	
	class CustomSubject(datamodel.Subject):
		pass

	class CustomNothing(object):
		pass

	def testEventOverrideWhiteBox(self):
		self.assertEqual(self.client._event_type, datamodel.Event)
		self.client.register_event_subclass(self.CustomEvent)
		self.assertEqual(self.client._event_type, self.CustomEvent)

	def testSubjectOverrideWhiteBox(self):
		self.assertEqual(self.client._event_type._subject_type, datamodel.Subject)
		self.client.register_subject_subclass(self.CustomSubject)
		self.assertEqual(self.client._event_type._subject_type, self.CustomSubject)

	def testEventAndSubjectOverrideWhiteBox(self):
		self.client.register_event_subclass(self.CustomEvent)
		self.client.register_subject_subclass(self.CustomSubject)
		self.assertTrue(issubclass(self.client._event_type, self.CustomEvent))
		self.assertEqual(self.client._event_type._subject_type, self.CustomSubject)

	def testBadOverride(self):
		self.assertRaises(TypeError, lambda:
			self.client.register_event_subclass(self.CustomNothing))
		self.assertRaises(TypeError, lambda:
			self.client.register_subject_subclass(self.CustomNothing))

	def testEventAndSubjectOverrideBlackBox(self):
		self.client.register_event_subclass(self.CustomEvent)
		self.client.register_subject_subclass(self.CustomSubject)
		self.insertEventsAndWait(parse_events("test/data/single_event.js"))
		result = self.findEventsForValuesAndWait()
		self.assertTrue(len(result[0].subjects) >= 1)
		self.assertTrue(isinstance(result[0], self.CustomEvent))
		self.assertTrue(isinstance(result[0].subjects[0], self.CustomSubject))

	def testMonitorOverrideBlackBox(self):
		self.client.register_event_subclass(self.CustomEvent)
		self.client.register_subject_subclass(self.CustomSubject)
		mainloop = self.create_mainloop()
		
		def notify_insert_handler(time_range, events):
			self.assertTrue(len(events[0].subjects) >= 1)
			self.assertTrue(isinstance(events[0], self.CustomEvent))
			self.assertTrue(
				isinstance(events[0].subjects[0], self.CustomSubject))
			mainloop.quit()
		
		self.client.install_monitor(datamodel.TimeRange.always(), [],
			notify_insert_handler, notify_insert_handler)
		self.client.insert_events(parse_events("test/data/single_event.js"))
		mainloop.run()
