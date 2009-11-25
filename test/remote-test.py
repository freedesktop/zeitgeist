#! /usr/bin/python

import unittest
import os
import time
import sys
import signal
from subprocess import Popen, PIPE

# DBus setup
import gobject
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

# Import local Zeitgeist modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from zeitgeist.client import ZeitgeistDBusInterface, ZeitgeistClient
from zeitgeist.datamodel import Event, Subject, Interpretation, Manifestation, TimeRange
import testutils

from testutils import parse_events

class ZeitgeistRemoteAPITest(testutils.RemoteTestCase):
	
	def __init__(self, methodName):
		super(ZeitgeistRemoteAPITest, self).__init__(methodName)
	
	def testInsertAndGetEvent(self):
		ev = Event.new_for_values(timestamp=123,
					interpretation=Interpretation.VISIT_EVENT.uri,
					manifestation=Manifestation.USER_ACTIVITY.uri,
					actor="Freak Mamma")
		subj = Subject.new_for_values(uri="void://foobar",
					interpretation=Interpretation.DOCUMENT.uri,
					manifestation=Manifestation.FILE.uri)
		ev.append_subject(subj)
		ids = self.insertEventsAndWait([ev])
		events = self.getEventsAndWait(ids)
		self.assertEquals(1, len(ids))
		self.assertEquals(1, len(events))
		
		ev = events[0]
		self.assertTrue(isinstance(ev, Event))
		self.assertEquals("123", ev.timestamp)
		self.assertEquals(Interpretation.VISIT_EVENT.uri, ev.interpretation)
		self.assertEquals(Manifestation.USER_ACTIVITY.uri, ev.manifestation)
		self.assertEquals("Freak Mamma", ev.actor)
		self.assertEquals(1, len(ev.subjects))
		self.assertEquals("void://foobar", ev.subjects[0].uri)
		self.assertEquals(Interpretation.DOCUMENT.uri, ev.subjects[0].interpretation)
		self.assertEquals(Manifestation.FILE.uri, ev.subjects[0].manifestation)
		
	def testFindTwoOfThreeEvents(self):
		ev1 = Event.new_for_values(timestamp=400,
					interpretation=Interpretation.VISIT_EVENT.uri,
					manifestation=Manifestation.USER_ACTIVITY.uri,
					actor="Boogaloo")	
		ev2 = Event.new_for_values(timestamp=500,
					interpretation=Interpretation.VISIT_EVENT.uri,
					manifestation=Manifestation.USER_ACTIVITY.uri,
					actor="Boogaloo")
		ev3 = Event.new_for_values(timestamp=600,
					interpretation=Interpretation.SEND_EVENT.uri,
					manifestation=Manifestation.USER_ACTIVITY.uri,
					actor="Boogaloo")
		subj1 = Subject.new_for_values(uri="foo://bar",
					interpretation=Interpretation.DOCUMENT.uri,
					manifestation=Manifestation.FILE.uri)
		subj2 = Subject.new_for_values(uri="foo://baz",
					interpretation=Interpretation.IMAGE.uri,
					manifestation=Manifestation.FILE.uri)
		subj3 = Subject.new_for_values(uri="foo://quiz",
					interpretation=Interpretation.MUSIC.uri,
					manifestation=Manifestation.FILE.uri)
		ev1.append_subject(subj1)
		ev2.append_subject(subj1)
		ev2.append_subject(subj2)
		ev3.append_subject(subj2)
		ev3.append_subject(subj3)
		ids = self.insertEventsAndWait([ev1, ev2, ev3])
		self.assertEquals(3, len(ids))
		
		events = self.getEventsAndWait(ids)
		self.assertEquals(3, len(events))		
		for event in events:
			self.assertTrue(isinstance(event, Event))
			self.assertEquals(Manifestation.USER_ACTIVITY.uri, event.manifestation)
			self.assertEquals("Boogaloo", event.actor)
		
		# Search for everything
		import dbus
		ids = self.findEventIdsAndWait([], num_events=3) # dbus.Array(signature="(asaasay)")
		self.assertEquals(3, len(ids)) # (we can not trust the ids because we don't have a clean test environment)
		
		# Search for some specific templates
		subj_templ1 = Subject.new_for_values(uri="foo://bar")
		subj_templ2 = Subject.new_for_values(uri="foo://baz")
		event_template = Event.new_for_values(
					actor="Boogaloo",
					interpretation=Interpretation.VISIT_EVENT.uri,
					subjects=[subj_templ1,subj_templ2])
		ids = self.findEventIdsAndWait([event_template],
						num_events=10)
		print "RESULTS", map(int, ids)
		self.assertEquals(2, len(ids))
		
	def testUnicodeInsert(self):
		events = parse_events("test/data/unicode_event.js")
		ids = self.insertEventsAndWait(events)
		self.assertEquals(len(ids), len(events))
		result_events = self.getEventsAndWait(ids)
		self.assertEquals(len(ids), len(result_events))
		

	
if __name__ == "__main__":
	unittest.main()
