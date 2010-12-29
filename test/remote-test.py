#! /usr/bin/python
# -.- coding: utf-8 -.-

import unittest
import os
import sys
import logging
import signal
import time
import tempfile
import shutil
import pickle
from subprocess import Popen, PIPE

# DBus setup
import gobject
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

# Import local Zeitgeist modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _zeitgeist.engine.datamodel import Event as ZgEvent
from zeitgeist.datamodel import (Event, Subject, Interpretation, Manifestation,
	TimeRange, StorageState, DataSource)

import testutils
from testutils import parse_events

class ZeitgeistRemoteAPITest(testutils.RemoteTestCase):
	
	def __init__(self, methodName):
		super(ZeitgeistRemoteAPITest, self).__init__(methodName)
	
	def testInsertAndGetEvent(self):
		ev = Event.new_for_values(timestamp=123,
					interpretation=Interpretation.ACCESS_EVENT,
					manifestation=Manifestation.USER_ACTIVITY,
					actor="Freak Mamma")
		subj = Subject.new_for_values(uri="void://foobar",
					interpretation=Interpretation.DOCUMENT,
					manifestation=Manifestation.FILE_DATA_OBJECT)
		ev.append_subject(subj)
		ids = self.insertEventsAndWait([ev])
		events = self.getEventsAndWait(ids)
		self.assertEquals(1, len(ids))
		self.assertEquals(1, len(events))
		
		ev = events[0]
		self.assertTrue(isinstance(ev, Event))
		self.assertEquals("123", ev.timestamp)
		self.assertEquals(Interpretation.ACCESS_EVENT, ev.interpretation)
		self.assertEquals(Manifestation.USER_ACTIVITY, ev.manifestation)
		self.assertEquals("Freak Mamma", ev.actor)
		self.assertEquals(1, len(ev.subjects))
		self.assertEquals("void://foobar", ev.subjects[0].uri)
		self.assertEquals(Interpretation.DOCUMENT, ev.subjects[0].interpretation)
		self.assertEquals(Manifestation.FILE_DATA_OBJECT, ev.subjects[0].manifestation)
	
	def testFindTwoOfThreeEvents(self):
		ev1 = Event.new_for_values(timestamp=400,
					interpretation=Interpretation.ACCESS_EVENT,
					manifestation=Manifestation.USER_ACTIVITY,
					actor="Boogaloo")	
		ev2 = Event.new_for_values(timestamp=500,
					interpretation=Interpretation.ACCESS_EVENT,
					manifestation=Manifestation.USER_ACTIVITY,
					actor="Boogaloo")
		ev3 = Event.new_for_values(timestamp=600,
					interpretation=Interpretation.SEND_EVENT,
					manifestation=Manifestation.USER_ACTIVITY,
					actor="Boogaloo")
		subj1 = Subject.new_for_values(uri="foo://bar",
					interpretation=Interpretation.DOCUMENT,
					manifestation=Manifestation.FILE_DATA_OBJECT)
		subj2 = Subject.new_for_values(uri="foo://baz",
					interpretation=Interpretation.IMAGE,
					manifestation=Manifestation.FILE_DATA_OBJECT)
		subj3 = Subject.new_for_values(uri="foo://quiz",
					interpretation=Interpretation.AUDIO,
					manifestation=Manifestation.FILE_DATA_OBJECT)
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
		ids = self.findEventIdsAndWait([], num_events=3)
		self.assertEquals(3, len(ids)) # (we can not trust the ids because we don't have a clean test environment)
		
		# Search for some specific templates
		subj_templ1 = Subject.new_for_values(manifestation=Manifestation.FILE_DATA_OBJECT)
		subj_templ2 = Subject.new_for_values(interpretation=Interpretation.IMAGE)
		event_template = Event.new_for_values(
					actor="Boogaloo",
					interpretation=Interpretation.ACCESS_EVENT,
					subjects=[subj_templ1,subj_templ2])
		ids = self.findEventIdsAndWait([event_template],
						num_events=10)
		self.assertEquals(1, len(ids))
		
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
	
	def testMonitorDeleteNonExistingEvent(self):
		result = []
		mainloop = gobject.MainLoop()
		events = parse_events("test/data/five_events.js")
		
		def timeout():
			# We want this timeout - we should not get informed
			# about deletions of non-existing events
			mainloop.quit()
			return False

		def notify_insert_handler(time_range, events):
			event_ids = map(lambda ev : ev.id, events)
			self.client.delete_events([9999999])
		
		def notify_delete_handler(time_range, event_ids):
			mainloop.quit()
			self.fail("Notified about deletion of non-existing events %s", events)
			
		self.client.install_monitor(TimeRange(125, 145), [],
			notify_insert_handler, notify_delete_handler)
		
		gobject.timeout_add_seconds(5, timeout)
		self.client.insert_events(events)
		mainloop.run()
	
	def testTwoMonitorsDeleteEvents(self):
		result1 = []
		result2 = []
		mainloop = gobject.MainLoop()
		events = parse_events("test/data/five_events.js")
		
		def timeout ():
			mainloop.quit()
			self.fail("Test case timed out")
			return False
		
		def check_ok():
			if len(result1) == 2 and len(result2) == 2:
				mainloop.quit()

		def notify_insert_handler1(time_range, events):
			event_ids = map(lambda ev : ev.id, events)
			self.client.delete_events(event_ids)
		
		def notify_delete_handler1(time_range, event_ids):
			result1.extend(event_ids)
			check_ok()
		
		def notify_delete_handler2(time_range, event_ids):
			result2.extend(event_ids)
			check_ok()
			
		self.client.install_monitor(TimeRange(125, 145), [],
			notify_insert_handler1, notify_delete_handler1)
		
		self.client.install_monitor(TimeRange(125, 145), [],
			lambda x, y: x, notify_delete_handler2)
		
		self.client.insert_events(events)
		gobject.timeout_add_seconds (5, timeout)
		mainloop.run()
		
		self.assertEquals(2, len(result1))
		self.assertEquals(2, len(result1))

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
		
	def testDeleteEvents(self):
		""" delete all events with actor == firefox """
		events = parse_events("test/data/five_events.js")
		self.insertEventsAndWait(events)
		
		event = Event()
		event.actor = "firefox"
		
		# get event ids with actor == firefox
		ff_ids = self.findEventIdsAndWait([event])
		# delete this events
		time_range = self.deleteEventsAndWait(ff_ids)
		# got timerange of deleted events
		self.assertEquals(2, len(time_range))
		# get all events, the one with actor == firefox should
		# not be there
		ids = self.findEventIdsAndWait([])
		self.assertEquals(2, len(ids))
		self.assertEquals(0, len(set(ff_ids) & set(ids)))
		
	def testFindByRandomActorAndGet(self):
		events = parse_events("test/data/five_events.js")
		self.insertEventsAndWait(events)
		
		template = Event.new_for_values(actor="/usr/bliblablu")
		
		ids = self.findEventIdsAndWait([template])
		self.assertEquals(len(ids), 0)
		
		events = self.getEventsAndWait(ids)
		self.assertEquals(len(events), 0)
	
	def testFindRelated(self):
		events = parse_events("test/data/apriori_events.js")
		self.insertEventsAndWait(events)
		
		uris = self.findRelatedAndWait(["i2"], num_events=2, result_type=1)
		self.assertEquals(uris, ["i3", "i1"])
		
		uris = self.findRelatedAndWait(["i2"], num_events=2, result_type=0)
		self.assertEquals(uris, ["i1", "i3"])
		
	def testFindEventsForValues(self):
		mainloop = gobject.MainLoop() # we don't have an *AndWait-helper method
									  # for the method we would like to test,
									  # this is why we need our own local loop
		events = parse_events("test/data/apriori_events.js")
		self.insertEventsAndWait(events)
		
		result = []
		def callback(events):
			result.extend(events)
			mainloop.quit()
		
		self.client.find_events_for_values(callback, actor="firefox", num_events=1)
		mainloop.run()
		self.assertEquals(len(result), 1)
		self.assertEquals(result[0].actor, "firefox")
		
	def testFindEventsWithStringPayload(self):
		mainloop = gobject.MainLoop()
		payload = "Hello World"
		def callback(ids):
			def callback2(events):
				mainloop.quit()
				self.assertEquals(events[0].payload, map(ord, payload))
			self.client.get_events(ids, callback2)
		events = [Event.new_for_values(actor=u"boo", timestamp=124, subject_uri="file://yomomma")]
		events[0].payload = payload
		self.client.insert_events(events, callback)
		mainloop.run()
		
	def testFindEventsWithNonASCIIPayload(self):
		mainloop = gobject.MainLoop()
		payload = u"äöü".encode("utf-8")
		def callback(ids):
			def callback2(events):
				mainloop.quit()
				self.assertEquals(events[0].payload, map(ord, payload))
			self.client.get_events(ids, callback2)
		events = [Event.new_for_values(actor=u"boo", timestamp=124, subject_uri="file://yomomma")]
		events[0].payload = payload
		self.client.insert_events(events, callback)
		mainloop.run()
		
	def testFindEventsWithBinaryPayload(self):
		mainloop = gobject.MainLoop()
		payload = pickle.dumps(1234)
		def callback(ids):
			def callback2(events):
				mainloop.quit()
				self.assertEquals(events[0].payload, map(ord, payload))
			self.client.get_events(ids, callback2)
		events = [Event.new_for_values(actor=u"boo", timestamp=124, subject_uri="file://yomomma")]
		events[0].payload = payload
		self.client.insert_events(events, callback)
		mainloop.run()
		
class ZeitgeistRemoteInterfaceTest(unittest.TestCase):
	
	def setUp(self):
		from _zeitgeist import engine
		from _zeitgeist.engine import sql, constants
		engine._engine = None
		sql.unset_cursor()
		self.saved_data = {
			"datapath": constants.DATA_PATH,
			"database": constants.DATABASE_FILE,
			"extensions": constants.USER_EXTENSION_PATH,
		}
		constants.DATA_PATH = tempfile.mkdtemp(prefix="zeitgeist.datapath.")
		constants.DATABASE_FILE = ":memory:"
		constants.USER_EXTENSION_PATH = os.path.join(constants.DATA_PATH, "extensions")
		
	def tearDown(self):
		from _zeitgeist.engine import constants
		shutil.rmtree(constants.DATA_PATH)
		constants.DATA_PATH = self.saved_data["datapath"]
		constants.DATABASE_FILE = self.saved_data["database"]
		constants.USER_EXTENSION_PATH = self.saved_data["extensions"]
	
	def testQuit(self):
		"""calling Quit() on the remote interface should shutdown the
		engine in a clean way"""
		from _zeitgeist.engine.remote import RemoteInterface
		interface = RemoteInterface()
		self.assertEquals(interface._engine.is_closed(), False)
		interface.Quit()
		self.assertEquals(interface._engine.is_closed(), True)


class ZeitgeistRemoteDataSourceRegistryTest(testutils.RemoteTestCase):
	
	_ds1 = [
		"www.example.com/foo",
		"Foo Source",
		"Awakes the foo in you",
		[
			Event.new_for_values(subject_manifestation = "!stfu:File"),
			Event.new_for_values(interpretation = "stfu:CreateEvent")
		],
	]

	_ds2 = [
		"www.example.org/bar",
		u"© mwhahaha çàéü",
		u"ThŊ§ ıs teĦ ün↓çØÐe¡",
		[]
	]

	_ds2b = [
		"www.example.org/bar", # same unique ID as _ds2
		u"This string has been translated into the ASCII language",
		u"Now the unicode is gone :(",
		[
			Event.new_for_values(subject_manifestation = "nah"),
		],
	]
	
	def __init__(self, methodName):
		super(ZeitgeistRemoteDataSourceRegistryTest, self).__init__(methodName)
	
	def _assertDataSourceEquals(self, dsdbus, dsref):
		self.assertEquals(dsdbus[DataSource.UniqueId], dsref[0])
		self.assertEquals(dsdbus[DataSource.Name], dsref[1])
		self.assertEquals(dsdbus[DataSource.Description], dsref[2])
		self.assertEquals(len(dsdbus[DataSource.EventTemplates]), len(dsref[3]))
		for i, template in enumerate(dsref[3]):
			tmpl = dsdbus[DataSource.EventTemplates][i]
			self.assertEquals(ZgEvent.get_plain(tmpl), ZgEvent.get_plain(template))
	
	def testPresence(self):
		""" Ensure that the DataSourceRegistry extension is there """
		iface = self.client._iface # we know that client._iface is as clean as possible
		registry = iface.get_extension("DataSourceRegistry", "data_source_registry")
		registry.GetDataSources()
	
	def testGetDataSourcesEmpty(self):
		self.assertEquals(self.client._registry.GetDataSources(), [])
	
	def testRegisterDataSource(self):
		self.client.register_data_source(*self._ds1)
		datasources = list(self.client._registry.GetDataSources())
		self.assertEquals(len(datasources), 1)
		self._assertDataSourceEquals(datasources[0], self._ds1)
	
	def testRegisterDataSourceUnicode(self):
		self.client.register_data_source(*self._ds2)
		datasources = list(self.client._registry.GetDataSources())
		self.assertEquals(len(datasources), 1)
		self._assertDataSourceEquals(datasources[0], self._ds2)
	
	def testRegisterDataSources(self):
		# Insert two data-sources
		self.client._registry.RegisterDataSource(*self._ds1)
		self.client._registry.RegisterDataSource(*self._ds2)
		
		# Verify that they have been inserted correctly
		datasources = list(self.client._registry.GetDataSources())
		self.assertEquals(len(datasources), 2)
		datasources.sort(key=lambda x: x[DataSource.UniqueId])
		self._assertDataSourceEquals(datasources[0], self._ds1)
		self._assertDataSourceEquals(datasources[1], self._ds2)
		
		# Change the information of the second data-source
		self.client._registry.RegisterDataSource(*self._ds2b)
		
		# Verify that it changed correctly
		datasources = list(self.client._registry.GetDataSources())
		self.assertEquals(len(datasources), 2)
		datasources.sort(key=lambda x: x[DataSource.UniqueId])
		self._assertDataSourceEquals(datasources[0], self._ds1)
		self._assertDataSourceEquals(datasources[1], self._ds2b)
	
	def testSetDataSourceEnabled(self):
		# Insert a data-source -- it should be enabled by default
		self.client._registry.RegisterDataSource(*self._ds1)
		ds = list(self.client._registry.GetDataSources())[0]
		self.assertEquals(ds[DataSource.Enabled], True)
		
		# Now we can choose to disable it...
		self.client._registry.SetDataSourceEnabled(self._ds1[0], False)
		ds = list(self.client._registry.GetDataSources())[0]
		self.assertEquals(ds[DataSource.Enabled], False)
		
		# And enable it again!
		self.client._registry.SetDataSourceEnabled(self._ds1[0], True)
		ds = list(self.client._registry.GetDataSources())[0]
		self.assertEquals(ds[DataSource.Enabled], True)
	
	def testDataSourceSignals(self):
		mainloop = gobject.MainLoop()
		global hit
		hit = 0
		
		def cb_registered(datasource):
			global hit
			self.assertEquals(hit, 0)
			hit = 1
		
		def cb_enabled(unique_id, enabled):
			global hit
			if hit == 1:
				self.assertEquals(enabled, False)
				hit = 2
			elif hit == 2:
				self.assertEquals(enabled, True)
				hit = 3
				# We're done -- change this if we figure out how to force a
				# disconnection from the bus, so we can also check the
				# DataSourceDisconnected signal.
				mainloop.quit()
			else:
				self.fail("Unexpected number of signals: %d." % hit)
		
		#def cb_disconnect(datasource):
		#	self.assertEquals(hit, 3)
		#	mainloop.quit()
		
		def cb_timeout():
			mainloop.quit()
			self.fail("Timed out -- operations not completed in 1 minute.")
		
		# Connect to signals
		self.client._registry.connect('DataSourceRegistered', cb_registered)
		self.client._registry.connect('DataSourceEnabled', cb_enabled)
		#self.client._registry.connect('DataSourceDisconnected', cb_disconnect)
		
		# Register data-source, disable it, enable it again
		gobject.idle_add(self.testSetDataSourceEnabled)
		
		# Add an arbitrary timeout so this test won't block if it fails
		gobject.timeout_add_seconds(30, cb_timeout)
		
		mainloop.run()


class ZeitgeistRemotePropertiesTest(testutils.RemoteTestCase):
	
	def __init__(self, methodName):
		super(ZeitgeistRemotePropertiesTest, self).__init__(methodName)
		
	def testExtensions(self):
		self.assertEquals(
			sorted(self.client.get_extensions()),
			["Blacklist", "DataSourceRegistry"]
		)
		self.assertEquals(
			sorted(self.client._iface.extensions()),
			["Blacklist", "DataSourceRegistry"]
		)


class ZeitgeistDaemonTest(unittest.TestCase):
	
	def setUp(self):
		self.env = os.environ.copy()
		self.datapath = tempfile.mkdtemp(prefix="zeitgeist.datapath.")
		self.env.update({
			"ZEITGEIST_DATABASE_PATH": ":memory:",
			"ZEITGEIST_DATA_PATH": self.datapath,
		})
		
	def tearDown(self):
		shutil.rmtree(self.datapath)
	
	def testSIGHUP(self):
		"""sending a SIGHUP signal to a running deamon instance results
		in a clean shutdown"""
		daemon = testutils.RemoteTestCase._safe_start_daemon(env=self.env)
		os.kill(daemon.pid, signal.SIGHUP)
		err = daemon.wait()
		self.assertEqual(err, 0)


if __name__ == "__main__":
	unittest.main()
