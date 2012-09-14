#! /usr/bin/env python
# -.- coding: utf-8 -.-

# Zeitgeist - Send all events from a JSON file to Zeitgeist
#
# Copyright © 2012 Collabora Ltd.
#             By Siegfried-A. Gevatter <siegfried.gevatter@collabora.co.uk>
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
#
# #############################################################################
# WARNING: Make sure you launch Zeitgeist with ZEITGEIST_DATA_PATH set if
#          you don't want to fill your real database!
#
#          See ./tools/run_fake_zeitgeist.sh for a convenient way of testing
#          Zeitgeist.
# #############################################################################

import os
import sys

from zeitgeist.datamodel import *
from zeitgeist.client import ZeitgeistDBusInterface

# Import parse_events from testutils.py
path = os.path.join(os.path.dirname(__file__), '../../test/dbus')
sys.path.append(path)
from testutils import parse_events

# Max. number of events to send in a D-Bus call
LIMIT = 100

def insert_events(events):
    iface = ZeitgeistDBusInterface()
    print "Inserting %d events..." % len(events)
    while len(events):
        iface.InsertEvents(events[:LIMIT])
        events = events[LIMIT:]
        print "."
    print 'OK.'

def main():
    if len(sys.argv) != 2:
        raise SystemExit, 'Usage: %s <json file>' % sys.argv[0]

    events = parse_events(sys.argv[1])
    insert_events(events)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
