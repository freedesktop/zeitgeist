#! /usr/bin/env python3
# -.- coding: utf-8 -.-

# histogram-test.py
#
# Copyright © 2011 Stefano Candori <stefano.candori@gmail.com>
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
import time
import datetime
import calendar
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from zeitgeist.client import ZeitgeistDBusInterface
from zeitgeist.datamodel import *
from testutils import RemoteTestCase, import_events, new_event

#
# EXPLANATION OF THE TEST:
# The test checks if the histogram extension works well despite the 
# ***timezone's hell***.
# For example the extension, for an user in the GMT+2 timezone, should count 
# an event inserted on the 2011/12/24 at 1:30 AM as belonging to the day 24.
# The problem is that in the engine the events are inserted as UTC-relative:
# for the example our event is inserted for the day 2011/12/23 at 23:30 UTC.
# The Histogram extension must revert this when collecting data, and this test 
# check this.
#
# ******************************************************************************
#
# In the test we create an event in the "borderline" time for the timezone and 
# then we insert it in the engine as UCT-relative. After, we retrieve the data
# from the extension and finally we check that the event belong to the right day
#

class HistogramTest(RemoteTestCase):

	def __init__(self, methodName):
		super(HistogramTest, self).__init__(methodName)
		self.histogram = None

	def setUp(self):
		# lazy import to get a chance to use the private bus
		import dbus
		
		# We set up the connection lazily in order to wait for the
		# engine to come up
		super(HistogramTest, self).setUp()
		obj = dbus.SessionBus().get_object("org.gnome.zeitgeist.Engine",
			"/org/gnome/zeitgeist/journal/activity")
		self.histogram = dbus.Interface(obj, "org.gnome.zeitgeist.Histogram")
		
	def _createEventOne(self):
		ev = new_event(
			interpretation=Interpretation.ACCESS_EVENT,
			subject_uri="file://sisisisisisi")
		ev.manifestation = Manifestation.USER_ACTIVITY
		
		if time.timezone < 0 :
			start_hour = 24 + int(time.timezone / 3600)
		else:
			start_hour =  int(time.timezone / 3600) - 1
			
		td = datetime.datetime.today()
		event_date = datetime.datetime(td.year, td.month, td.day, start_hour, 30)
		timestamp = calendar.timegm(event_date.timetuple())
		
		ev.timestamp = timestamp * 1000
		
		return ev, timestamp
		
	def testGetHistogramData(self):
		ev, ev_timestamp = self._createEventOne();
		
		inserted_ids = self.insertEventsAndWait([ev])
		self.assertEqual(1, len(inserted_ids))
		
		h_data = self.histogram.GetHistogramData()
		self.assertEqual(1, len(h_data))
		
		h_day_timestamp = h_data[0][0]
		
		#Check if the inserted event belong to the right day!
		day_ev = datetime.date.fromtimestamp(ev_timestamp)
		start_day = datetime.date.fromtimestamp(h_day_timestamp)
		self.assertEqual(day_ev.day , start_day.day)

if __name__ == "__main__":
	unittest.main()

# vim:noexpandtab:ts=4:sw=4
