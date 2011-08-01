#! /usr/bin/python
# -.- coding: utf-8 -.-

# Zeitgeist
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
	TimeRange, StorageState, DataSource)

import testutils
from testutils import parse_events

class ZeitgeistRemoteAPITest(testutils.RemoteTestCase):

	def testInsertAndGetEvent(self):
		events = parse_events("test/data/single_event.js")
		ids = self.insertEventsAndWait(events)
		retrieved_events = self.getEventsAndWait(ids)
		self.assertEquals(1, len(ids))
		self.assertEquals(1, len(retrieved_events))
		self.assertEventsEqual(retrieved_events[0], events[0])


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
