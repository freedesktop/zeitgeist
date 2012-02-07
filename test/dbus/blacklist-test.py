#! /usr/bin/python
# -.- coding: utf-8 -.-

# remote-test.py
#
# Copyright © 2009 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
# Copyright © 2010 Markus Korn <thekorn@gmx.de>
# Copyright © 2010 Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
# Copyright © 2011 Manish Sinha <manishsinha@ubuntu.com>
# Copyright © 2011 Collabora Ltd.
#             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
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

# Update python path to use local zeitgeist module
import sys
import os
import unittest
import gobject

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from zeitgeist.client import ZeitgeistDBusInterface
from zeitgeist.datamodel import *
from testutils import RemoteTestCase, asyncTestMethod

class BlacklistTest(RemoteTestCase):

	def __init__(self, methodName):
		super(BlacklistTest, self).__init__(methodName)
		self.blacklist = None

	def setUp(self):
		# lazy import to get a chance to use the private bus
		import dbus
		
		# We set up the connection lazily in order to wait for the
		# engine to come up
		super(BlacklistTest, self).setUp()
		obj = dbus.SessionBus().get_object("org.gnome.zeitgeist.Engine",
			"/org/gnome/zeitgeist/blacklist")
		self.blacklist = dbus.Interface(obj, "org.gnome.zeitgeist.Blacklist")

		self.dbus_signals = set()
	
	def tearDown(self):
		# Cleanup D-Bus signals
		for signal in self.dbus_signals:
			signal.remove()

		super(BlacklistTest, self).tearDown()

	def testClear(self):
		# Insert a blacklist template
		self.blacklist.AddTemplate("unicorns",
			Event.new_for_values(subject_uri="a"))
		self.assertTrue(len(self.blacklist.GetTemplates()) > 0)
		
		# Now remove all existing templates...
		allTemplates = self.blacklist.GetTemplates()
		[self.blacklist.RemoveTemplate(key) for key in allTemplates.iterkeys()]
		
		# And ensure that they are indeed gone.
		self.assertEquals(len(self.blacklist.GetTemplates()), 0)

	def testSetOne(self):
		orig = Event.new_for_values(interpretation=Interpretation.ACCESS_EVENT,
			subject_uri="http://nothingtoseehere.gov")
		self.blacklist.AddTemplate("Foobar", orig)
		res = self.blacklist.GetTemplates()
		
		self.assertEquals(len(res), 1)
		self.assertEventsEqual(orig, Event(res["Foobar"]))

	def testApplyBlacklist(self):
		self.testSetOne()
		ev = Event.new_for_values(interpretation=Interpretation.ACCESS_EVENT,
			subject_uri="http://nothingtoseehere.gov")
		ev.manifestation = Manifestation.USER_ACTIVITY
		ev.actor = "app.//foo.desktop"

		inserted_ids = self.insertEventsAndWait([ev])
		self.assertEquals(1, len(inserted_ids))
		self.assertEquals(0, int(inserted_ids[0]))

		# Now change the event to pass the blacklist
		ev.get_subjects()[0].uri = "htpp://totallyvaliduri.com"
		inserted_ids = self.insertEventsAndWait([ev])
		self.assertEquals(1, len(inserted_ids))
		self.assertTrue(0 != inserted_ids[0])

	def _get_blacklist_iface(self):
		"""
		Create a blacklist interface using the get_extension() method
		from client.py.
		"""
		del self.blacklist
		iface = ZeitgeistDBusInterface()
		blacklist = iface.get_extension("Blacklist", "blacklist")
		return blacklist

	def testBlacklistUsingClientDBusInterface(self):
		"""
		Ensure that get_extension() from client.py method works correctly.
		"""
		blacklist = self._get_blacklist_iface()
		allTemplates = blacklist.GetTemplates()
		[blacklist.RemoveTemplate(key) for key in allTemplates.iterkeys()]
		newAllTemplates = blacklist.GetTemplates()
		self.assertEquals(len(newAllTemplates), 0)

	def testBlacklistSignals(self, mainloop=None, connect_signals=True):
		self.blacklist = self._get_blacklist_iface()
		if mainloop is None:
			mainloop = self.create_mainloop()

		template1 = Event.new_for_values(
			timestamp=0,
			interpretation=Interpretation.ACCESS_EVENT,
			subject_uri="http://nothingtoseehere.gov")

		global hit
		hit = 0

		@asyncTestMethod(mainloop)
		def cb_added(template_id, event_template):
			global hit
			self.assertEquals(hit, 0)
			hit = 1
			self.assertEquals(template_id, "TestTemplate")
			self.assertEventsEqual(template1, event_template)

		@asyncTestMethod(mainloop)
		def cb_removed(template_id, event_template):
			global hit
			self.assertEquals(hit, 1)
			hit = 2
			self.assertEquals(template_id, "TestTemplate")
			self.assertEventsEqual(template1, event_template)
			mainloop.quit()

		# Connect to signals
		if connect_signals:
			self.dbus_signals.add(
				self.blacklist.connect('TemplateAdded', cb_added))
			self.dbus_signals.add(
				self.blacklist.connect('TemplateRemoved', cb_removed))

		def launch_tests():
			self.blacklist.AddTemplate("TestTemplate", template1)
			self.blacklist.RemoveTemplate("TestTemplate")
		gobject.idle_add(launch_tests)

		mainloop.run()

	def testBlacklistSignalWithReconnection(self):
		mainloop = self.create_mainloop()
		self.testBlacklistSignals(mainloop)

		# Restart the Zeitgeist daemon...
		self.kill_daemon()
		self.spawn_daemon()

		# ... and try again without re-connecting to the signals
		self.testBlacklistSignals(mainloop, connect_signals=False)

if __name__ == "__main__":
	unittest.main()
