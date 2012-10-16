#! /usr/bin/python
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
        initial_sql = open("test/data/databases/%s.sql" % from_version).read()
        con.cursor().executescript(initial_sql)
        del con

        # Launch Zeitgeist, using the created database
        super(ZeitgeistUpgradeTest, self).setUp(self._db_file)

    def sanity_check(self):
        events = self.findEventsForTemplatesAndWait([])
        self.assertEquals(len(events), 3)

        # Introduced in Zeitgeist 0.8.0:
        #  - event.origin
        #  - subject.current_uri
        #  - subject.storage
        for event in events:
            self.assertEquals(event.origin, "")
            for subject in event.subjects:
                self.assertEquals(subject.current_uri, subject.uri)

        # Introduced in Bluebird Alpha 2:
        #  - WebDataObject

    def testUpgradeFrom071(self):
        self.prepare("071")
        self.sanity_check()

if __name__ == "__main__":
	unittest.main()
