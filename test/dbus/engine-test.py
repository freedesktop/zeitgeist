#! /usr/bin/python
# -.- coding: utf-8 -.-

# remote-test.py
#
# Copyright © 2009-2011 Seif Lotfy <seif@lotfy.com>
# Copyright © 2009-2011 Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
# Copyright © 2009-2011 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
# Copyright © 2009-2011 Markus Korn <thekorn@gmx.de>
# Copyright © 2011 Collabora Ltd.
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
from dbus.exceptions import DBusException

from zeitgeist.datamodel import (Event, Subject, Interpretation, Manifestation,
	TimeRange, StorageState, DataSource, NULL_EVENT, ResultType)

import testutils
from testutils import parse_events, import_events

TEST_ACTOR = "/usr/share/applications/gnome-about.desktop"

# FIXME: move this to a .js file
test_event_1 = None
def create_test_event_1():
	ev = Event()
	ev.timestamp = 0
	ev.interpretation = Manifestation.USER_ACTIVITY
	ev.manifestation = Interpretation.CREATE_EVENT
	ev.actor = TEST_ACTOR
	subj = Subject()
	subj.uri = u"test://mytest"
	subj.manifestation = "lala"
	subj.interpretation = "tinky winky"
	subj.origin = "test://"
	subj.mimetype = "YOMAMA"
	subj.text = "SUCKS"
	subj.storage = "MyStorage"
	subj.current_uri = u"test://mytest"

	ev.append_subject(subj)
	return ev


class ZeitgeistEngineTest(testutils.RemoteTestCase):

	def testSingleInsertGet(self):
		test_event_1 = create_test_event_1()
		# Insert item and event
		ids = self.insertEventsAndWait([test_event_1])
		self.assertEquals(1, len(ids))
		
		result = self.getEventsAndWait(ids)
		resulting_event = result.pop()
		self.assertEquals(len(resulting_event), len(test_event_1))
		
		# fixing id, the initial event does not have any id set
		test_event_1[0][0] = ids[0]
		resulting_event[2] = ""
		
		self.assertEqual(resulting_event, test_event_1)
		
	def testInsertGetWithoutTimestamp(self):
		# We test two things, that Event creates a default timestamp
		# and that the engine provides one for us if don't do our selves
		
		subj = Subject.new_for_values(interpretation="foo://interp",
					manifestation="foo://manif",
					uri="nowhere")
		ev = Event.new_for_values(interpretation="foo://bar",
					manifestation="foo://quiz",
					actor="actor://myself",
					subjects=[subj])
		
		# Assert that timestamp is set
		self.assertTrue(ev.timestamp)
		
		# Clear the timestamp and insert event
		ev.timestamp = ""
		ids = self.insertEventsAndWait([ev])
		result = self.getEventsAndWait(ids)
		
		self.assertEquals(1, len(result))
		resulting_event = Event(result.pop())
		self.assertEquals("foo://bar", resulting_event.interpretation)
		self.assertTrue(resulting_event.timestamp) # We should have a timestamp again
		
	def testDuplicateEventInsertion(self):
		self.testSingleInsertGet()
		
		# Inserting the same event again should be ok, but not
		# cause duplicates
		self.testSingleInsertGet()
		
		# Find all events, and make sure that this is exactly one event
		result = self.findEventIdsAndWait([])
		self.assertEquals(1, len(result))
		self.assertEquals(1, result[0]) # The single event must have id 1
	
	def testDeleteSingle(self):
		self.testSingleInsertGet()
		self.deleteEventsAndWait([1])
		result = self.getEventsAndWait([1])
		self.assertEquals(0, len(filter(None, result)))

	def testIllegalPredefinedEventId(self):
		event = Event()
		event[0][0] = str(23) # This is illegal, we assert the error later
		event.timestamp = 0
		event.interpretation = Manifestation.USER_ACTIVITY
		event.manifestation = Interpretation.CREATE_EVENT
		event.actor = "/usr/share/applications/gnome-about.desktop"
		
		subject = Subject()
		subject.uri = "file:///tmp/file.txt"
		subject.manifestation = Manifestation.FILE_DATA_OBJECT
		subject.interpretation = Interpretation.DOCUMENT
		subject.origin = "test://"
		subject.mimetype = "text/plain"
		subject.text = "This subject has no text"
		subject.storage = "368c991f-8b59-4018-8130-3ce0ec944157" # UUID of home partition
		
		event.append_subject(subject)
		
		# Insert item and event
		ids = self.insertEventsAndWait([event,])
		self.assertEquals(len(ids), 1)
		# event is not inserted, id == 0 means error
		self.assertEquals(ids[0], 0)
		# check if really not events were inserted
		ids = self.findEventIdsAndWait([])
		self.assertEquals(len(ids), 0)
		
	def testGetNonExisting(self):
		events = self.getEventsAndWait([23,45,65])
		self.assertEquals(3, len(events))
		for ev in events : self.assertEquals(None, ev)
	
	def testGetDuplicateEventIds(self):
		ids = import_events("test/data/five_events.js", self)
		self.assertEquals(5, len(ids))
		
		events = self.getEventsAndWait([1, 1])
		self.assertEqual(2, len(events))
		self.assertEqual(2, len(filter(None, events))) #FIXME:FAILS HERE
		self.assertTrue(events[0].id == events[1].id == 1)
		
	def testFindEventsId(self):
		test_event_1 = create_test_event_1()
		self.testSingleInsertGet()
		result = self.findEventIdsAndWait([])
		self.assertEquals(1, len(result))
		test_event_1[0][0] = 1
		self.assertEqual(result[0], test_event_1.id)
		
	def testFindNothing(self):
		result = self.findEventIdsAndWait([])
		self.assertEquals(0, len(result))

	def testFindNothingBackwards(self):
		result = self.findEventIdsAndWait([], timerange=(1000000,1))
		self.assertEquals(0, len(result))
		
	def testFindFilteredByEventButNotSubject(self):
		# revision rainct@ubuntu.com-20091128164327-j8ez3fsifd1gygkr (1185)
		# Fix _build_templates so that it works when the Subject is empty.
		self.testSingleInsertGet()
		result = self.findEventIdsAndWait([Event.new_for_values(interpretation=Interpretation.LEAVE_EVENT)])
		self.assertEquals(0, len(result))

	def testFindFive(self):
		import_events("test/data/five_events.js", self)
		result = self.findEventIdsAndWait([])
		self.assertEquals(5, len(result))
		
	def testFindFiveWithStorageState(self):
		import_events("test/data/five_events.js", self)
		# The event's storage is unknown, so we get them back always.
		result = self.findEventIdsAndWait([], storage_state = 1)
		self.assertEquals(5, len(result))
		result = self.findEventIdsAndWait([], storage_state = 0)
		self.assertEquals(5, len(result))

	def testFindWithNonExistantActor(self):
		# Bug 496109: filtering by timerange and a non-existing actor gave an
		# incorrect result.
		import_events("test/data/twenty_events.js", self)
		# The event's storage is unknown, so we get them back always.
		result = self.findEventIdsAndWait([Event.new_for_values(actor="fake://foobar")])
		self.assertEquals(0, len(result))

	def testFindWithSubjectText(self):
		import_events("test/data/five_events.js", self)
		result = self.findEventIdsAndWait([Event.new_for_values(subject_text='this is not real')])
		self.assertEquals(0, len(result))
		result = self.findEventIdsAndWait([Event.new_for_values(subject_text='some text')])
		self.assertEquals(1, len(result))
		result = self.findEventIdsAndWait([Event.new_for_values(subject_text='this *')])
		self.assertEquals(0, len(result)) #We don't support wildcards for text
		result = self.findEventIdsAndWait([Event.new_for_values(subject_text='this item *')])
		self.assertEquals(1, len(result))

	def testSortFindByTimeAsc(self):
		import_events("test/data/twenty_events.js", self)
		result = self.findEventIdsAndWait([], num_events = 2, result_type = ResultType.LeastRecentEvents)
		event1 = self.getEventsAndWait([result[0]])[0]
		event2 = self.getEventsAndWait([result[1]])[0]
		self.assertEquals(True, event1.timestamp < event2.timestamp)
		
	def testSortFindByTimeDesc(self):
		import_events("test/data/twenty_events.js", self)
		result = self.findEventIdsAndWait([], num_events = 2, result_type = ResultType.MostRecentEvents)
		event1 = self.getEventsAndWait([result[0]])[0]
		event2 = self.getEventsAndWait([result[1]])[0]
		self.assertEquals(True, event1.timestamp > event2.timestamp)
	
	def testFindWithActor(self):
		test_event_1 = create_test_event_1()
		self.testSingleInsertGet()
		subj = Subject()
		event_template = Event.new_for_values(actor=TEST_ACTOR, subjects=[subj,])
		result = self.findEventIdsAndWait([event_template], num_events = 0, result_type = 1)
		self.assertEquals(1, len(result))
		test_event_1[0][0] = 1
		self.assertEqual(result[0], test_event_1.id)

	def testFindWithInterpretation(self):
		import_events("test/data/five_events.js", self)
		subj = Subject()
		event_template = Event.new_for_values(interpretation="stfu:OpenEvent", subjects=[subj])
		result = self.findEventIdsAndWait([event_template], num_events = 0, result_type = 1)
		self.assertEquals(2, len(result))
		events = self.getEventsAndWait(result)
		for event in events:
			self.assertEqual(event.interpretation, "stfu:OpenEvent")

	def testFindEventTwoInterpretations(self):
		import_events("test/data/twenty_events.js", self)
		result = self.findEventIdsAndWait([
			Event.new_for_values(interpretation="stfu:OpenEvent"),
			Event.new_for_values(interpretation="stfu:EvilEvent")],
			timerange = (102, 117), num_events = 0, result_type = 0)
		self.assertEquals(15, len(result))

	def testFindWithFakeInterpretation(self):
		import_events("test/data/twenty_events.js", self)
		result = self.findEventIdsAndWait([Event.new_for_values(interpretation="this-is-not-an-intrprettin")],
			num_events = 0, result_type = 0)
		self.assertEquals(0, len(result))

	def testFindWithManifestation(self):
		import_events("test/data/five_events.js", self)
		subj = Subject()
		event_template = Event.new_for_values(manifestation="stfu:EpicFailActivity", subjects=[subj])
		
		result = self.findEventIdsAndWait([event_template],
			num_events = 0, result_type = 1)
		self.assertEquals(1, len(result))
		events = self.getEventsAndWait(result)
		for event in events:
			self.assertEqual(event.manifestation, "stfu:EpicFailActivity")
			
	def testFindWithEventOrigin(self):
		import_events("test/data/twenty_events.js", self)
		event_template = Event.new_for_values(origin="origin3")
		result = self.findEventIdsAndWait([event_template], 
			num_events = 0, result_type = 1)
		events = self.getEventsAndWait(result)
		
		self.assertTrue(len(events) > 0)
		self.assertTrue(all(ev.origin == "origin3" for ev in events))
	
	def testFindWithEventOriginNegatedWildcard(self):
		import_events("test/data/twenty_events.js", self)
		event_template = Event.new_for_values(origin="!origin*")
		result = self.findEventIdsAndWait([event_template], 
			num_events = 0, result_type = 1)
		events = self.getEventsAndWait(result)
		
		self.assertTrue(len(events) > 0)
		self.assertFalse(any(ev.origin.startswith("origin") for ev in events))
	
	def testFindWithSubjectOrigin(self):
		import_events("test/data/five_events.js", self)
		subj = Subject.new_for_values(origin="file:///tmp")
		event_template = Event.new_for_values(subjects=[subj])
		result = self.findEventIdsAndWait([event_template], num_events = 0, result_type = 1)
		events = self.getEventsAndWait(result)
		for event in events:
			test = any(subj.origin == "file:///tmp" for subj in event.subjects)
			self.assertTrue(test)

	def testFindMultipleEvents(self):
		import_events("test/data/five_events.js", self)
		subj1 = Subject.new_for_values(uri="file:///home/foo.txt")
		event_template1 = Event.new_for_values(subjects=[subj1])
		subj2 = Subject.new_for_values(uri="file:///tmp/foo.txt")
		event_template2 = Event.new_for_values(subjects=[subj2])
		result = self.findEventIdsAndWait([event_template1, event_template2], num_events = 0, result_type = 4)
		self.assertEquals(2, len(result)) 
		events = self.getEventsAndWait(result)
		
	def testGetWithMultipleSubjects(self):
		subj1 = Subject.new_for_values(uri="file:///tmp/foo.txt")
		subj2 = Subject.new_for_values(uri="file:///tmp/loo.txt")
		event_template = Event.new_for_values(subjects=[subj1, subj2])
		result = self.insertEventsAndWait([event_template])
		events = self.getEventsAndWait(result)
		self.assertEquals(2, len(events[0].subjects))
		self.assertEquals("file:///tmp/foo.txt", events[0].subjects[0].uri)
		self.assertEquals("file:///tmp/loo.txt", events[0].subjects[1].uri)
	
	def testFindEventIdsWithMultipleSubjects(self):
		subj1 = Subject.new_for_values(uri="file:///tmp/foo.txt")
		subj2 = Subject.new_for_values(uri="file:///tmp/loo.txt")
		event = Event.new_for_values(subjects=[subj1, subj2])
		orig_ids = self.insertEventsAndWait([event])
		result_ids = self.findEventIdsAndWait([Event()], num_events = 0, result_type = 1)
		self.assertEquals(orig_ids, list(result_ids)) #FIXME: We need subjects of the same event to be merged
		
	def testFindEventsEventTemplate(self):
		import_events("test/data/five_events.js", self)
		subj = Subject.new_for_values(interpretation="stfu:Bee")
		subj1 = Subject.new_for_values(interpretation="stfu:Bar")
		event_template = Event.new_for_values(subjects=[subj, subj1])
		result = self.findEventIdsAndWait(
			[event_template, ],
			timerange = (0, 200),
			num_events = 100,
			result_type = 0)
		self.assertEquals(0, len(result)) # no subject with two different
										  # interpretations at the same time
		subj = Subject.new_for_values(uri="file:///tmp/foo.txt")
		subj1 = Subject.new_for_values(interpretation="stfu:Image")
		event_template = Event.new_for_values(subjects=[subj, subj1])
		result = self.findEventIdsAndWait(
			[event_template, ],
			timerange = (0, 200),
			num_events = 100,
			result_type = 0)
		self.assertEquals(1, len(result))
		
	def testJsonImport(self):
		import_events("test/data/single_event.js", self)
		results = self.getEventsAndWait([1])
		self.assertEquals(1, len(results))
		ev = results[0]
		self.assertEquals(1, ev.id)
		self.assertEquals("123", ev.timestamp)
		self.assertEquals("stfu:OpenEvent", ev.interpretation)
		self.assertEquals("stfu:UserActivity", ev.manifestation)
		self.assertEquals("firefox", ev.actor)
		self.assertEquals(1, len(ev.subjects))
		
		subj = ev.subjects[0]
		self.assertEquals("file:///tmp/foo.txt", subj.uri)
		self.assertEquals("stfu:Document", subj.interpretation)
		self.assertEquals("stfu:File", subj.manifestation)
		self.assertEquals("text/plain", subj.mimetype)
		self.assertEquals("this item has no text... rly!", subj.text)
		self.assertEquals("368c991f-8b59-4018-8130-3ce0ec944157", subj.storage)
		
	def testInsertSubjectOptionalAttributes(self):
		ev = Event.new_for_values(
			timestamp=123,
			interpretation=Interpretation.ACCESS_EVENT,
			manifestation=Manifestation.USER_ACTIVITY,
			actor="Freak Mamma"
		)
		subj = Subject.new_for_values(
			uri="void://foobar",
			interpretation=Interpretation.DOCUMENT,
			manifestation=Manifestation.FILE_DATA_OBJECT,
			)
		ev.append_subject(subj)
		
		ids = self.insertEventsAndWait([ev,])
		result = self.getEventsAndWait(ids)
		self.assertEquals(len(ids), len(result))
		
	def testEventWithoutSubject(self):
		ev = Event.new_for_values(timestamp=123,
					interpretation=Interpretation.ACCESS_EVENT,
					manifestation=Manifestation.USER_ACTIVITY,
					actor="Freak Mamma")
		ids = self.insertEventsAndWait([ev,])
		self.assertEquals(len(ids), 1)
		# event is not inserted, id == 0 means error
		self.assertEquals(ids[0], 0)
		# check if really not events were inserted
		ids = self.findEventIdsAndWait([ev],
			num_events = 0,
			result_type =  ResultType.MostRecentEvents)
		self.assertEquals(len(ids), 0)
		
	def testUnicodeEventInsert(self):
		# Insert and get a unicode event
		ids = import_events("test/data/unicode_event.js", self)
		self.assertEquals(len(ids), 1)
		result = self.getEventsAndWait(ids)
		self.assertEquals(1, len(result))
		event = result[0]
		self.assertEquals(1, len(event.subjects))
		self.assertEquals(u"hällö, I'm gürmen - åge drikker øl - ☠", event.subjects[0].text)
		self.assertEquals(u"http://live.gnome.org/☠", event.subjects[0].uri)
		
		# update the event we got from the DB's timestamp and insert
		# it again, we want to to test some ping-pong back and forth
		event[0][Event.Id] = ""  #FIXME: It used to be None but it did not work until i passed an empty string
		event.timestamp = str(243)
		ids = self.insertEventsAndWait([event])
		result = self.getEventsAndWait(ids)
		self.assertEquals(1, len(result))
		event = result[0]
		self.assertEquals(1, len(event.subjects))
		self.assertEquals(u"hällö, I'm gürmen - åge drikker øl - ☠", event.subjects[0].text)
		self.assertEquals(u"http://live.gnome.org/☠", event.subjects[0].uri)		
		
		# try and find a unicode event, we use unicode and not
		# inconsequently on deliberation
		subj = Subject.new_for_values(text="hällö, I'm gürmen - åge drikker øl - ☠",
					origin="file:///åges_øl í",
					uri=u"http://live.gnome.org/☠")
		event_template = Event.new_for_values(subjects=[subj,])
		
		
		result = self.findEventIdsAndWait([event_template],
			timerange = (0,200),
			num_events = 100,
			result_type = 0)
		self.assertEquals(len(result), 1)
		
	def testEventWithBinaryPayload(self):
		ev = Event()
		subject = Subject()
		ev.actor = "application:///firefox.desktop"
		ev.manifestation = Manifestation.USER_ACTIVITY
		ev.interpretation = Interpretation.ACCESS_EVENT
		subject.uri = "http://www.google.com"
		subject.interpretation = Interpretation #InterPretation.UNKNOWN
		subject.manifestation = Manifestation #Manifestation.WEB_HISTORY
		subject.text = ""
		subject.mimetype = "text/html"
		subject.origin = ""
		subject.storage = ""
		ev.subjects.append(subject)

		sampleString = """
		<Content name="Telepathy" class="Text">
		  <header>johnsmith@foo.bar</header>
		  <body>
		    John: Here is a talking point
		    You: Ok that looks fine
		  </body>
		  <launcher command="{application} johnsmith@foo.bar"/>
		</Content>"""
		
		ev.payload = sampleString.encode("UTF-8")
		ids = self.insertEventsAndWait([ev])
		_ev = self.getEventsAndWait(ids)[0]
		_ev.payload = "".join(map(str, _ev.payload)).decode('utf-8')
		self.assertEquals(ev.payload, _ev.payload)
		
		# Note: engine.insert_events() sets the id of the Event objects
		ev[0][0] = _ev.id
		self.assertEquals(ev.payload, _ev.payload)
		
	def testQueryByParent (self):
		ev = Event.new_for_values(subject_interpretation=Interpretation.AUDIO)
		_ids = self.insertEventsAndWait([ev])
		
		tmpl = Event.new_for_values(subject_interpretation=Interpretation.MEDIA)
		ids = self.findEventIdsAndWait([tmpl],
			num_events = 10, 
			result_type = ResultType.MostRecentEvents)
		
		self.assertEquals(1, len(ids))
		self.assertEquals(_ids, list(ids))
		
	def testNegation(self):
		import_events("test/data/five_events.js", self)

		template = Event.new_for_values(
			interpretation = "!stfu:OpenEvent"
		)
		ids = self.findEventIdsAndWait([template,],
			num_events = 10, 
			result_type = ResultType.MostRecentEvents
		)
		self.assertEquals(3, len(ids))
		
		template = Event.new_for_values(
			manifestation = "!stfu:YourActivity"
		)
		ids = self.findEventIdsAndWait([template,],
			num_events = 10, 
			result_type = ResultType.MostRecentEvents
		)
		self.assertEquals(4, len(ids))
		
		template = Event.new_for_values(
			actor = "!firefox"
		)
		ids = self.findEventIdsAndWait([template,],
			num_events = 10, 
			result_type = ResultType.MostRecentEvents
		)
		self.assertEquals(2, len(ids))
		
		template = Event.new_for_values(
			subject_uri = "!file:///tmp/foo.txt"
		)
		ids = self.findEventIdsAndWait([template,],
			num_events = 10, 
			result_type = ResultType.MostRecentEvents
		)
		self.assertEquals(3, len(ids))
		
		template = Event.new_for_values(
			subject_interpretation = "!stfu:Document"
		)
		ids = self.findEventIdsAndWait([template,],
			num_events = 10, 
			result_type = ResultType.MostRecentEvents
		)
		self.assertEquals(4, len(ids))
		
		template = Event.new_for_values(
			subject_manifestation = "!stfu:File"
		)
		ids = self.findEventIdsAndWait([template,],
			num_events = 10, 
			result_type = ResultType.MostRecentEvents
		)
		self.assertEquals(1, len(ids))
		
		template = Event.new_for_values(
			subject_origin = "!file:///tmp"
		)
		ids = self.findEventIdsAndWait([template,],
			num_events = 10, 
			result_type = ResultType.MostRecentEvents
		)
		self.assertEquals(1, len(ids))
		
		template = Event.new_for_values(
			subject_mimetype = "!text/plain"
		)
		ids = self.findEventIdsAndWait([template,],
			num_events = 10, 
			result_type = ResultType.MostRecentEvents
		)
		self.assertEquals(2, len(ids))
		
		# the next two fields do not support negation, '!' is treated as
		# content
		
		template = Event.new_for_values(
			subject_text = "!boo"
		)
		ids = self.findEventIdsAndWait([template,],
			num_events = 10, 
			result_type = ResultType.MostRecentEvents
		)
		self.assertEquals(0, len(ids))
		
		# searching by subject_storage is not working
		#~ template = Event.new_for_values(
			#~ subject_storage = "!boo"
		#~ )
		#~ ids = self.engine.find_eventids(TimeRange.always(),
			#~ [template,], StorageState.Any, 10, ResultType.MostRecentEvents
		#~ )
		#~ self.assertEquals(0, len(ids))
		
	def testNegationCombination(self):
		import_events("test/data/five_events.js", self)
		
		template = Event.new_for_values(
			interpretation = "!stfu:OpenEvent",
			actor = "!firefox"
		)
		ids = self.findEventIdsAndWait([template,],
			num_events = 10, 
			result_type = ResultType.MostRecentEvents
		)
		self.assertEquals(2, len(ids))
		
		template = Event.new_for_values(
			interpretation = "!stfu:OpenEvent",
			manifestation = "!stfu:YourActivity"
		)
		ids = self.findEventIdsAndWait([template,],
			num_events = 10, 
			result_type = ResultType.MostRecentEvents
		)
		self.assertEquals(3, len(ids))
		
	def testFindStorageNotExistant(self):
		events = [
			Event.new_for_values(timestamp=1000, subject_storage="sometext"),
			Event.new_for_values(timestamp=2000, subject_storage="anotherplace")
		]
		ids_in = self.insertEventsAndWait(events)
		template = Event.new_for_values(subject_storage="xxx")
		results = self.findEventIdsAndWait([template,],
			num_events = 10, 
			result_type = ResultType.MostRecentEvents
		)
		self.assertEquals(0, len(results))
				
	def testFindStorage(self):
		events = [
			Event.new_for_values(timestamp=1000, subject_storage="sometext"),
			Event.new_for_values(timestamp=2000, subject_storage="anotherplace")
		]
		ids_in = self.insertEventsAndWait(events)
		template = Event.new_for_values(subject_storage="sometext")
		results = self.findEventIdsAndWait([template,],
			num_events = 10, 
			result_type = ResultType.MostRecentEvents
		)
		self.assertEquals(1, len(results))
	
	def testWildcard(self):
		import_events("test/data/five_events.js", self)

		template = Event.new_for_values(
			actor = "ge*"
		)
		ids = self.findEventIdsAndWait([template,],
			num_events = 10, 
			result_type = ResultType.MostRecentEvents
		)
		self.assertEquals(2, len(ids))
		
		template = Event.new_for_values(
			actor = "!ge*"
		)
		ids = self.findEventIdsAndWait([template,],
			num_events = 10, 
			result_type = ResultType.MostRecentEvents
		)
		self.assertEquals(3, len(ids))
		
		template = Event.new_for_values(
			subject_mimetype = "text/*"
		)
		ids = self.findEventIdsAndWait([template,],
			num_events = 10, 
			result_type = ResultType.MostRecentEvents
		)
		self.assertEquals(3, len(ids))
		
		template = Event.new_for_values(
			subject_uri = "http://*"
		)
		ids = self.findEventIdsAndWait([template,],
			num_events = 10, 
			result_type = ResultType.MostRecentEvents
		)
		self.assertEquals(1, len(ids))

		template = Event.new_for_values(
			subject_current_uri = "http://*"
		)
		ids = self.findEventIdsAndWait([template,],
			num_events = 10, 
			result_type = ResultType.MostRecentEvents
		)
		self.assertEquals(1, len(ids))
		
		template = Event.new_for_values(
			subject_origin = "file://*"
		)
		ids = self.findEventIdsAndWait([template,],
			num_events = 10, 
			result_type = ResultType.MostRecentEvents
		)
		self.assertEquals(4, len(ids)) 

class ResultTypeTest(testutils.RemoteTestCase):
	
	def testResultTypesMostRecentEvents(self):
		import_events("test/data/five_events.js", self)
		
		# MostRecentEvents - new -> old			
		ids = self.findEventIdsAndWait([],
			num_events = 0, 
			result_type = ResultType.MostRecentEvents
		)
		events = self.getEventsAndWait(ids)
		sorted_event_ids = [
			event.id for event in sorted(events,
				cmp=lambda x, y: cmp(int(x.timestamp), int(y.timestamp)),
				reverse=True
			)
		]
		self.assertEquals(list(ids), sorted_event_ids)
		
	def testResultTypesLeastRecentEvents(self):
		import_events("test/data/five_events.js", self)
		
		# LeastRecentEvents - old -> new
		ids = self.findEventIdsAndWait([],
			num_events = 0, 
			result_type = ResultType.LeastRecentEvents)
		events = self.getEventsAndWait(ids)
		sorted_event_ids = [
			event.id for event in sorted(events,
				cmp=lambda x, y: cmp(int(x.timestamp), int(y.timestamp)))
		]
		self.assertEquals(list(ids), sorted_event_ids)
		
	def testResultTypesMostPopularActor(self):
		import_events("test/data/twenty_events.js", self)
		
		ids = self.findEventIdsAndWait([],
			num_events = 0, 
			result_type = ResultType.MostPopularActor)
		events = self.getEventsAndWait(ids)
		self.assertEquals([e[0][4] for e in events], ["firefox", "icedove",
			"frobnicator"])
		self.assertEquals([e.timestamp for e in events], ["119", "114", "105"])
		
	def testResultTypesMostPopularActor2(self):
		import_events("test/data/twenty_events.js", self)
		
		ids = self.findEventIdsAndWait([],
			timerange = (105,107),
			num_events = 0, 
			result_type = ResultType.MostPopularActor)
		events = self.getEventsAndWait(ids)
		self.assertEquals(len(events), 2)
		self.assertEquals([e[0][4] for e in events], ["firefox", "frobnicator"])
		self.assertEquals([e.timestamp for e in events], ["107", "105"])

	def testResultTypesLeastPopularActor(self):
		import_events("test/data/twenty_events.js", self)
		
		ids = self.findEventIdsAndWait([],
			num_events = 0, 
			result_type = ResultType.LeastPopularActor)
		events = self.getEventsAndWait(ids)
		
		self.assertEquals([e[0][4] for e in events], ["frobnicator", "icedove",
			"firefox"])
		self.assertEquals([e.timestamp for e in events], ["105", "114", "119"])
	
	def testResultTypesLeastPopularActor2(self):
		import_events("test/data/twenty_events.js", self)
		
		ids = self.findEventIdsAndWait([],
			timerange = (105,107),
			num_events = 0, 
			result_type = ResultType.LeastPopularActor)
		events = self.getEventsAndWait(ids)
		
		self.assertEquals(len(events), 2)
		self.assertEquals([e[0][4] for e in events], ["frobnicator", "firefox"])
		self.assertEquals([e.timestamp for e in events], ["105", "107"])
	
	def testResultTypesMostRecentSubject(self):
		import_events("test/data/five_events.js", self)
		
		ids = self.findEventIdsAndWait([],
			num_events = 0, 
			result_type = ResultType.MostRecentSubjects)
		events = self.getEventsAndWait(ids)
		
		self.assertEquals([e.timestamp for e in events],
			["163", "153", "143", "123"])
	
	def testResultTypesLeastRecentSubject(self):
		import_events("test/data/five_events.js", self)
		
		ids = self.findEventIdsAndWait([],
			num_events = 0, 
			result_type = ResultType.LeastRecentSubjects)
		events = self.getEventsAndWait(ids)
		self.assertEquals([e.timestamp for e in events],
			["123", "143", "153", "163"])
	
	def testResultTypesMostPopularSubject(self):
		import_events("test/data/five_events.js", self)
		
		ids = self.findEventIdsAndWait([],
			num_events = 0, 
			result_type = ResultType.MostPopularSubjects)
		events = self.getEventsAndWait(ids)
		self.assertEquals([e.timestamp for e in events],
			["143", "163", "153", "123"])
	
	def testResultTypesLeastPopularSubject(self):
		import_events("test/data/five_events.js", self)
		
		ids = self.findEventIdsAndWait([],
			num_events = 0, 
			result_type = ResultType.LeastPopularSubjects)
		events = self.getEventsAndWait(ids)
		
		self.assertEquals([e.timestamp for e in events],
			["123", "153", "163", "143"])
	
	def testResultTypesMostRecentCurrentUri(self):
		import_events("test/data/five_events.js", self)
		import_events("test/data/five_events_ext_move.js", self)
		
		ids = self.findEventIdsAndWait([],
			num_events = 0, 
			result_type = ResultType.MostRecentCurrentUri)
		events = self.getEventsAndWait(ids)
		
		self.assertEquals([e.timestamp for e in events],
			["200", "153", "123"])
		
	def testResultTypesLeastRecentCurrentUri(self):
		import_events("test/data/five_events.js", self)
		import_events("test/data/five_events_ext_move.js", self)
		
		ids = self.findEventIdsAndWait([],
			num_events = 0, 
			result_type = ResultType.LeastRecentCurrentUri)
		events = self.getEventsAndWait(ids)
		self.assertEquals([e.timestamp for e in events],
			["123", "153", "200"])

	def testResultTypesMostPopularCurrentUri(self):
		import_events("test/data/five_events.js", self)
		import_events("test/data/five_events_ext_move.js", self)
		
		ids = self.findEventIdsAndWait([],
			num_events = 0, 
			result_type = ResultType.MostPopularCurrentUri)
		events = self.getEventsAndWait(ids)
		self.assertEquals([e.timestamp for e in events],
			["200", "123", "153"]) 
	
	def testResultTypesLeastPopularCurrentUri(self):
		import_events("test/data/five_events.js", self)
		import_events("test/data/five_events_ext_move.js", self)
		
		ids = self.findEventIdsAndWait([],
			num_events = 0, 
			result_type = ResultType.LeastPopularCurrentUri)
		events = self.getEventsAndWait(ids)
		self.assertEquals([e.timestamp for e in events],
			["153", "123", "200"]) #Zeitgeist 0.8 does this test wrong.
				#This is the expected results

	def testResultTypesMostRecentActor(self):
		import_events("test/data/twenty_events.js", self)
		
		ids = self.findEventIdsAndWait([],
			num_events = 0, 
			result_type = ResultType.MostRecentActor)
		events = self.getEventsAndWait(ids)
		
		self.assertEquals([e.timestamp for e in events], ["119", "114", "105"])
	
	def testResultTypesMostRecentActor2(self):
		import_events("test/data/twenty_events.js", self)
		
		ids = self.findEventIdsAndWait([],
			timerange = (105, 107),
			num_events = 0, 
			result_type = ResultType.MostRecentActor)
		events = self.getEventsAndWait(ids)
		
		self.assertEquals([e.timestamp for e in events], ["107", "105"])
	
	def testResultTypesOldestActorBug641968(self):
		events = [
			Event.new_for_values(timestamp=1, actor="boo", subject_uri="tmp/boo"),
			Event.new_for_values(timestamp=2, actor="boo", subject_uri="home/boo"),
			Event.new_for_values(timestamp=3, actor="bar", subject_uri="tmp/boo"),
			Event.new_for_values(timestamp=4, actor="baz", subject_uri="tmp/boo"),
		]
		self.insertEventsAndWait(events)
		
		# Get the least recent actors
		ids = self.findEventIdsAndWait([],
			num_events = 0, 
			result_type = ResultType.OldestActor)
		events = self.getEventsAndWait(ids)
		self.assertEquals(list(ids), [1, 3, 4])
		
		# Get the least recent actors for "home/boo"
		template = Event.new_for_values(subject_uri="home/boo")
		ids = self.findEventIdsAndWait([template], 
			num_events = 0,
			result_type = ResultType.OldestActor)
		self.assertEquals(list(ids), [2])
		
		# Let's also try the same with MostRecentActor... Although there
		# should be no problem here.
		template = Event.new_for_values(subject_uri="home/boo")
		ids = self.findEventIdsAndWait([template], 
			num_events = 0, 
			result_type = ResultType.OldestActor)
		self.assertEquals(list(ids), [2])
	
	def testResultTypesOldestActor(self):
		import_events("test/data/twenty_events.js", self)
		
		ids = self.findEventIdsAndWait(
			[Event.new_for_values(subject_manifestation="stfu:File")],
			num_events = 0, 
			result_type = ResultType.OldestActor)
		events = self.getEventsAndWait(ids)
		self.assertEquals([e.timestamp for e in events], ["100", "101", "105"])

	def testResultTypesLeastRecentActor(self):
		import_events("test/data/twenty_events.js", self)
		
		ids = self.findEventIdsAndWait(
			[Event.new_for_values(subject_manifestation="stfu:File")],
			num_events = 0, 
			result_type = ResultType.LeastRecentActor)
		events = self.getEventsAndWait(ids)
		
		self.assertEquals([e.timestamp for e in events], ['105', '114', '119'])
	
	def testResultTypesLeastRecentActor2(self):
		# The same test as before, but this time with fewer events so that
		# it is actually understandable.
		events = [
			Event.new_for_values(timestamp=1, actor="gedit", subject_uri="oldFile"),
			Event.new_for_values(timestamp=2, actor="banshee", subject_uri="oldMusic"),
			Event.new_for_values(timestamp=3, actor="banshee", subject_uri="newMusic"),
			Event.new_for_values(timestamp=4, actor="gedit", subject_uri="newFile"),
		]
		self.insertEventsAndWait(events)
		
		ids = self.findEventIdsAndWait([],
			num_events = 0, 
			result_type = ResultType.LeastRecentActor)
		recv_events = self.getEventsAndWait(ids)
		self.assertEquals([e.timestamp for e in recv_events], ['3', '4'])
	
	def testResultTypesMostPopularEventOrigin(self):
		import_events("test/data/twenty_events.js", self)
		
		ids = self.findEventIdsAndWait([],
			num_events = 0, 
			result_type = ResultType.MostPopularEventOrigin)
		events = self.getEventsAndWait(ids)
			
		self.assertEquals([e[0][5] for e in events],
			["origin1", "origin3", "origin2"])
		self.assertEquals([e.timestamp for e in events], ["102", "103", "100"])

	def testResultTypesLeastPopularEventOrigin(self):
		import_events("test/data/twenty_events.js", self)
		
		ids = self.findEventIdsAndWait([],
			num_events = 0, 
			result_type = ResultType.LeastPopularEventOrigin)
		events = self.getEventsAndWait(ids)
		
		self.assertEquals([e[0][5] for e in events],
			["origin2", "origin3", "origin1"])
		self.assertEquals([e.timestamp for e in events], ["100", "103", "102"])

	def testResultTypesMostRecentEventOrigin(self):
		import_events("test/data/twenty_events.js", self)
		
		ids = self.findEventIdsAndWait([],
			num_events = 0, 
			result_type = ResultType.MostRecentEventOrigin)
		events = self.getEventsAndWait(ids)		
	
		self.assertEquals([e.timestamp for e in events], ["103", "102", "100"])
	
	def testResultTypesLeastRecentEventOrigin(self):
		import_events("test/data/twenty_events.js", self)
		
		ids = self.findEventIdsAndWait([],
			num_events = 0, 
			result_type = ResultType.LeastRecentEventOrigin)
		events = self.getEventsAndWait(ids)		
		
		self.assertEquals([e.timestamp for e in events], ["100", "102", "103"])

	def testResultTypesMostPopularSubjectOrigin(self):
		import_events("test/data/twenty_events.js", self)
		
		ids = self.findEventIdsAndWait([],
			num_events = 0, 
			result_type = ResultType.MostPopularOrigin)
		events = self.getEventsAndWait(ids)		
		
		self.assertEquals([e[1][0][3] for e in events], ["file:///tmp", "file:///home",
			"file:///etc"])
		self.assertEquals([e.timestamp for e in events], ["116", "118", "119"])

	def testResultTypesLeastPopularSubjectOrigin(self):
		import_events("test/data/twenty_events.js", self)
		
		ids = self.findEventIdsAndWait([],
			num_events = 0, 
			result_type = ResultType.LeastPopularOrigin)
		events = self.getEventsAndWait(ids)
		
		self.assertEquals([e[1][0][3] for e in events], ["file:///etc", "file:///home",
			"file:///tmp"])
		self.assertEquals([e.timestamp for e in events], ["119", "118", "116"])

	def testResultTypesMostRecentSubjectOrigin(self):
		import_events("test/data/twenty_events.js", self)
		
		ids = self.findEventIdsAndWait([],
			num_events = 0, 
			result_type = ResultType.MostRecentOrigin)
		events = self.getEventsAndWait(ids)
		
		self.assertEquals([e.timestamp for e in events], ["119", "118", "116"])

	def testResultTypesLeastRecentSubjectOrigin(self):
		import_events("test/data/twenty_events.js", self)
		
		ids = self.findEventIdsAndWait([],
			num_events = 0, 
			result_type = ResultType.LeastRecentOrigin)
		events = self.getEventsAndWait(ids)
		
		self.assertEquals([e.timestamp for e in events], ["116", "118", "119"])
		
	def testResultTypesMostRecentMimeType(self):
		import_events("test/data/twenty_events.js", self)
		
		ids = self.findEventIdsAndWait([],
			num_events = 0, 
			result_type = ResultType.MostRecentMimeType)
		events = self.getEventsAndWait(ids)
		
		self.assertEquals([e.timestamp for e in events], ['119', '114', '110', '107'])
		
	def testResultTypesLeastRecentMimeType(self):
		import_events("test/data/twenty_events.js", self)
		
		ids = self.findEventIdsAndWait([],
			num_events = 0, 
			result_type = ResultType.LeastRecentMimeType)
		events = self.getEventsAndWait(ids)
			
		self.assertEquals([e.timestamp for e in events], ['107', '110', '114', '119'])
		
	def testResultTypesMostPopularMimeType(self):
		import_events("test/data/twenty_events.js", self)
		
		ids = self.findEventIdsAndWait([],
			num_events = 0, 
			result_type = ResultType.MostPopularMimeType)
		events = self.getEventsAndWait(ids)
		
		self.assertEquals([e.timestamp for e in events], ['119', '110', '107', '114'])
		
	def testResultTypesLeastPopularMimeType(self):
		import_events("test/data/twenty_events.js", self)
		
		ids = self.findEventIdsAndWait([],
			num_events = 0, 
			result_type = ResultType.LeastPopularMimeType)
		events = self.getEventsAndWait(ids)
		
		self.assertEquals([e.timestamp for e in events], ['114', '107', '110', '119'])
	
	def testResultTypesMostRecentSubjectInterpretation(self):
		import_events("test/data/twenty_events.js", self)
		
		ids = self.findEventIdsAndWait([],
			num_events = 0, 
			result_type = ResultType.MostRecentSubjectInterpretation)
		events = self.getEventsAndWait(ids)
		
		self.assertEquals([e.timestamp for e in events], ['119', '118', '116', '106'])
		
	def testResultTypesLeastRecentSubjectInterpretation(self):
		import_events("test/data/twenty_events.js", self)
		
		ids = self.findEventIdsAndWait([],
			num_events = 0, 
			result_type = ResultType.LeastRecentSubjectInterpretation)
		events = self.getEventsAndWait(ids)
		
		self.assertEquals([e.timestamp for e in events], ['106', '116', '118', '119'])
		
	def testResultTypesMostPopularSubjectInterpretation(self):
		import_events("test/data/twenty_events.js", self)
		
		ids = self.findEventIdsAndWait([],
			num_events = 0, 
			result_type = ResultType.MostPopularSubjectInterpretation)
		events = self.getEventsAndWait(ids)
		
		self.assertEquals([e.timestamp for e in events], ['119', '116', '106', '118'])
		
	def testResultTypesLeastPopularSubjectInterpretation(self):
		import_events("test/data/twenty_events.js", self)
		
		ids = self.findEventIdsAndWait([],
			num_events = 0, 
			result_type = ResultType.LeastPopularSubjectInterpretation)
		events = self.getEventsAndWait(ids)
		
		self.assertEquals([e.timestamp for e in events], ['118', '106', '116', '119'])

if __name__ == "__main__":
	unittest.main()
