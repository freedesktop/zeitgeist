#!/usr/bin/python
# -.- coding: utf-8 -.-

# Update python path to use local zeitgeist module
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from zeitgeist.client import ZeitgeistDBusInterface
from zeitgeist.datamodel import *
from testutils import RemoteTestCase

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
		allTemplates = self.blacklist.GetTemplates()
		[self.blacklist.RemoveTemplate(key) for key in allTemplates.iterkeys()]
		newAllTemplates = self.blacklist.GetTemplates()
		self.assertEquals(len(newAllTemplates), 0)
		
	def testSetOne(self):
		orig = Event.new_for_values(interpretation=Interpretation.ACCESS_EVENT,
		                            subject_uri="http://nothingtoseehere.gov")
		self.blacklist.AddTemplate("Foobar", orig)
		res = self.blacklist.GetTemplates()
		
		self.assertEquals(len(res), 1)
		result = Event(res["Foobar"])
		self.assertEquals(result.manifestation, "")
		self.assertEquals(result.interpretation, Interpretation.ACCESS_EVENT)
		self.assertEquals(len(result.subjects), 1)
		self.assertEquals(result.subjects[0].uri, "http://nothingtoseehere.gov")
		self.assertEquals(result.subjects[0].interpretation, "")
	
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

	def testBlacklistUsingClientDBusInterface(self):
		"""
		Ensure that get_extension() from client.py method works correctly.
		"""
		
		del self.blacklist
		iface = ZeitgeistDBusInterface()
		blacklist = iface.get_extension("Blacklist", "blacklist")
		allTemplates = blacklist.GetTemplates()
		[blacklist.RemoveTemplate(key) for key in allTemplates.iterkeys()]
		newAllTemplates = blacklist.GetTemplates()
		self.assertEquals(len(newAllTemplates), 0)

if __name__ == "__main__":
	unittest.main()
