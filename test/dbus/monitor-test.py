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


class ZeitgeistMonitorTest(testutils.RemoteTestCase):

	def testMonitorInsertEvents(self):
		result = []
		mainloop = self.create_mainloop()
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
		
	def testMonitorInsertEventsWithSubjectTemplate(self):
		result = []
		mainloop = self.create_mainloop()
		tmpl = Event.new_for_values(
			subjects=[Subject.new_for_values(uri="file:///tmp/bar.txt")])
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
		
		self.assertEquals(1, len(result))
	
	def testMonitorInsertEventsWithNegatedSubjectTemplate(self):
		result = []
		mainloop = self.create_mainloop()
		tmpl = Event.new_for_values(
			subjects=[Subject.new_for_values(uri="!file:///tmp/bar.txt")])
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
		
		self.assertEquals(4, len(result))
	
	def testMonitorDeleteEvents(self):
		result = []
		mainloop = self.create_mainloop()
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
		mainloop = self.create_mainloop(None)
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
		mainloop = self.create_mainloop()
		events = parse_events("test/data/five_events.js")
		
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
		mainloop.run()
		
		self.assertEquals(2, len(result1))
		self.assertEquals(2, len(result2))

	def testMonitorInstallRemoval(self):
		result = []
		mainloop = self.create_mainloop()
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

if __name__ == "__main__":
	unittest.main()
