#! /usr/bin/env python
# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2010 Seif Lotfy <seif@lotfy.com>
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

from zeitgeist import _config
_config.setup_path()

from _zeitgeist.engine.sql import get_default_cursor

cursor = get_default_cursor()

# Get all ids from all tables
uris = [id[0] for id in cursor.execute("SELECT id FROM uri").fetchall()]
interpretations = [id[0] for id in cursor.execute("SELECT id FROM interpretation").fetchall()]
manifestations = [id[0] for id in cursor.execute("SELECT id FROM manifestation").fetchall()]
actors = [id[0] for id in cursor.execute("SELECT id FROM actor").fetchall()]
mimetypes = [id[0] for id in cursor.execute("SELECT id FROM mimetype").fetchall()]
texts = [id[0] for id in cursor.execute("SELECT id FROM text").fetchall()]
storages = [id[0] for id in cursor.execute("SELECT id FROM storage").fetchall()]
payloads = [id[0] for id in cursor.execute("SELECT id FROM payload").fetchall()]
events = [event for event in cursor.execute("SELECT * FROM event").fetchall()]

# Check if each event field if they exist in the respected ids table
# if not add to the respected "failure list"
for event in events:
    if not event[2] in interpretations and event[2]:
        print "event %i: broken interpretation %s" %(event[0], event[2])
    if not event[3] in manifestations and event[3]:
        print "event %i: broken manifestations %s" %(event[0], event[3])
    if not event[4] in actors and event[4]:
        print "event %i: broken actor %s" %(event[0], event[4])
    if not event[5] in payloads and event[5]:
        print "event %i: broken payload %s" %(event[0], event[5])
    if not event[6] in uris and event[6]:
        print "event %i: broken subj_id %s" %(event[0], event[6])
    if not event[7] in interpretations and events[7]:
        print "event %i: broken subj_interpretation %s" %(event[0], event[7])
    if not event[8] in manifestations and event[8]:
        print "event %i: broken subj_manifestations %s" %(event[0], event[8])
    if not event[9] in uris and event[9]:
        print "event %i: broken subj_origin %s" %(event[0], event[9])
    if not event[10] in mimetypes and event[10]:
        print "event %i: broken subj_mimetype. %s" %(event[0], event[10])
    if not event[11] in texts and event[11]:
        print "event %i: broken subj_text %s" %(event[0], event[11])
    if not event[12] in storages and event[12]:
        print "event %i: broken subj_storage %s" %(event[0], event[12])
