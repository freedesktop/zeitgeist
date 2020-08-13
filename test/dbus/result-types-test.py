#! /usr/bin/env python3
# -.- coding: utf-8 -.-

# result-types-test.py
#
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
				key=lambda x: x.timestamp,
				reverse=True
			)
		]
		self.assertEqual(list(ids), sorted_event_ids)

	def testResultTypesLeastRecentEvents(self):
		import_events("test/data/five_events.js", self)

		# LeastRecentEvents - old -> new
		ids = self.findEventIdsAndWait([],
			num_events = 0,
			result_type = ResultType.LeastRecentEvents)
		events = self.getEventsAndWait(ids)
		sorted_event_ids = [
			event.id for event in sorted(events,
				key=lambda x: x.timestamp)
		]
		self.assertEqual(list(ids), sorted_event_ids)

	def testResultTypesMostPopularActor(self):
		import_events("test/data/twenty_events.js", self)

		ids = self.findEventIdsAndWait([],
			num_events = 0,
			result_type = ResultType.MostPopularActor)
		events = self.getEventsAndWait(ids)
		self.assertEqual([e[0][4] for e in events], ["firefox", "icedove",
			"frobnicator"])
		self.assertEqual([e.timestamp for e in events], ["119", "114", "105"])

	def testResultTypesMostPopularActor2(self):
		import_events("test/data/twenty_events.js", self)

		ids = self.findEventIdsAndWait([],
			timerange = (105,107),
			num_events = 0,
			result_type = ResultType.MostPopularActor)
		events = self.getEventsAndWait(ids)
		self.assertEqual(len(events), 2)
		self.assertEqual([e[0][4] for e in events], ["firefox", "frobnicator"])
		self.assertEqual([e.timestamp for e in events], ["107", "105"])

	def testResultTypesLeastPopularActor(self):
		import_events("test/data/twenty_events.js", self)

		ids = self.findEventIdsAndWait([],
			num_events = 0,
			result_type = ResultType.LeastPopularActor)
		events = self.getEventsAndWait(ids)

		self.assertEqual([e[0][4] for e in events], ["frobnicator", "icedove",
			"firefox"])
		self.assertEqual([e.timestamp for e in events], ["105", "114", "119"])

	def testResultTypesLeastPopularActor2(self):
		import_events("test/data/twenty_events.js", self)

		ids = self.findEventIdsAndWait([],
			timerange = (105,107),
			num_events = 0,
			result_type = ResultType.LeastPopularActor)
		events = self.getEventsAndWait(ids)

		self.assertEqual(len(events), 2)
		self.assertEqual([e[0][4] for e in events], ["frobnicator", "firefox"])
		self.assertEqual([e.timestamp for e in events], ["105", "107"])

	def testResultTypesMostRecentSubject(self):
		import_events("test/data/five_events.js", self)

		ids = self.findEventIdsAndWait([],
			num_events = 0,
			result_type = ResultType.MostRecentSubjects)
		events = self.getEventsAndWait(ids)

		self.assertEqual([e.timestamp for e in events],
			["163", "153", "143", "123"])

	def testResultTypesLeastRecentSubject(self):
		import_events("test/data/five_events.js", self)

		ids = self.findEventIdsAndWait([],
			num_events = 0,
			result_type = ResultType.LeastRecentSubjects)
		events = self.getEventsAndWait(ids)
		self.assertEqual([e.timestamp for e in events],
			["123", "143", "153", "163"])

	def testResultTypesMostPopularSubject(self):
		import_events("test/data/five_events.js", self)

		ids = self.findEventIdsAndWait([],
			num_events = 0,
			result_type = ResultType.MostPopularSubjects)
		events = self.getEventsAndWait(ids)
		self.assertEqual([e.timestamp for e in events],
			["143", "163", "153", "123"])

	def testResultTypesLeastPopularSubject(self):
		import_events("test/data/five_events.js", self)

		ids = self.findEventIdsAndWait([],
			num_events = 0,
			result_type = ResultType.LeastPopularSubjects)
		events = self.getEventsAndWait(ids)

		self.assertEqual([e.timestamp for e in events],
			["123", "153", "163", "143"])

	def testResultTypesMostRecentCurrentUri(self):
		import_events("test/data/five_events.js", self)
		import_events("test/data/five_events_ext_move.js", self)

		ids = self.findEventIdsAndWait([],
			num_events = 0,
			result_type = ResultType.MostRecentCurrentUri)
		events = self.getEventsAndWait(ids)

		self.assertEqual([e.timestamp for e in events],
			["200", "153", "123"])

	def testResultTypesLeastRecentCurrentUri(self):
		import_events("test/data/five_events.js", self)
		import_events("test/data/five_events_ext_move.js", self)

		ids = self.findEventIdsAndWait([],
			num_events = 0,
			result_type = ResultType.LeastRecentCurrentUri)
		events = self.getEventsAndWait(ids)
		self.assertEqual([e.timestamp for e in events],
			["123", "153", "200"])

	def testResultTypesMostPopularCurrentUri(self):
		import_events("test/data/five_events.js", self)
		import_events("test/data/five_events_ext_move.js", self)

		ids = self.findEventIdsAndWait([],
			num_events = 0,
			result_type = ResultType.MostPopularCurrentUri)
		events = self.getEventsAndWait(ids)
		self.assertEqual([e.timestamp for e in events],
			["200", "123", "153"])

	def testResultTypesLeastPopularCurrentUri(self):
		import_events("test/data/five_events.js", self)
		import_events("test/data/five_events_ext_move.js", self)

		ids = self.findEventIdsAndWait([],
			num_events = 0,
			result_type = ResultType.LeastPopularCurrentUri)
		events = self.getEventsAndWait(ids)
		self.assertEqual([e.timestamp for e in events],
			["153", "123", "200"])

	def testResultTypesMostRecentCurrentOrigin(self):
		import_events("test/data/five_events.js", self)
		import_events("test/data/five_events_ext_move.js", self)

		ids = self.findEventIdsAndWait([],
			num_events=0,
			result_type=ResultType.MostRecentCurrentOrigin)
		events = self.getEventsAndWait(ids)

		self.assertEqual([e.timestamp for e in events],
			["200", "163", "153", "123"])

	def testResultTypesLeastRecentCurrentOrigin(self):
		import_events("test/data/five_events.js", self)
		import_events("test/data/five_events_ext_move.js", self)

		ids = self.findEventIdsAndWait([],
			num_events=0,
			result_type=ResultType.LeastRecentCurrentOrigin)
		events = self.getEventsAndWait(ids)
		self.assertEqual([e.timestamp for e in events],
			["123", "153", "163", "200"])

	def testResultTypesMostPopularCurrentOrigin(self):
		import_events("test/data/five_events.js", self)
		import_events("test/data/five_events_ext_move.js", self)

		ids = self.findEventIdsAndWait([],
			num_events=0,
			result_type=ResultType.MostPopularCurrentOrigin)
		events = self.getEventsAndWait(ids)
		self.assertEqual([e.timestamp for e in events],
			["200", "123", "163", "153"])

	def testResultTypesLeastPopularCurrentOrigin(self):
		import_events("test/data/five_events.js", self)
		import_events("test/data/five_events_ext_move.js", self)

		ids = self.findEventIdsAndWait([],
			num_events=0,
			result_type=ResultType.LeastPopularCurrentOrigin)
		events = self.getEventsAndWait(ids)
		self.assertEqual([e.timestamp for e in events],
			["153", "163", "123", "200"])

	def testResultTypesMostRecentActor(self):
		import_events("test/data/twenty_events.js", self)

		ids = self.findEventIdsAndWait([],
			num_events = 0,
			result_type = ResultType.MostRecentActor)
		events = self.getEventsAndWait(ids)

		self.assertEqual([e.timestamp for e in events], ["119", "114", "105"])

	def testResultTypesMostRecentActor2(self):
		import_events("test/data/twenty_events.js", self)

		ids = self.findEventIdsAndWait([],
			timerange = (105, 107),
			num_events = 0,
			result_type = ResultType.MostRecentActor)
		events = self.getEventsAndWait(ids)

		self.assertEqual([e.timestamp for e in events], ["107", "105"])

	def testResultTypesOldestActorBug641968(self):
		events = [
			new_event(timestamp=1, actor="boo", subject_uri="tmp/boo"),
			new_event(timestamp=2, actor="boo", subject_uri="home/boo"),
			new_event(timestamp=3, actor="bar", subject_uri="tmp/boo"),
			new_event(timestamp=4, actor="baz", subject_uri="tmp/boo"),
		]
		self.insertEventsAndWait(events)

		# Get the least recent actors
		ids = self.findEventIdsAndWait([],
			num_events = 0,
			result_type = ResultType.OldestActor)
		events = self.getEventsAndWait(ids)
		self.assertEqual(list(ids), [1, 3, 4])

		# Get the least recent actors for "home/boo"
		template = Event.new_for_values(subject_uri="home/boo")
		ids = self.findEventIdsAndWait([template],
			num_events = 0,
			result_type = ResultType.OldestActor)
		self.assertEqual(list(ids), [2])

		# Let's also try the same with MostRecentActor... Although there
		# should be no problem here.
		template = Event.new_for_values(subject_uri="home/boo")
		ids = self.findEventIdsAndWait([template],
			num_events = 0,
			result_type = ResultType.OldestActor)
		self.assertEqual(list(ids), [2])

	def testResultTypesOldestActor(self):
		import_events("test/data/twenty_events.js", self)

		ids = self.findEventIdsAndWait(
			[Event.new_for_values(subject_manifestation="stfu:File")],
			num_events = 0,
			result_type = ResultType.OldestActor)
		events = self.getEventsAndWait(ids)
		self.assertEqual([e.timestamp for e in events], ["100", "101", "105"])

	def testResultTypesLeastRecentActor(self):
		import_events("test/data/twenty_events.js", self)

		ids = self.findEventIdsAndWait(
			[Event.new_for_values(subject_manifestation="stfu:File")],
			num_events = 0,
			result_type = ResultType.LeastRecentActor)
		events = self.getEventsAndWait(ids)

		self.assertEqual([e.timestamp for e in events], ['105', '114', '119'])

	def testResultTypesLeastRecentActor2(self):
		# The same test as before, but this time with fewer events so that
		# it is actually understandable.
		events = [
			new_event(timestamp=1, actor="gedit", subject_uri="oldFile"),
			new_event(timestamp=2, actor="banshee", subject_uri="oldMusic"),
			new_event(timestamp=3, actor="banshee", subject_uri="newMusic"),
			new_event(timestamp=4, actor="gedit", subject_uri="newFile"),
		]
		self.insertEventsAndWait(events)

		ids = self.findEventIdsAndWait([],
			num_events = 0,
			result_type = ResultType.LeastRecentActor)
		recv_events = self.getEventsAndWait(ids)
		self.assertEqual([e.timestamp for e in recv_events], ['3', '4'])

	def testResultTypesMostPopularEventOrigin(self):
		import_events("test/data/twenty_events.js", self)

		ids = self.findEventIdsAndWait([],
			num_events = 0,
			result_type = ResultType.MostPopularEventOrigin)
		events = self.getEventsAndWait(ids)

		self.assertEqual([e[0][5] for e in events],
			["origin1", "origin3", "origin2"])
		self.assertEqual([e.timestamp for e in events], ["102", "103", "100"])

	def testResultTypesLeastPopularEventOrigin(self):
		import_events("test/data/twenty_events.js", self)

		ids = self.findEventIdsAndWait([],
			num_events = 0,
			result_type = ResultType.LeastPopularEventOrigin)
		events = self.getEventsAndWait(ids)

		self.assertEqual([e[0][5] for e in events],
			["origin2", "origin3", "origin1"])
		self.assertEqual([e.timestamp for e in events], ["100", "103", "102"])

	def testResultTypesMostRecentEventOrigin(self):
		import_events("test/data/twenty_events.js", self)

		ids = self.findEventIdsAndWait([],
			num_events = 0,
			result_type = ResultType.MostRecentEventOrigin)
		events = self.getEventsAndWait(ids)

		self.assertEqual([e.timestamp for e in events], ["103", "102", "100"])

	def testResultTypesLeastRecentEventOrigin(self):
		import_events("test/data/twenty_events.js", self)

		ids = self.findEventIdsAndWait([],
			num_events = 0,
			result_type = ResultType.LeastRecentEventOrigin)
		events = self.getEventsAndWait(ids)

		self.assertEqual([e.timestamp for e in events], ["100", "102", "103"])

	def testResultTypesMostPopularSubjectOrigin(self):
		import_events("test/data/twenty_events.js", self)

		ids = self.findEventIdsAndWait([],
			num_events = 0,
			result_type = ResultType.MostPopularOrigin)
		events = self.getEventsAndWait(ids)

		self.assertEqual([e[1][0][3] for e in events], ["file:///tmp", "file:///home",
			"file:///etc"])
		self.assertEqual([e.timestamp for e in events], ["116", "118", "119"])

	def testResultTypesLeastPopularSubjectOrigin(self):
		import_events("test/data/twenty_events.js", self)

		ids = self.findEventIdsAndWait([],
			num_events = 0,
			result_type = ResultType.LeastPopularOrigin)
		events = self.getEventsAndWait(ids)

		self.assertEqual([e[1][0][3] for e in events], ["file:///etc", "file:///home",
			"file:///tmp"])
		self.assertEqual([e.timestamp for e in events], ["119", "118", "116"])

	def testResultTypesMostRecentSubjectOrigin(self):
		import_events("test/data/twenty_events.js", self)

		ids = self.findEventIdsAndWait([],
			num_events = 0,
			result_type = ResultType.MostRecentOrigin)
		events = self.getEventsAndWait(ids)

		self.assertEqual([e.timestamp for e in events], ["119", "118", "116"])

	def testResultTypesLeastRecentSubjectOrigin(self):
		import_events("test/data/twenty_events.js", self)

		ids = self.findEventIdsAndWait([],
			num_events = 0,
			result_type = ResultType.LeastRecentOrigin)
		events = self.getEventsAndWait(ids)

		self.assertEqual([e.timestamp for e in events], ["116", "118", "119"])

	def testResultTypesMostRecentMimeType(self):
		import_events("test/data/twenty_events.js", self)

		ids = self.findEventIdsAndWait([],
			num_events = 0,
			result_type = ResultType.MostRecentMimeType)
		events = self.getEventsAndWait(ids)

		self.assertEqual([e.timestamp for e in events], ['119', '114', '110', '107'])

	def testResultTypesLeastRecentMimeType(self):
		import_events("test/data/twenty_events.js", self)

		ids = self.findEventIdsAndWait([],
			num_events = 0,
			result_type = ResultType.LeastRecentMimeType)
		events = self.getEventsAndWait(ids)

		self.assertEqual([e.timestamp for e in events], ['107', '110', '114', '119'])

	def testResultTypesMostPopularMimeType(self):
		import_events("test/data/twenty_events.js", self)

		ids = self.findEventIdsAndWait([],
			num_events = 0,
			result_type = ResultType.MostPopularMimeType)
		events = self.getEventsAndWait(ids)

		self.assertEqual([e.timestamp for e in events], ['119', '110', '107', '114'])

	def testResultTypesLeastPopularMimeType(self):
		import_events("test/data/twenty_events.js", self)

		ids = self.findEventIdsAndWait([],
			num_events = 0,
			result_type = ResultType.LeastPopularMimeType)
		events = self.getEventsAndWait(ids)

		self.assertEqual([e.timestamp for e in events], ['114', '107', '110', '119'])

	def testResultTypesMostRecentSubjectInterpretation(self):
		import_events("test/data/twenty_events.js", self)

		ids = self.findEventIdsAndWait([],
			num_events = 0,
			result_type = ResultType.MostRecentSubjectInterpretation)
		events = self.getEventsAndWait(ids)

		self.assertEqual([e.timestamp for e in events], ['119', '118', '116', '106'])

	def testResultTypesLeastRecentSubjectInterpretation(self):
		import_events("test/data/twenty_events.js", self)

		ids = self.findEventIdsAndWait([],
			num_events = 0,
			result_type = ResultType.LeastRecentSubjectInterpretation)
		events = self.getEventsAndWait(ids)

		self.assertEqual([e.timestamp for e in events], ['106', '116', '118', '119'])

	def testResultTypesMostPopularSubjectInterpretation(self):
		import_events("test/data/twenty_events.js", self)

		ids = self.findEventIdsAndWait([],
			num_events = 0,
			result_type = ResultType.MostPopularSubjectInterpretation)
		events = self.getEventsAndWait(ids)

		self.assertEqual([e.timestamp for e in events], ['119', '116', '106', '118'])

	def testResultTypesLeastPopularSubjectInterpretation(self):
		import_events("test/data/twenty_events.js", self)

		ids = self.findEventIdsAndWait([],
			num_events = 0,
			result_type = ResultType.LeastPopularSubjectInterpretation)
		events = self.getEventsAndWait(ids)

		self.assertEqual([e.timestamp for e in events], ['118', '106', '116', '119'])

if __name__ == "__main__":
	testutils.run()

# vim:noexpandtab:ts=4:sw=4
