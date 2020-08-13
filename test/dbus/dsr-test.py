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

import unittest
import os
import sys
import logging
import signal
import time
import tempfile
import shutil
import pickle
import gi
from subprocess import Popen, PIPE

# DBus setup
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)
from dbus.exceptions import DBusException

from gi.repository import GLib
from zeitgeist.datamodel import (Event, Subject, Interpretation, Manifestation,
	TimeRange, StorageState, DataSource, NULL_EVENT, ResultType)

import testutils
from testutils import parse_events, import_events, asyncTestMethod


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
		"© mwhahaha çàéü",
		"ThŊ§ ıs teĦ ün↓çØÐe¡",
		[]
	]

	_ds2b = [
		"www.example.org/bar", # same unique ID as _ds2
		"This string has been translated into the ASCII language",
		"Now the unicode is gone :(",
		[
			Event.new_for_values(subject_manifestation = "nah"),
		],
	]
	
	def __init__(self, methodName):
		super(ZeitgeistRemoteDataSourceRegistryTest, self).__init__(methodName)
	
	def get_plain(self, ev):
		"""
		Ensure that an Event instance is a Plain Old Python Object (popo),
		without DBus wrappings etc.
		"""
		popo = []
		ev[0][0] = ""
		popo.append(list(map(str, ev[0])))
		popo.append([list(map(str, subj)) for subj in ev[1]])
		# We need the check here so that if D-Bus gives us an empty
		# byte array we don't serialize the text "dbus.Array(...)".
		popo.append(str(ev[2]) if ev[2] else '')
		return popo
	
	def _assertDataSourceEquals(self, dsdbus, dsref):
		self.assertEqual(dsdbus[DataSource.UniqueId], dsref[0])
		self.assertEqual(dsdbus[DataSource.Name], dsref[1])
		self.assertEqual(dsdbus[DataSource.Description], dsref[2])
		self.assertEqual(len(dsdbus[DataSource.EventTemplates]), len(dsref[3]))
		for i, template in enumerate(dsref[3]):
			tmpl = dsdbus[DataSource.EventTemplates][i]
			self.assertEqual(self.get_plain(tmpl), self.get_plain(template))
	
	def testPresence(self):
		""" Ensure that the DataSourceRegistry extension is there """
		iface = self.client._iface # we know that client._iface is as clean as possible
		registry = iface.get_extension("DataSourceRegistry", "data_source_registry")
		registry.GetDataSources()
	
	def testGetDataSourcesEmpty(self):
		self.assertEqual(self.client._registry.GetDataSources(), [])
	
	def testRegisterDataSource(self):
		self.client.register_data_source(*self._ds1)
		datasources = list(self.client._registry.GetDataSources())
		self.assertEqual(len(datasources), 1)
		self._assertDataSourceEquals(datasources[0], self._ds1)
	
	def testRegisterDataSourceUnicode(self):
		self.client.register_data_source(*self._ds2)
		datasources = list(self.client._registry.GetDataSources())
		self.assertEqual(len(datasources), 1)
		self._assertDataSourceEquals(datasources[0], self._ds2)
	
	def testRegisterDataSourceWithCallback(self):
		self.client.register_data_source(*self._ds1, enabled_callback=lambda x: True)
	
	def testRegisterDataSources(self):
		# Insert two data-sources
		self.client._registry.RegisterDataSource(*self._ds1)
		self.client._registry.RegisterDataSource(*self._ds2)
		
		# Verify that they have been inserted correctly
		datasources = list(self.client._registry.GetDataSources())
		self.assertEqual(len(datasources), 2)
		datasources.sort(key=lambda x: x[DataSource.UniqueId])
		self._assertDataSourceEquals(datasources[0], self._ds1)
		self._assertDataSourceEquals(datasources[1], self._ds2)
		
		# Change the information of the second data-source
		self.client._registry.RegisterDataSource(*self._ds2b)
		
		# Verify that it changed correctly
		datasources = list(self.client._registry.GetDataSources())
		self.assertEqual(len(datasources), 2)
		datasources.sort(key=lambda x: x[DataSource.UniqueId])
		self._assertDataSourceEquals(datasources[0], self._ds1)
		self._assertDataSourceEquals(datasources[1], self._ds2b)
	
	def testSetDataSourceEnabled(self):
		# Insert a data-source -- it should be enabled by default
		self.client._registry.RegisterDataSource(*self._ds1)
		ds = list(self.client._registry.GetDataSources())[0]
		self.assertEqual(ds[DataSource.Enabled], True)
		
		# Now we can choose to disable it...
		self.client._registry.SetDataSourceEnabled(self._ds1[0], False)
		ds = list(self.client._registry.GetDataSources())[0]
		self.assertEqual(ds[DataSource.Enabled], False)
		
		# And enable it again!
		self.client._registry.SetDataSourceEnabled(self._ds1[0], True)
		ds = list(self.client._registry.GetDataSources())[0]
		self.assertEqual(ds[DataSource.Enabled], True)

	def testSetDataSourceDisabled(self):
		# Insert a data-source -- it should be enabled by default
		self.client._registry.RegisterDataSource(*self._ds1)
		ds = list(self.client._registry.GetDataSources())[0]
		self.assertEqual(ds[DataSource.Enabled], True)

		# Now we can choose to disable it...
		self.client._registry.SetDataSourceEnabled(self._ds1[0], False)
		ds = list(self.client._registry.GetDataSources())[0]
		self.assertEqual(ds[DataSource.Enabled], False)

		event = Event.new_for_values(
			interpretation="interpretation",
			manifestation="manifestation",
			actor="actor",
			subject_uri="some uri",
			subject_manifestation="!stfu:File")

		# ... which will block its events from being inserted
		ids = self.insertEventsAndWait([event])
		self.assertEqual(ids[0], 0)

		# And enable it again!
		self.client._registry.SetDataSourceEnabled(self._ds1[0], True)
		ds = list(self.client._registry.GetDataSources())[0]
		self.assertEqual(ds[DataSource.Enabled], True)

		ids = self.insertEventsAndWait([event])
		self.assertEqual(ids[0], 1)

	def testGetDataSourceFromId(self):
		# Insert a data-source -- and then retrieve it by id
		self.client._registry.RegisterDataSource(*self._ds1)
		ds = self.client._registry.GetDataSourceFromId(self._ds1[0])
		self._assertDataSourceEquals(ds, self._ds1)
		
		# Retrieve a data-source from an id that has not been registered
		self.assertRaises(DBusException,
			self.client._registry.GetDataSourceFromId,
			self._ds2[0])

	def testDataSourceSignals(self):
		mainloop = self.create_mainloop()
		
		global hit
		hit = 0
		
		@asyncTestMethod(mainloop)
		def cb_registered(datasource):
			global hit
			self.assertEqual(hit, 0)
			hit = 1
		
		@asyncTestMethod(mainloop)
		def cb_enabled(unique_id, enabled):
			global hit
			if hit == 1:
				self.assertEqual(enabled, False)
				hit = 2
			elif hit == 2:
				self.assertEqual(enabled, True)
				hit = 3
				# We're done -- change this if we figure out how to force a
				# disconnection from the bus, so we can also check the
				# DataSourceDisconnected signal.
				mainloop.quit()
			else:
				self.fail("Unexpected number of signals: %d." % hit)
		
		#@asyncTestMethod(mainloop)
		#def cb_disconnect(datasource):
		#	self.assertEquals(hit, 3)
		#	mainloop.quit()
		
		# Connect to signals
		self.client._registry.connect('DataSourceRegistered', cb_registered)
		self.client._registry.connect('DataSourceEnabled', cb_enabled)
		#self.client._registry.connect('DataSourceDisconnected', cb_disconnect)
		
		# Register data-source, disable it, enable it again
		GLib.idle_add(self.testSetDataSourceEnabled)
		
		mainloop.run()
	
	def testRegisterDataSourceEnabledCallbackOnRegister(self):
		mainloop = self.create_mainloop()
		
		@asyncTestMethod(mainloop)
		def callback(enabled):
			mainloop.quit()
		self.client.register_data_source(*self._ds1, enabled_callback=callback)
		
		mainloop.run()
	
	def testRegisterDataSourceEnabledCallbackOnChange(self):
		mainloop = self.create_mainloop()
		global hit
		hit = 0
		
		# Register a callback
		@asyncTestMethod(mainloop)
		def callback(enabled):
			global hit
			if hit == 0:
				# Register callback
				hit = 1
			elif hit == 1:
				# Disable callback
				mainloop.quit()
			else:
				self.fail("Unexpected number of signals: %d." % hit)
		self.client.register_data_source(*self._ds1)
		self.client.set_data_source_enabled_callback(self._ds1[0], callback)
		
		# Disable the data-source
		self.client._registry.SetDataSourceEnabled(self._ds1[0], False)

		mainloop.run()


if __name__ == "__main__":
	unittest.main()

# vim:noexpandtab:ts=4:sw=4
