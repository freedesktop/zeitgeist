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
from zeitgeist.datamodel import (Event, Subject, Interpretation, Manifestation,
	TimeRange, StorageState)
import testutils

from testutils import parse_events

class ZeitgeistRemoteAPITest(testutils.RemoteTestCase):
	
	def __init__(self, methodName):
		super(ZeitgeistRemoteAPITest, self).__init__(methodName)
	
	def testInsertAndGetEvent(self):
		ev = Event.new_for_values(timestamp=123,
					interpretation=Interpretation.VISIT_EVENT,
					manifestation=Manifestation.USER_ACTIVITY,
					actor="Freak Mamma")
		subj = Subject.new_for_values(uri="void://foobar",
					interpretation=Interpretation.DOCUMENT,
					manifestation=Manifestation.FILE)
		ev.append_subject(subj)
		ids = self.insertEventsAndWait([ev])
		events = self.getEventsAndWait(ids)
		self.assertEquals(1, len(ids))
		self.assertEquals(1, len(events))
		
		ev = events[0]
		self.assertTrue(isinstance(ev, Event))
		self.assertEquals("123", ev.timestamp)
		self.assertEquals(Interpretation.VISIT_EVENT, ev.interpretation)
		self.assertEquals(Manifestation.USER_ACTIVITY, ev.manifestation)
		self.assertEquals("Freak Mamma", ev.actor)
		self.assertEquals(1, len(ev.subjects))
		self.assertEquals("void://foobar", ev.subjects[0].uri)
		self.assertEquals(Interpretation.DOCUMENT, ev.subjects[0].interpretation)
		self.assertEquals(Manifestation.FILE, ev.subjects[0].manifestation)
	
	def testFindTwoOfThreeEvents(self):
		ev1 = Event.new_for_values(timestamp=400,
					interpretation=Interpretation.VISIT_EVENT,
					manifestation=Manifestation.USER_ACTIVITY,
					actor="Boogaloo")	
		ev2 = Event.new_for_values(timestamp=500,
					interpretation=Interpretation.VISIT_EVENT,
					manifestation=Manifestation.USER_ACTIVITY,
					actor="Boogaloo")
		ev3 = Event.new_for_values(timestamp=600,
					interpretation=Interpretation.SEND_EVENT,
					manifestation=Manifestation.USER_ACTIVITY,
					actor="Boogaloo")
		subj1 = Subject.new_for_values(uri="foo://bar",
					interpretation=Interpretation.DOCUMENT,
					manifestation=Manifestation.FILE)
		subj2 = Subject.new_for_values(uri="foo://baz",
					interpretation=Interpretation.IMAGE,
					manifestation=Manifestation.FILE)
		subj3 = Subject.new_for_values(uri="foo://quiz",
					interpretation=Interpretation.MUSIC,
					manifestation=Manifestation.FILE)
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
			self.assertEquals(Manifestation.USER_ACTIVITY, event.manifestation)
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
					interpretation=Interpretation.VISIT_EVENT,
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
		
	def testGetEvents(self):
		events = parse_events("test/data/five_events.js")
		ids = self.insertEventsAndWait(events) + [1000, 2000]
		result = self.getEventsAndWait(ids)
		self.assertEquals(len(filter(None, result)), len(events))
		self.assertEquals(len(filter(lambda event: event is None, result)), 2)
	
	def testMonitorInsertEvents(self):
		result = []
		mainloop = gobject.MainLoop()
		tmpl = Event.new_for_values(interpretation="stfu:OpenEvent")
		events = parse_events("test/data/five_events.js")
		
		def notify_insert_handler(time_range, events):
			result.extend(events)
			mainloop.quit()
		
		def notify_delete_handler(time_range, event_ids):
			mainloop.quit()
			self.fail("Unexpected delete notification")
			
		self.client.install_monitor(TimeRange.always(), [tmpl],
			notify_insert_handler, notify_delete_handler)
		self.client.insert_events(events)
		mainloop.run()
		
		self.assertEquals(2, len(result))
		
	def testMonitorDeleteEvents(self):
		result = []
		mainloop = gobject.MainLoop()
		events = parse_events("test/data/five_events.js")
		
		def notify_insert_handler(time_range, events):
			event_ids = map(lambda ev : ev.id, events)
			self.client.delete_events(event_ids)
		
		def notify_delete_handler(time_range, event_ids):
			mainloop.quit()
			result.extend(event_ids)
			
			
		self.client.install_monitor(TimeRange(125, 145), [],
			notify_insert_handler, notify_delete_handler)
		
		self.client.insert_events(events)
		mainloop.run()
		
		self.assertEquals(2, len(result))
	
	def testMonitorInstallRemoval(self):
		result = []
		mainloop = gobject.MainLoop()
		tmpl = Event.new_for_values(interpretation="stfu:OpenEvent")
		
		def notify_insert_handler(notification_type, events):
		        pass
		
		def notify_delete_handler(time_range, event_ids):
			mainloop.quit()
			self.fail("Unexpected delete notification")
		
		mon = self.client.install_monitor(TimeRange.always(), [tmpl],
			notify_insert_handler, notify_delete_handler)
		
		def removed_handler(result_state):
		        result.append(result_state)
		        mainloop.quit()
		
		self.client.remove_monitor(mon, removed_handler)
		mainloop.run()
		self.assertEquals(1, len(result))
		self.assertEquals(1, result.pop())
		
	def testFindByRandomActor(self):
		result = []
		mainloop = gobject.MainLoop()
		events = parse_events("test/data/five_events.js")
		self.client.insert_events(events)
		
		template = Event.new_for_values(actor="/usr/bliblablu")
				
		ids = self.findEventIdsAndWait([template])
		self.assertEquals(len(ids), 0)
		
	def testGetMostUsedWithSubjects(self):
		events = parse_events("test/data/apriori_events.js")
		self.client.insert_events(events)
		# this will fail
		result = self.client._iface.GetMostUsedWithSubjects(["i4"],
			TimeRange.always(), [], StorageState.Any)
		self.assertEquals([unicode(x) for x in result], ["i3", "i2", "i1", "i5"])
		
	
if __name__ == "__main__":
	unittest.main()
