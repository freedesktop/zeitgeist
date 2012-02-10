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

	def _add_template(self, name, template):
		self.blacklist.AddTemplate(name, template)

		res = self.blacklist.GetTemplates()
		self.assertEventsEqual(template, Event(res[name]))

	def _assert_template_count(self, num):
		self.assertEquals(len(self.blacklist.GetTemplates()), num)

	def _assert_insert_blocked(self, *events):
		inserted_ids = map(int, self.insertEventsAndWait(events))
		zeros = filter(lambda x: x == 0, inserted_ids)
		self.assertEquals(len(events), len(inserted_ids))
		self.assertEquals(len(events), len(zeros))
	
	def _assert_insert_allowed(self, *events):
		inserted_ids = map(int, self.insertEventsAndWait(events))
		self.assertEquals(len(events), len(inserted_ids))
		self.assertEquals([], filter(lambda x: x == 0, inserted_ids))

	def testSetOne(self):
		orig = Event.new_for_values(
			interpretation=Interpretation.ACCESS_EVENT,
			subject_uri="http://nothingtoseehere.gov")

		self._add_template("Foobar", orig)
		self._assert_template_count(1)

	def testApplyBlacklist(self):
		ev = Event.new_for_values(
			interpretation=Interpretation.ACCESS_EVENT,
			manifestation=Manifestation.USER_ACTIVITY,
			actor="app://foo.desktop",
			subject_uri="http://nothingtoseehere.gov")
		self._add_template("Foobar", ev)
		self._assert_template_count(1)

		self._assert_insert_blocked(ev)

		# Now change the event to pass the blacklist
		ev.get_subjects()[0].uri = "http://totallyvaliduri.com"
		self._assert_insert_allowed(ev)

	def testApplyBlacklistWithTwoTemplates(self):
		# Setup an event we'll use to test insertions
		event = Event.new_for_values(
			timestamp = 1,
			interpretation=Interpretation.ACCESS_EVENT,
			manifestation=Manifestation.SCHEDULED_ACTIVITY,
			subject_uri="blarg")

		# With no blacklisted templates we can insert it without problems
		self._assert_insert_allowed(event)

		# We blacklist the event's interpretation
		templ1 = Event.new_for_values(
			interpretation=Interpretation.ACCESS_EVENT)
		self._add_template("One", templ1)
		self._assert_template_count(1)

		# Now it can't be inserted anymore
		event.timestamp = 1
		self._assert_insert_blocked(event)

		# We blacklist the event's URI
		templ2 = Event.new_for_values(
			subject_uri="blarg")
		self._add_template("Two", templ1)
		self._assert_template_count(2)

		# No way it can be logged now
		event.timestamp = 2 # change timestamp so it isn't a duplicate event
		self._assert_insert_blocked(event)

		# We remove the first blacklisted template, it still can't get logged
		self.blacklist.RemoveTemplate("One")
		self._assert_template_count(1)
		event.timestamp = 3
		self._assert_insert_blocked(event)

		# Removing the second template, now it'll let us insert it
		self.blacklist.RemoveTemplate("Two")
		self._assert_template_count(0)
		event.timestamp = 4
		self._assert_insert_allowed(event)

		# Finally, we blacklist a template that doesn't match the event
		templ3 = Event.new_for_values(
			interpretation=Interpretation.ACCESS_EVENT,
			manifestation=Manifestation.USER_ACTIVITY)
		self._add_template("One", templ3) # reuse the template identifier, why not?
		self._assert_template_count(1)

		# And of course we can still insert it :)
		event.timestamp = 5
		self._assert_insert_allowed(event)

	def testApplyBlacklistWithSpacesInURI(self):
		# We blacklist a particular URI
		templ1 = Event.new_for_values(subject_uri="New York is a city")
		self._add_template("One", templ1)
		self._assert_template_count(1)

		# And check that it works
		self._assert_insert_blocked(Event.new_for_values(
			subject_uri="New York is a city"))
		self._assert_insert_allowed(Event.new_for_values(
			subject_uri="New York is a city NOT"))
		self._assert_insert_allowed(Event.new_for_values(
			subject_uri="Do you like cheese?"))
		self._assert_insert_allowed(Event.new_for_values(
			interpretation=Interpretation.MOVE_EVENT,
			subject_uri="kung fu",
			subject_current_uri="New York is a city"))

	def testApplyBlacklistWithAccentsInURI(self):
		# We blacklist some particular URIs
		self._add_template("weirdo", Event.new_for_values(
			subject_uri=u"çàrßá€"))
		self._add_template("normalo", Event.new_for_values(
			subject_uri=u"hello"))
		self._assert_template_count(2)

		# And check that the blacklisting works
		self._assert_insert_blocked(Event.new_for_values(
			subject_uri=u"çàrßá€"))
		self._assert_insert_blocked(Event.new_for_values(
			subject_uri=u"hello"))
		self._assert_insert_allowed(Event.new_for_values(
			subject_uri=u"hola"))
		self._assert_insert_allowed(Event.new_for_values(
			subject_uri=u"çàrßá"))

	def testApplyBlacklistForEventWithEmptyCurrentURI(self):
		# We blacklist some particular current URI
		self._add_template("t", Event.new_for_values(subject_current_uri=u"t"))
		self._assert_template_count(1)

		# Blocking the current_uri works
		self._assert_insert_blocked(Event.new_for_values(
			interpretation=Interpretation.MOVE_EVENT,
			subject_current_uri="t"))

		# But if we only set uri (and leave it up to Zeitgeist to set current_uri
		# to the same value?
		self._assert_insert_blocked(Event.new_for_values(subject_uri="t"))

	def testApplyBlacklistWithWildcardInURI(self):
		# We blacklist some particular URIs
		self._add_template("wild", Event.new_for_values(
			subject_uri=u"block me*"))
		self._assert_template_count(1)

		# And check that the blacklisting works
		self._assert_insert_blocked(Event.new_for_values(
			subject_uri=u"block me"))
		self._assert_insert_blocked(Event.new_for_values(
			subject_uri=u"block me*"))
		self._assert_insert_blocked(Event.new_for_values(
			subject_uri=u"block me now"))
		self._assert_insert_blocked(Event.new_for_values(
			subject_uri=u"block meß :)"))
		self._assert_insert_allowed(Event.new_for_values(
			subject_uri=u"block mNOT"))
		self._assert_insert_allowed(Event.new_for_values(
			subject_uri=u"nblock me"))

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
			self.blacklist.connect('TemplateAdded', cb_added)
			self.blacklist.connect('TemplateRemoved', cb_removed)

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
