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
	TimeRange, StorageState, DataSource, NULL_EVENT)

import testutils
from testutils import parse_events

class ZeitgeistRemoteAPITest(testutils.RemoteTestCase):

	def testInsertAndGetEvent(self):
		# Insert an event
		events = parse_events("test/data/single_event.js")
		ids = self.insertEventsAndWait(events)
		self.assertEquals(1, len(ids))

		# Now get it back and check it hasn't changed
		retrieved_events = self.getEventsAndWait(ids)
		self.assertEquals(1, len(retrieved_events))
		self.assertEventsEqual(retrieved_events[0], events[0])

	def testInsertAndDeleteEvent(self):
		# Insert an event
		events = parse_events("test/data/single_event.js")
		ids = self.insertEventsAndWait(events)

		# Delete it, make sure the returned time range is correct
		time_range = self.deleteEventsAndWait(ids)
		self.assertEquals(time_range[0], time_range[1])
		self.assertEquals(time_range[0], int(events[0].timestamp))

		# Make sure the event is gone
		retrieved_events = self.getEventsAndWait(ids)
		self.assertEquals(retrieved_events[0], None)

	def testDeleteNonExistantEvent(self):
		# Insert an event (populate the database so it isn't empty)
		events = parse_events("test/data/single_event.js")
		ids = self.insertEventsAndWait(events)

		# Try deleting a non-existant event
		events = parse_events("test/data/single_event.js")
		time_range = self.deleteEventsAndWait([int(ids[0]) + 1000])
		self.assertEquals(time_range[0], time_range[1])
		self.assertEquals(time_range[0], -1)

		# Make sure the event is still there
		retrieved_events = self.getEventsAndWait(ids)
		self.assertEquals(1, len(retrieved_events))
		self.assertEventsEqual(retrieved_events[0], events[0])

	def testDeleteTwoSimilarEvents(self):
		# Insert a couple similar events
		event1 = parse_events("test/data/single_event.js")[0]
		event2 = Event(event1)
		event2.timestamp = int(event1.timestamp) + 1
		ids = self.insertEventsAndWait([event1, event2])

		# Try deleting one of them
		self.deleteEventsAndWait([ids[0]])

		# Make sure it's gone
		retrieved_events = self.getEventsAndWait([ids[0]])
		self.assertEquals(retrieved_events[0], None)

		# But the second one is still there
		retrieved_events = self.getEventsAndWait([ids[1]])
		self.assertEquals(1, len(retrieved_events))
		self.assertEventsEqual(retrieved_events[0], event2)

class ZeitgeistRemoteInterfaceTest(testutils.RemoteTestCase):

	def testQuit(self):
		"""
		Calling Quit() on the remote interface should shutdown the
		engine in a clean way.
		"""
		self.client._iface.Quit()

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
	unittest.main()
