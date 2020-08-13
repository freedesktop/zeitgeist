#! /usr/bin/env python3
# -.- coding: utf-8 -.-

# engine-test.py
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

from zeitgeist.datamodel import (Event, Subject, Interpretation, Manifestation,
	TimeRange, StorageState, DataSource, NULL_EVENT, ResultType)

import testutils
from testutils import parse_events, import_events, new_event

class ZeitgeistEngineTest(testutils.RemoteTestCase):

	def testSingleInsertGet(self):
		test_event_1 = parse_events("test/data/one_event.js")[0]
		# Insert item and event
		ids = self.insertEventsAndWait([test_event_1])
		self.assertEqual(1, len(ids))

		result = self.getEventsAndWait(ids)
		resulting_event = result.pop()
		self.assertEqual(len(resulting_event), len(test_event_1))

		# fixing id, the initial event does not have any id set
		test_event_1[0][0] = ids[0]
		resulting_event[2] = ""

		self.assertEqual(resulting_event, test_event_1)

	def testInsertGetWithoutTimestamp(self):
		# We test two things, that Event creates a default timestamp
		# and that the engine provides one for us if necessary

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

		self.assertEqual(1, len(result))
		resulting_event = Event(result.pop())
		self.assertEqual("foo://bar", resulting_event.interpretation)
		self.assertTrue(resulting_event.timestamp) # We should have a timestamp again

	def testDuplicateEventInsertion(self):
		self.testSingleInsertGet()

		# Inserting the same event again should be ok, but not
		# cause duplicates
		self.testSingleInsertGet()

		# Find all events, and make sure that this is exactly one event
		result = self.findEventIdsAndWait([])
		self.assertEqual(1, len(result))
		self.assertEqual(1, result[0]) # The single event must have id 1

	def testDeleteSingle(self):
		self.testSingleInsertGet()
		self.deleteEventsAndWait([1])
		result = self.getEventsAndWait([1])
		self.assertEqual(0, len([_f for _f in result if _f]))

	def testIllegalPredefinedEventId(self):
		event = parse_events("test/data/single_event.js")[0]
		event[0][Event.Id] = "23" # This is illegal, we assert the error later

		# Try inserting the event
		ids = self.insertEventsAndWait([event,])
		self.assertEqual(len(ids), 1)

		# Event is not inserted, id == 0 means error
		self.assertEqual(ids[0], 0)

		# Ensure that it really wasn't inserted
		ids = self.findEventIdsAndWait([])
		self.assertEqual(len(ids), 0)

	def testGetNonExisting(self):
		events = self.getEventsAndWait([23,45,65])
		self.assertEqual(3, len(events))
		for ev in events: self.assertEqual(None, ev)

	def testGetDuplicateEventIds(self):
		ids = import_events("test/data/five_events.js", self)
		self.assertEqual(5, len(ids))

		events = self.getEventsAndWait([1, 1])
		self.assertEqual(2, len(events))
		self.assertEqual(2, len([_f for _f in events if _f]))
		self.assertTrue(events[0].id == events[1].id == 1)

	def testFindEventsId(self):
		test_event_1 = parse_events("test/data/one_event.js")[0]
		self.testSingleInsertGet()
		result = self.findEventIdsAndWait([])
		self.assertEqual(1, len(result))
		test_event_1[0][0] = 1
		self.assertEqual(result[0], test_event_1.id)

	def testFindNothing(self):
		result = self.findEventIdsAndWait([])
		self.assertEqual(0, len(result))

	def testFindNothingBackwards(self):
		result = self.findEventIdsAndWait([], timerange=(1000000,1))
		self.assertEqual(0, len(result))

	def testFindFilteredByEventButNotSubject(self):
		# revision rainct@ubuntu.com-20091128164327-j8ez3fsifd1gygkr (1185)
		# Fix _build_templates so that it works when the Subject is empty.
		self.testSingleInsertGet()
		result = self.findEventIdsAndWait([Event.new_for_values(
			interpretation=Interpretation.LEAVE_EVENT)])
		self.assertEqual(0, len(result))

	def testFindFive(self):
		import_events("test/data/five_events.js", self)
		result = self.findEventIdsAndWait([])
		self.assertEqual(5, len(result))

	def testFindFiveWithStorageState(self):
		import_events("test/data/five_events.js", self)
		# The event's storage is unknown, so we get them back always.
		result = self.findEventIdsAndWait([], storage_state=1)
		self.assertEqual(5, len(result))
		result = self.findEventIdsAndWait([], storage_state=0)
		self.assertEqual(5, len(result))

	def testFindWithNonExistantActor(self):
		# Bug 496109: filtering by timerange and a non-existing actor gave an
		# incorrect result.
		import_events("test/data/twenty_events.js", self)
		result = self.findEventIdsAndWait([Event.new_for_values(actor="fake://foobar")])
		self.assertEqual(0, len(result))

	def testFindWithSubjectText(self):
		import_events("test/data/five_events.js", self)
		result = self.findEventIdsAndWait([Event.new_for_values(subject_text='this is not real')])
		self.assertEqual(0, len(result))
		result = self.findEventIdsAndWait([Event.new_for_values(subject_text='some text')])
		self.assertEqual(1, len(result))
		result = self.findEventIdsAndWait([Event.new_for_values(subject_text='this *')])
		self.assertEqual(0, len(result)) # We don't support wildcards for text
		result = self.findEventIdsAndWait([Event.new_for_values(subject_text='this item *')])
		self.assertEqual(1, len(result))

	def testSortFindByTimeAsc(self):
		import_events("test/data/twenty_events.js", self)
		result = self.findEventIdsAndWait([], num_events=2,
			result_type=ResultType.LeastRecentEvents)
		event1 = self.getEventsAndWait([result[0]])[0]
		event2 = self.getEventsAndWait([result[1]])[0]
		self.assertEqual(True, event1.timestamp < event2.timestamp)

	def testSortFindByTimeDesc(self):
		import_events("test/data/twenty_events.js", self)
		result = self.findEventIdsAndWait([], num_events=2,
			result_type=ResultType.MostRecentEvents)
		event1 = self.getEventsAndWait([result[0]])[0]
		event2 = self.getEventsAndWait([result[1]])[0]
		self.assertEqual(True, event1.timestamp > event2.timestamp)

	def testFindWithActor(self):
		test_event_1 = parse_events("test/data/one_event.js")[0]
		self.testSingleInsertGet()
		subj = Subject()
		event_template = Event.new_for_values(
			actor="application://gnome-about.desktop",
			subjects=[subj,])
		result = self.findEventIdsAndWait([event_template], num_events=0, result_type=1)
		self.assertEqual(1, len(result))
		test_event_1[0][0] = 1
		self.assertEqual(result[0], test_event_1.id)

	def testFindWithInterpretation(self):
		import_events("test/data/five_events.js", self)
		subj = Subject()
		event_template = Event.new_for_values(interpretation="stfu:OpenEvent", subjects=[subj])
		result = self.findEventIdsAndWait([event_template], num_events=0, result_type=1)
		self.assertEqual(2, len(result))
		events = self.getEventsAndWait(result)
		for event in events:
			self.assertEqual(event.interpretation, "stfu:OpenEvent")

	def testFindEventTwoInterpretations(self):
		import_events("test/data/twenty_events.js", self)
		result = self.findEventIdsAndWait([
			Event.new_for_values(interpretation="stfu:OpenEvent"),
			Event.new_for_values(interpretation="stfu:EvilEvent")],
			timerange = (102, 117), num_events=0, result_type=0)
		self.assertEqual(15, len(result))

	def testFindWithFakeInterpretation(self):
		import_events("test/data/twenty_events.js", self)
		result = self.findEventIdsAndWait([Event.new_for_values(
			interpretation="this-is-not-an-interpretation")])
		self.assertEqual(0, len(result))

	def testFindWithManifestation(self):
		import_events("test/data/five_events.js", self)
		subj = Subject()
		event_template = Event.new_for_values(manifestation="stfu:EpicFailActivity", subjects=[subj])

		result = self.findEventIdsAndWait([event_template],
			num_events=0, result_type=1)
		self.assertEqual(1, len(result))
		events = self.getEventsAndWait(result)
		for event in events:
			self.assertEqual(event.manifestation, "stfu:EpicFailActivity")

	def testFindWithEventOrigin(self):
		import_events("test/data/twenty_events.js", self)
		event_template = Event.new_for_values(origin="origin3")
		result = self.findEventIdsAndWait([event_template],
			num_events=0, result_type=1)
		events = self.getEventsAndWait(result)

		self.assertTrue(len(events) > 0)
		self.assertTrue(all(ev.origin == "origin3" for ev in events))

	def testFindWithEventOriginNegatedWildcard(self):
		import_events("test/data/twenty_events.js", self)
		event_template = Event.new_for_values(origin="!origin*")
		result = self.findEventIdsAndWait([event_template],
			num_events=0, result_type=1)
		events = self.getEventsAndWait(result)

		self.assertTrue(len(events) > 0)
		self.assertFalse(any(ev.origin.startswith("origin") for ev in events))

	def testFindWithSubjectOrigin(self):
		import_events("test/data/five_events.js", self)
		subj = Subject.new_for_values(origin="file:///tmp")
		event_template = Event.new_for_values(subjects=[subj])
		result = self.findEventIdsAndWait([event_template], num_events=0, result_type=1)
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
		result = self.findEventIdsAndWait([event_template1, event_template2], num_events=0, result_type=4)
		self.assertEqual(2, len(result))
		events = self.getEventsAndWait(result)

	def testGetWithMultipleSubjects(self):
		subj1 = Subject.new_for_values(uri="file:///tmp/foo.txt")
		subj2 = Subject.new_for_values(uri="file:///tmp/loo.txt")
		event = new_event(subjects=[subj1, subj2])
		result = self.insertEventsAndWait([event])
		events = self.getEventsAndWait(result)
		self.assertEqual(2, len(events[0].subjects))
		self.assertEqual("file:///tmp/foo.txt", events[0].subjects[0].uri)
		self.assertEqual("file:///tmp/loo.txt", events[0].subjects[1].uri)

	def testFindEventIdsWithMultipleSubjects(self):
		subj1 = Subject.new_for_values(uri="file:///tmp/foo.txt")
		subj2 = Subject.new_for_values(uri="file:///tmp/loo.txt")
		event = new_event(subjects=[subj1, subj2])
		orig_ids = self.insertEventsAndWait([event])
		result_ids = self.findEventIdsAndWait([Event()], num_events=0,
			result_type=ResultType.LeastRecentEvents)
		self.assertEqual(orig_ids, list(result_ids))

	def testFindEventsEventTemplate(self):
		import_events("test/data/five_events.js", self)
		subj = Subject.new_for_values(interpretation="stfu:Bee")
		subj1 = Subject.new_for_values(interpretation="stfu:Bar")
		event_template = Event.new_for_values(subjects=[subj, subj1])
		result = self.findEventIdsAndWait(
			[event_template, ],
			timerange = (0, 200),
			num_events=100,
			result_type=0)
		self.assertEqual(0, len(result)) # no subject with two different
										  # interpretations at the same time
		subj = Subject.new_for_values(uri="file:///tmp/foo.txt")
		subj1 = Subject.new_for_values(interpretation="stfu:Image")
		event_template = Event.new_for_values(subjects=[subj, subj1])
		result = self.findEventIdsAndWait(
			[event_template, ],
			timerange = (0, 200),
			num_events=100,
			result_type=0)
		self.assertEqual(1, len(result))

	def testJsonImport(self):
		import_events("test/data/single_event.js", self)
		results = self.getEventsAndWait([1])
		self.assertEqual(1, len(results))
		ev = results[0]
		self.assertEqual(1, ev.id)
		self.assertEqual("123", ev.timestamp)
		self.assertEqual("stfu:OpenEvent", ev.interpretation)
		self.assertEqual("stfu:UserActivity", ev.manifestation)
		self.assertEqual("firefox", ev.actor)
		self.assertEqual(1, len(ev.subjects))

		subj = ev.subjects[0]
		self.assertEqual("file:///tmp/foo.txt", subj.uri)
		self.assertEqual("stfu:Document", subj.interpretation)
		self.assertEqual("stfu:File", subj.manifestation)
		self.assertEqual("text/plain", subj.mimetype)
		self.assertEqual("this item has no text... rly!", subj.text)
		self.assertEqual("368c991f-8b59-4018-8130-3ce0ec944157", subj.storage)

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
		self.assertEqual(len(ids), len(result))

	def testEventWithoutSubject(self):
		ev = Event.new_for_values(timestamp=123,
					interpretation=Interpretation.ACCESS_EVENT,
					manifestation=Manifestation.USER_ACTIVITY,
					actor="Freak Mamma")
		ids = self.insertEventsAndWait([ev,])
		self.assertEqual(len(ids), 1)
		# event is not inserted, id == 0 means error
		self.assertEqual(ids[0], 0)
		# check if really not events were inserted
		ids = self.findEventIdsAndWait([ev],
			num_events=0,
			result_type= ResultType.MostRecentEvents)
		self.assertEqual(len(ids), 0)

	def testUnicodeEventInsert(self):
		# Insert and get a unicode event
		ids = import_events("test/data/unicode_event.js", self)
		self.assertEqual(len(ids), 1)
		result = self.getEventsAndWait(ids)
		self.assertEqual(1, len(result))
		event = result[0]
		self.assertEqual(1, len(event.subjects))
		self.assertEqual("hällö, I'm gürmen - åge drikker øl - ☠", event.subjects[0].text)
		self.assertEqual("http://live.gnome.org/☠", event.subjects[0].uri)

		# Update the event we got from the DB's timestamp and insert
		# it again, we want to to test some ping-pong back and forth
		event[0][Event.Id] = ""
		event.timestamp = "243"
		ids = self.insertEventsAndWait([event])
		result = self.getEventsAndWait(ids)
		self.assertEqual(1, len(result))
		event = result[0]
		self.assertEqual(1, len(event.subjects))
		self.assertEqual("hällö, I'm gürmen - åge drikker øl - ☠", event.subjects[0].text)
		self.assertEqual("http://live.gnome.org/☠", event.subjects[0].uri)

		# Try and find a unicode event
		subj = Subject.new_for_values(text="hällö, I'm gürmen - åge drikker øl - ☠",
			origin="file:///åges_øl í", uri="http://live.gnome.org/☠")
		event_template = Event.new_for_values(subjects=[subj,])

		result = self.findEventIdsAndWait([event_template],
			timerange=(0,200), num_events=100, result_type=0)
		self.assertEqual(len(result), 1)

	def testEventWithBinaryPayload(self):
		event = parse_events("test/data/single_event.js")[0]

		sampleString = """
		<Content name="Telepathy" class="Text">
		  <header>johnsmith@foo.bar</header>
		  <body>
		    John: 你好 Here is a talking point
		    You: Ok that looks fine
		  </body>
		  <launcher command="{application} johnsmith@foo.bar"/>
		</Content>"""
		event.payload = sampleString.encode("utf-8")

		ids = self.insertEventsAndWait([event])
		result = self.getEventsAndWait(ids)[0]

		# verify all '248' bytes
		self.assertEqual(len(event.payload), len(result.payload))
		for i in list(range(len(event.payload))):
			self.assertEqual(event.payload[i], result.payload[i])

	def testQueryByParent(self):
		ev = new_event(subject_interpretation=Interpretation.AUDIO)
		_ids = self.insertEventsAndWait([ev])

		tmpl = Event.new_for_values(subject_interpretation=Interpretation.MEDIA)
		ids = self.findEventIdsAndWait([tmpl],
			num_events=10,
			result_type=ResultType.MostRecentEvents)

		self.assertEqual(1, len(ids))
		self.assertEqual(_ids, list(ids))

	def testNegation(self):
		import_events("test/data/five_events.js", self)

		template = Event.new_for_values(
			interpretation = "!stfu:OpenEvent"
		)
		ids = self.findEventIdsAndWait([template,],
			num_events=10,
			result_type=ResultType.MostRecentEvents
		)
		self.assertEqual(3, len(ids))
		
		template = Event.new_for_values(
			manifestation = "!stfu:YourActivity"
		)
		ids = self.findEventIdsAndWait([template,],
			num_events=10,
			result_type=ResultType.MostRecentEvents
		)
		self.assertEqual(4, len(ids))
		
		template = Event.new_for_values(
			actor = "!firefox"
		)
		ids = self.findEventIdsAndWait([template,],
			num_events=10,
			result_type=ResultType.MostRecentEvents
		)
		self.assertEqual(2, len(ids))

		template = Event.new_for_values(
			subject_uri = "!file:///tmp/foo.txt"
		)
		ids = self.findEventIdsAndWait([template,],
			num_events=10,
			result_type=ResultType.MostRecentEvents
		)
		self.assertEqual(3, len(ids))

		template = Event.new_for_values(
			subject_interpretation = "!stfu:Document"
		)
		ids = self.findEventIdsAndWait([template,],
			num_events=10,
			result_type=ResultType.MostRecentEvents
		)
		self.assertEqual(4, len(ids))

		template = Event.new_for_values(
			subject_manifestation = "!stfu:File"
		)
		ids = self.findEventIdsAndWait([template,],
			num_events=10,
			result_type=ResultType.MostRecentEvents
		)
		self.assertEqual(1, len(ids))

		template = Event.new_for_values(
			subject_origin = "!file:///tmp"
		)
		ids = self.findEventIdsAndWait([template,],
			num_events=10,
			result_type=ResultType.MostRecentEvents
		)
		self.assertEqual(2, len(ids))

		template = Event.new_for_values(
			subject_mimetype = "!text/plain"
		)
		ids = self.findEventIdsAndWait([template,],
			num_events=10,
			result_type=ResultType.MostRecentEvents
		)
		self.assertEqual(2, len(ids))

		# the next two fields do not support negation, '!' is treated as
		# content

		template = Event.new_for_values(
			subject_text = "!boo"
		)
		ids = self.findEventIdsAndWait([template,],
			num_events=10,
			result_type=ResultType.MostRecentEvents
		)
		self.assertEqual(0, len(ids))

	def testNegationCombination(self):
		import_events("test/data/five_events.js", self)

		template = Event.new_for_values(
			interpretation = "!stfu:OpenEvent",
			actor = "!firefox"
		)
		ids = self.findEventIdsAndWait([template,],
			num_events=10,
			result_type=ResultType.MostRecentEvents
		)
		self.assertEqual(2, len(ids))

		template = Event.new_for_values(
			interpretation = "!stfu:OpenEvent",
			manifestation = "!stfu:YourActivity"
		)
		ids = self.findEventIdsAndWait([template,],
			num_events=10,
			result_type=ResultType.MostRecentEvents
		)
		self.assertEqual(3, len(ids))

	def testFindStorageNotExistant(self):
		events = [
			new_event(timestamp=1000, subject_storage="sometext"),
			new_event(timestamp=2000, subject_storage="anotherplace")
		]
		ids_in = self.insertEventsAndWait(events)
		template = Event.new_for_values(subject_storage="xxx")
		results = self.findEventIdsAndWait([template,],
			num_events=10,
			result_type=ResultType.MostRecentEvents
		)
		self.assertEqual(0, len(results))

	def testFindStorage(self):
		events = [
			new_event(timestamp=1000, subject_storage="sometext"),
			new_event(timestamp=2000, subject_storage="anotherplace")
		]
		ids_in = self.insertEventsAndWait(events)
		template = Event.new_for_values(subject_storage="sometext")
		results = self.findEventIdsAndWait([template,],
			num_events=10,
			result_type=ResultType.MostRecentEvents
		)
		self.assertEqual(1, len(results))

	def testMoving(self):
		import_events("test/data/five_events.js", self)
		import_events("test/data/five_events_ext_move.js", self)
		template = Event.new_for_values(subject_current_uri='file:///*')

		ids = self.findEventIdsAndWait([template],
			num_events = 0,
			result_type = ResultType.MostRecentCurrentUri)
		self.assertEqual(2, len(ids))

		ids = self.findEventIdsAndWait([template],
			num_events = 0,
			result_type = ResultType.MostRecentCurrentUri)
		self.assertEqual(2, len(ids))

		ids = self.findEventIdsAndWait([template],
			num_events = 0,
			result_type = ResultType.MostRecentEvents)
		self.assertEqual(5, len(ids))

		template = Event.new_for_values(subject_current_origin='file:///*')
		ids = self.findEventIdsAndWait([template],
			num_events = 0,
			result_type = ResultType.MostRecentEvents)
		self.assertEqual(4, len(ids))

	def testWildcard(self):
		import_events("test/data/five_events.js", self)

		template = Event.new_for_values(
			actor = "ge*"
		)
		ids = self.findEventIdsAndWait([template,],
			num_events=10,
			result_type=ResultType.MostRecentEvents
		)
		self.assertEqual(2, len(ids))

		template = Event.new_for_values(
			actor = "!ge*"
		)
		ids = self.findEventIdsAndWait([template,],
			num_events=10,
			result_type=ResultType.MostRecentEvents
		)
		self.assertEqual(3, len(ids))

		template = Event.new_for_values(
			subject_mimetype = "text/*"
		)
		ids = self.findEventIdsAndWait([template,],
			num_events=10,
			result_type=ResultType.MostRecentEvents
		)
		self.assertEqual(3, len(ids))

		template = Event.new_for_values(
			subject_uri = "http://*"
		)
		ids = self.findEventIdsAndWait([template,],
			num_events=10,
			result_type=ResultType.MostRecentEvents
		)
		self.assertEqual(1, len(ids))

		template = Event.new_for_values(
			subject_current_uri = "http://*"
		)
		ids = self.findEventIdsAndWait([template,],
			num_events=10,
			result_type=ResultType.MostRecentEvents
		)
		self.assertEqual(1, len(ids))

		template = Event.new_for_values(
			subject_origin = "file://*"
		)
		ids = self.findEventIdsAndWait([template,],
			num_events=10,
			result_type=ResultType.MostRecentEvents
		)
		self.assertEqual(3, len(ids))

if __name__ == "__main__":
	testutils.run()

# vim:noexpandtab:ts=4:sw=4
