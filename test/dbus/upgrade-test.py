#! /usr/bin/env python3
# -.- coding: utf-8 -.-

# upgrade-test.py
#
# Copyright © 2012 Collabora Ltd.
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

import os
import sqlite3
import tempfile
import unittest

from zeitgeist.datamodel import *

import testutils
from testutils import parse_events, import_events

class ZeitgeistUpgradeTest(testutils.RemoteTestCase):

    def setUp(self):
        self._db_file = tempfile.mktemp(".sqlite", prefix="zeitgeist.upgrade.")
        # Do nothing, functions should call prepare() instead

    def tearDown(self):
        super(ZeitgeistUpgradeTest, self).tearDown()
        os.remove(self._db_file)

    def prepare(self, from_version):
        # Create initial database
        con = sqlite3.connect(self._db_file)
        with open("test/data/databases/%s.sql" % from_version) as f:
                initial_sql = f.read()
        con.cursor().executescript(initial_sql)
        del con

        # Launch Zeitgeist, using the created database
        super(ZeitgeistUpgradeTest, self).setUp(self._db_file)

    def sanity_check(self):
        events = self.findEventsForTemplatesAndWait([])
        original_events = parse_events("test/data/upgrade_test.js")

        # Ensure no events got lost (or duplicated)
        self.assertEqual(len(events), len(original_events))

        # Ensure no subjects got lost
        for i in range(len(events)):
            self.assertEqual(len(events[i].subjects),
                              len(original_events[i].subjects))

        # Ensure data didn't change (unless it should)
        for i in range(len(events)):
            a = events[i]
            b = original_events[i]
            self.assertEqual(a.timestamp, b.timestamp)
            self.assertEqual(a.interpretation, b.interpretation)
            self.assertEqual(a.manifestation, b.manifestation)
            self.assertEqual(a.actor, b.actor)
            for j in range(len(a.subjects)):
                sa = a.subjects[j]
                sb = b.subjects[j]
                self.assertEqual(sa.uri, sb.uri)
                self.assertEqual(sa.interpretation, sb.interpretation)
                if not sa.uri.startswith("http://"):
                    self.assertEqual(sa.manifestation, sb.manifestation)
                self.assertEqual(sa.origin, sb.origin)
                self.assertEqual(sa.mimetype, sb.mimetype)
                self.assertEqual(sa.text, sb.text)
                self.assertEqual(sa.storage, sb.storage)

        # Introduced in Zeitgeist 0.8.0:
        #  - event.origin
        #  - subject.current_uri
        for event in events:
            self.assertEqual(event.origin, "")
            for subject in event.subjects:
                self.assertEqual(subject.current_uri, subject.uri)

        # Introduced in Bluebird Alpha 2:
        #  - WebDataObject
        for event in events:
            for subject in event.subjects:
                if subject.uri.startswith("http://"):
                    self.assertEqual(subject.manifestation, Manifestation.WEB_DATA_OBJECT)

        # Introduced in Zeitgeist 1.0 Beta 1
        #  - subject.current_origin
        for event in events:
            for subject in event.subjects:
                self.assertEqual(subject.current_origin, subject.origin)

    def testUpgradeFrom071(self):
        self.prepare("071")
        self.sanity_check()

    def testUpgradeFrom080(self):
        self.prepare("080")
        self.sanity_check()

    def testUpgradeFrom090a1(self):
        self.prepare("090~alpha1")
        self.sanity_check()

    def testUpgradeFrom090a2(self):
        self.prepare("090~alpha2")
        self.sanity_check()

    def testUpgradeFrom090a3(self):
        self.prepare("090~alpha3")
        self.sanity_check()

if __name__ == "__main__":
	unittest.main()
