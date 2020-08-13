#! /usr/bin/env python3
# -.- coding: utf-8 -.-

# remote-test.py
#
# Copyright © 2009-2011 Seif Lotfy <seif@lotfy.com>
# Copyright © 2009-2011 Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
# Copyright © 2009-2011 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
# Copyright © 2009-2011 Markus Korn <thekorn@gmx.de>
# Copyright © 2011-2012 Collabora Ltd.
#             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
#             By Seif Lotfy <seif@lotfy.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 2.1 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import signal

from zeitgeist.datamodel import (Event, Subject, Interpretation, Manifestation,
	TimeRange, StorageState, DataSource, NULL_EVENT, ResultType)

import testutils
from dbus.exceptions import DBusException
from testutils import parse_events, import_events

class ZeitgeistRemoteAPITest(testutils.RemoteTestCase):

	def testInsertAndGetEvent(self):
		# Insert an event
		events = parse_events("test/data/single_event.js")
		ids = self.insertEventsAndWait(events)
		self.assertEqual(1, len(ids))

		# Now get it back and check it hasn't changed
		retrieved_events = self.getEventsAndWait(ids)
		self.assertEqual(1, len(retrieved_events))
		self.assertEventsEqual(retrieved_events[0], events[0])

	def testUnicodeInsert(self):
		events = parse_events("test/data/unicode_event.js")
		ids = self.insertEventsAndWait(events)
		self.assertEqual(len(ids), len(events))
		result_events = self.getEventsAndWait(ids)
		self.assertEqual(len(ids), len(result_events))

	def testGetEvents(self):
		events = parse_events("test/data/five_events.js")
		ids = self.insertEventsAndWait(events) + [1000, 2000]
		result = self.getEventsAndWait(ids)
		self.assertEqual(len([_f for _f in result if _f]), len(events))
		self.assertEqual(len([event for event in result if event is None]), 2)

	def testInsertAndDeleteEvent(self):
		# Insert an event
		events = parse_events("test/data/single_event.js")
		ids = self.insertEventsAndWait(events)

		# Delete it, make sure the returned time range is correct
		time_range = self.deleteEventsAndWait(ids)
		self.assertEqual(time_range[0], time_range[1])
		self.assertEqual(time_range[0], int(events[0].timestamp))

		# Make sure the event is gone
		retrieved_events = self.getEventsAndWait(ids)
		self.assertEqual(retrieved_events[0], None)

	def testDeleteNonExistantEvent(self):
		# Insert an event (populate the database so it isn't empty)
		events = parse_events("test/data/single_event.js")
		ids = self.insertEventsAndWait(events)

		# Try deleting a non-existant event
		events = parse_events("test/data/single_event.js")
		time_range = self.deleteEventsAndWait([int(ids[0]) + 1000])
		self.assertEqual(time_range[0], time_range[1])
		self.assertEqual(time_range[0], -1)

		# Make sure the inserted event is still there
		retrieved_events = self.getEventsAndWait(ids)
		self.assertEqual(1, len(retrieved_events))
		self.assertEventsEqual(retrieved_events[0], events[0])

	def testDeleteTwoSimilarEvents(self):
		# Insert a couple similar events
		event1 = parse_events("test/data/single_event.js")[0]
		event2 = Event(event1)
		event2.timestamp = int(event1.timestamp) + 1
		ids = self.insertEventsAndWait([event1, event2])

		# Try deleting one of them
		self.deleteEventsAndWait([ids[0]])

		# Make sure it's gone, but the second one is still there
		retrieved_events = self.getEventsAndWait(ids)
		self.assertEqual(retrieved_events[0], None)
		self.assertEventsEqual(retrieved_events[1], event2)

class ZeitgeistRemoteAPITestAdvanced(testutils.RemoteTestCase):

	def testFindTwoOfThreeEvents(self):
		events = parse_events("test/data/three_events.js")
		ids = self.insertEventsAndWait(events)
		self.assertEqual(3, len(ids))
		
		events = self.getEventsAndWait(ids)
		self.assertEqual(3, len(events))
		for event in events:
			self.assertTrue(isinstance(event, Event))
			self.assertEqual(Manifestation.USER_ACTIVITY, event.manifestation)
			self.assertTrue(event.actor.startswith("Boogaloo"))
		
		# Search for everything
		ids = self.findEventIdsAndWait([], num_events=3)
		self.assertEqual(3, len(ids))
		
		# Search for some specific templates
		subj_templ1 = Subject.new_for_values(manifestation=Manifestation.FILE_DATA_OBJECT)
		subj_templ2 = Subject.new_for_values(interpretation=Interpretation.IMAGE)
		event_template = Event.new_for_values(
					actor="Boogaloo*",
					interpretation=Interpretation.ACCESS_EVENT,
					subjects=[subj_templ1, subj_templ2])
		ids = self.findEventIdsAndWait([event_template],
						num_events=10)
		self.assertEqual(1, len(ids))

	def testFindOneOfThreeEvents(self):
		events = parse_events("test/data/three_events.js")
		ids = self.insertEventsAndWait(events)
		self.assertEqual(3, len(ids))
		
		events = self.getEventsAndWait(ids)
		self.assertEqual(3, len(events))
		for event in events:
			self.assertTrue(isinstance(event, Event))
			self.assertEqual(Manifestation.USER_ACTIVITY, event.manifestation)
			self.assertTrue(event.actor.startswith("Boogaloo"))
		
		# Search for everything
		ids = self.findEventIdsAndWait([], num_events=3)
		self.assertEqual(3, len(ids))
		
		# Search for some specific templates
		subj_templ1 = Subject.new_for_values(interpretation="!"+Interpretation.AUDIO)
		subj_templ2 = Subject.new_for_values(interpretation="!"+Interpretation.IMAGE)
		event_template = Event.new_for_values(
					actor="Boogaloo*",
					interpretation=Interpretation.ACCESS_EVENT,
					subjects=[subj_templ1, subj_templ2])
		ids = self.findEventIdsAndWait([event_template],
						num_events=10)
		self.assertEqual(1, len(ids))
		events = self.getEventsAndWait(ids)
		event = events[0]
		self.assertEqual(event.subjects[0].interpretation, Interpretation.DOCUMENT)

	def testFindEventsWithMultipleSubjects(self):
		events = parse_events("test/data/three_events.js")
		ids = self.insertEventsAndWait(events)

		results = self.findEventsForTemplatesAndWait([], num_events=5)
		self.assertEqual(3, len(results))

		self.assertEqual(len(results[2].get_subjects()), 2)
		self.assertEqual(len(results[1].get_subjects()), 1)
		self.assertEqual(len(results[0].get_subjects()), 1)

	def testFindEventsWithNoexpandOperator(self):
		events = parse_events("test/data/three_events.js")
		ids = self.insertEventsAndWait(events)

		template = Event.new_for_values(
			subject_interpretation=Interpretation.MEDIA)
		results = self.findEventsForTemplatesAndWait([template],
			num_events=5)
		self.assertEqual(3, len(results))

		template = Event.new_for_values(
			subject_interpretation='+%s' % Interpretation.MEDIA)
		results = self.findEventsForTemplatesAndWait([template],
			num_events=5)
		self.assertEqual(0, len(results))

		template = Event.new_for_values(
			subject_interpretation='+%s' % Interpretation.AUDIO)
		results = self.findEventsForTemplatesAndWait([template],
			num_events=5)
		self.assertEqual(1, len(results))
		self.assertEqual(results[0].get_subjects()[0].interpretation,
			Interpretation.AUDIO)

	def testFindEventsLimitWhenDuplicates(self):
		events = parse_events("test/data/three_events.js")
		ids = self.insertEventsAndWait(events)

		# This test makes sure that we get the requested number of events
		# when some of them have multiple subjects (so more than one row
		# with the same event id).
		results = self.findEventsForTemplatesAndWait([], num_events=3)
		self.assertEqual(3, len(results))

	def testInsertWithEmptySubjectInterpretationManifestation(self):
		events = parse_events("test/data/incomplete_events.js")
		ids = self.insertEventsAndWait(events[:3])
		self.assertEqual(3, len(ids))

		event = self.getEventsAndWait([ids[0]])[0]
		self.assertEqual("Hi", event.subjects[0].manifestation)
		self.assertEqual("", event.subjects[0].interpretation)
		self.assertEqual("Something", event.subjects[1].manifestation)
		self.assertEqual("", event.subjects[1].interpretation)

		event = self.getEventsAndWait([ids[1]])[0]
		self.assertEqual(Manifestation.FILE_DATA_OBJECT, event.subjects[0].manifestation)
		self.assertEqual(Interpretation.SOURCE_CODE, event.subjects[0].interpretation)
		self.assertEqual(Manifestation.FILE_DATA_OBJECT, event.subjects[1].manifestation)
		self.assertEqual("a", event.subjects[1].interpretation)
		self.assertEqual("b", event.subjects[2].manifestation)
		self.assertEqual(Interpretation.SOURCE_CODE, event.subjects[2].interpretation)
		
		event = self.getEventsAndWait([ids[2]])[0]
		self.assertEqual("something else", event.subjects[0].manifestation)
		self.assertEqual("#Audio", event.subjects[0].interpretation)

	def testInsertWithEmptySubjectMimeType(self):
		events = parse_events("test/data/incomplete_events.js")
		ids = self.insertEventsAndWait([events[7]])
		self.assertEqual(1, len(ids))
		
		event = self.getEventsAndWait([ids[0]])[0]
		self.assertEqual(1, len(event.subjects))

		subject = event.subjects[0]
		self.assertEqual("file:///unknown-mimetype-file", subject.uri)
		self.assertEqual("", subject.mimetype)
		self.assertEqual(Manifestation.FILE_DATA_OBJECT, subject.manifestation)  # FIXME
		self.assertEqual("", subject.interpretation) # FIXME

	def testInsertIncompleteEvent(self):
		events = parse_events("test/data/incomplete_events.js")

		# Missing interpretation
		ids = self.insertEventsAndWait([events[3]])
		self.assertEqual(0, len(ids))

		# Missing manifestation
		ids = self.insertEventsAndWait([events[4]])
		self.assertEqual(0, len(ids))

		# Missing actor
		ids = self.insertEventsAndWait([events[5]])
		self.assertEqual(0, len(ids))

	def testInsertIncompleteSubject(self):
		events = parse_events("test/data/incomplete_events.js")

		# Missing one subject URI
		ids = self.insertEventsAndWait([events[6]])
		self.assertEqual(0, len(ids))

class ZeitgeistRemoteFindEventIdsTest(testutils.RemoteTestCase):
	"""
	Test cases with basic tests for FindEventIds.
	
	Since they are all using the same test events and all tests contained
	here are read-only, I'd make sense to use something like setUpClass/
	tearDownClass to speed up test execution.
	"""

	def setUp(self):
		super(ZeitgeistRemoteFindEventIdsTest, self).setUp()
		
		# Insert some events...
		events = parse_events("test/data/five_events.js")
		self.ids = self.insertEventsAndWait(events)

	def testFindEventIds(self):
		# Retrieve all existing event IDs, make sure they are correct
		retrieved_ids = self.findEventIdsAndWait([])
		self.assertEqual(set(retrieved_ids), set(self.ids))

	def testFindEventIdsForId(self):
		# Retrieve events for a particular event ID 
		template = Event([["3", "", "", "", "", ""], [], ""])
		ids = self.findEventIdsAndWait([template])
		self.assertEqual(ids, [3])

	def testFindEventIdsForTimeRange(self):
		# Make sure that filtering by time range we get the right ones
		retrieved_ids = self.findEventIdsAndWait([],
			timerange=TimeRange(133, 153))
		self.assertEqual(retrieved_ids, [4, 2, 3]) # TS: [133, 143, 153]

		retrieved_ids = self.findEventIdsAndWait([],
			timerange=TimeRange(163, 163))
		self.assertEqual(retrieved_ids, [5]) # Timestamps: [163]

	def testFindEventIdsForInterpretation(self):
		# Retrieve events for a particular interpretation
		template = Event.new_for_values(interpretation='stfu:OpenEvent')
		ids = self.findEventIdsAndWait([template])
		self.assertEqual(ids, [5, 1])

		# Retrieve events excluding a particular interpretation
		template = Event.new_for_values(interpretation='!stfu:OpenEvent')
		ids = self.findEventIdsAndWait([template])
		self.assertEqual(list(map(int, ids)), [4, 2, 3])

	def testFindEventIdsForManifestation(self):
		# Retrieve events for a particular manifestation
		template = Event.new_for_values(manifestation='stfu:BooActivity')
		ids = self.findEventIdsAndWait([template])
		self.assertEqual(ids, [2])

		# Retrieve events excluding a particular manifestation
		template = Event.new_for_values(manifestation='!stfu:BooActivity')
		ids = self.findEventIdsAndWait([template])
		self.assertEqual(list(map(int, ids)), [5, 4, 3, 1])

	def testFindEventIdsForActor(self):
		# Retrieve events for a particular actor
		template = Event.new_for_values(actor='gedit')
		ids = self.findEventIdsAndWait([template])
		self.assertEqual(ids, [3])

		# Retrieve events excluding a particular actor
		template = Event.new_for_values(actor='!gedit')
		ids = self.findEventIdsAndWait([template])
		self.assertEqual(list(map(int, ids)), [5, 4, 2, 1])

		# Retrieve events with actor matching a prefix
		template = Event.new_for_values(actor='g*')
		ids = self.findEventIdsAndWait([template])
		self.assertEqual(list(map(int, ids)), [2, 3])

	def testFindEventIdsForEventOrigin(self):
		# Retrieve events for a particular actor
		template = Event.new_for_values(origin='big bang')
		ids = self.findEventIdsAndWait([template])
		self.assertEqual(ids, [5, 3])

		# Now let's try with wildcard and negation
		template = Event.new_for_values(origin='!big *')
		ids = self.findEventIdsAndWait([template])
		self.assertEqual(list(map(int, ids)), [4, 2, 1])

	def testFindEventIdsForSubjectInterpretation(self):
		# Retrieve events for a particular subject interpretation
		template = Event.new_for_values(subject_interpretation='stfu:Document')
		ids = self.findEventIdsAndWait([template])
		self.assertEqual(ids, [1])

		# Retrieve events excluding a particular subject interpretation
		template = Event.new_for_values(subject_interpretation='!stfu:Document')
		ids = self.findEventIdsAndWait([template])
		self.assertEqual(list(map(int, ids)), [5, 4, 2, 3])

	def testFindEventIdsForSubjectManifestation(self):
		# Retrieve events for a particular subject manifestation
		template = Event.new_for_values(subject_manifestation='stfu:File')
		ids = self.findEventIdsAndWait([template])
		self.assertEqual(ids, [5, 4, 3, 1])

		# Retrieve events excluding a particular subject interpretation
		template = Event.new_for_values(subject_manifestation='!stfu:File')
		ids = self.findEventIdsAndWait([template])
		self.assertEqual(list(map(int, ids)), [2])

	def testFindEventIdsForSubjectMimeType(self):
		# Retrieve events for a particular mime-type
		template = Event.new_for_values(subject_mimetype='text/plain')
		ids = self.findEventIdsAndWait([template])
		self.assertEqual(ids, [4, 2, 3])

		# Now let's try with wildcard and negation
		template = Event.new_for_values(subject_mimetype='!meat/*')
		ids = self.findEventIdsAndWait([template])
		self.assertEqual(list(map(int, ids)), [5, 4, 2, 3])

	def testFindEventIdsForSubjectUri(self):
		# Retrieve events for a particular URI
		template = Event.new_for_values(subject_uri='file:///tmp/foo.txt')
		ids = self.findEventIdsAndWait([template])
		self.assertEqual(ids, [2, 3])

		# Now let's try with wildcard...
		template = Event.new_for_values(subject_uri='http://*')
		ids = self.findEventIdsAndWait([template])
		self.assertEqual(list(map(int, ids)), [1])

		# ... and negation
		template = Event.new_for_values(subject_uri='!file:///tmp/foo.txt')
		ids = self.findEventIdsAndWait([template])
		self.assertEqual(list(map(int, ids)), [5, 4, 1])

	def testFindEventIdsForSubjectOrigin(self):
		# Retrieve events for a particular origin
		template = Event.new_for_values(subject_origin='file:///tmp')
		ids = self.findEventIdsAndWait([template])
		self.assertEqual(ids, [4, 2, 3])

		# Now let's try with wildcard and negation
		template = Event.new_for_values(subject_origin='!file:*')
		ids = self.findEventIdsAndWait([template])
		self.assertEqual(list(map(int, ids)), [5, 1])

	def testFindEventIdsForSubjectText(self):
		# Retrieve events with a particular text
		template = Event.new_for_values(subject_text='this item *')
		ids = self.findEventIdsAndWait([template])
		self.assertEqual(ids, [4])

	def testFindEventIdsForSubjectCurrentUri(self):
		# Retrieve events for a particular current URI
		template = Event.new_for_values(subject_current_uri='http://www.google.de')
		ids = self.findEventIdsAndWait([template])
		self.assertEqual(ids, [1])

		# Now let's try with wildcard and negation
		template = Event.new_for_values(subject_current_uri='!http:*')
		ids = self.findEventIdsAndWait([template])
		self.assertEqual(list(map(int, ids)), [5, 4, 2, 3])

	def testFindEventIdsForSubjectCurrentOrigin(self):
		# Retrieve events for a particular current origin
		template = Event.new_for_values(subject_current_origin='file:///tmp')
		ids = self.findEventIdsAndWait([template])
		self.assertEqual(ids, [4, 2, 3])

		# Now let's try with wildcard and negation
		template = Event.new_for_values(subject_current_origin='!file:*')
		ids = self.findEventIdsAndWait([template])
		self.assertEqual(list(map(int, ids)), [5, 1])

		# Now let's try with wildcard and negation
		template = Event.new_for_values(subject_current_origin='!http:*')
		ids = self.findEventIdsAndWait([template])
		self.assertEqual(list(map(int, ids)), [4, 2, 3])

	def testFindEventIdsForSubjectStorage(self):
		# Retrieve events for a particular subject storage
		template = Event.new_for_values(subject_storage=
			'368c991f-8b59-4018-8130-3ce0ec944157')
		ids = self.findEventIdsAndWait([template])
		self.assertEqual(ids, [4, 2, 3, 1])

	def testFindEventIdsWithStorageState(self):
		"""
		Test FindEventIds with different storage states.
		
		Although currently there isn't much point in this test, since
		all events have storage state set to NULL and so are always returned.
		"""
		
		# Retrieve events with storage state "any"
		ids = self.findEventIdsAndWait([], storage_state=StorageState.Any)
		self.assertEqual(ids, [5, 4, 2, 3, 1])
		
		# Retrieve events with storage state "available"
		ids = self.findEventIdsAndWait([], storage_state=StorageState.Available)
		self.assertEqual(ids, [5, 4, 2, 3, 1])
		
		# Retrieve events with storage state "not available"
		ids = self.findEventIdsAndWait([],
			storage_state=StorageState.NotAvailable)
		self.assertEqual(ids, [5, 4, 2, 3, 1])

	def testFindEventIdsWithUnknownStorageState(self):
		"""
		Events with storage state "unknown" should always be considered
		as being available.
		"""

		event = parse_events("test/data/single_event.js")[0]
		event.subjects[0].uri = 'file:///i-am-unknown'
		event.subjects[0].storage = 'unknown'

		self.insertEventsAndWait([event])

		tmpl = Event.new_for_values(subject_uri='file:///i-am-unknown')
		ids = self.findEventIdsAndWait([tmpl], storage_state=StorageState.Available)
		self.assertEqual(ids, [6])

class ZeitgeistRemoteInterfaceTest(testutils.RemoteTestCase):

	def testQuit(self):
		"""
		Calling Quit() on the remote interface should shutdown the
		engine in a clean way.
		"""
		try:
			self.client._iface.Quit()
		except DBusException as e:
			# expect a silent remote disconnection
			if e.get_dbus_name() != "org.freedesktop.DBus.Error.NoReply":
				raise (e)
		self.daemon.wait()
		self.assertRaises(OSError, self.kill_daemon)
		self.spawn_daemon()

	def testSIGHUP(self):
		"""
		Sending a SIGHUP signal to a running deamon instance should result
		in a clean shutdown.
		"""
		code = self.kill_daemon(signal.SIGHUP)
		self.assertEqual(code, 0)
		self.spawn_daemon()


class ZeitgeistRemotePropertiesTest(testutils.RemoteTestCase):

	def __init__(self, methodName):
		super(ZeitgeistRemotePropertiesTest, self).__init__(methodName)
	
	def testVersion(self):
		self.assertTrue(len(self.client.get_version()) >= 2)


if __name__ == "__main__":
	testutils.run()

# vim:noexpandtab:ts=4:sw=4
