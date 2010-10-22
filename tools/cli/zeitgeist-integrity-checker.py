#! /usr/bin/env python
# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2010 Seif Lotfy <seif@lotfy.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
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

uris = [id[0] for id in cursor.execute("SELECT id FROM uri").fetchall()]
interpretations = [id[0] for id in cursor.execute("SELECT id FROM interpretation").fetchall()]
manifestations = [id[0] for id in cursor.execute("SELECT id FROM manifestation").fetchall()]
actors = [id[0] for id in cursor.execute("SELECT id FROM actor").fetchall()]
mimetypes = [id[0] for id in cursor.execute("SELECT id FROM mimetype").fetchall()]
texts = [id[0] for id in cursor.execute("SELECT id FROM text").fetchall()]
storages = [id[0] for id in cursor.execute("SELECT id FROM storage").fetchall()]
payloads = [id[0] for id in cursor.execute("SELECT id FROM payload").fetchall()]
events = [event for event in cursor.execute("SELECT * FROM event").fetchall()]

f_interpretations = []
f_manifestations = []
f_actors = []
f_payloads = []
f_uris = []
f_origin = []
f_subject_interpretations = []
f_subject_manifestations = []
f_mimetypes = []
f_texts = []
f_storages = []

for event in events:
    if not event[2] in interpretations and event[2]:
        f_interpretations.append(event[2])
    if not event[3] in manifestations and event[3]:
        f_manifestations.append(event[3])
    if not event[4] in actors and event[4]:
        f_actors.append(event[4])
    if not event[5] in payloads and event[5]:
        f_payloads.append(event[5])
    if not event[6] in uris and event[6]:
        f_uris.append(event[6])
    if not event[7] in interpretations and events[7]:
        f_subject_interpretations.append(event[7])
    if not event[8] in manifestations and event[8]:
        f_subject_manifestations.append(event[8])
    if not event[9] in uris and event[9]:
        f_origin.append(event[9])
    if not event[10] in mimetypes and event[10]:
        f_mimetypes.append(event[10])
    if not event[11] in texts and event[11]:
        f_texts.append(event[11])
    if not event[12] in storages and event[12]:
        f_storages.append(event[12])

print "broken event interpretation ", list(set(f_interpretations))
print "broken event_manifestation ", list(set(f_manifestations))
print "broken event actors ", list(set(f_actors))
print "broken event payloads ", list(set(f_payloads))
print "broken subject uris ", list(set(f_uris))
print "broken subject interpretations ", list(set(f_subject_interpretations))
print "broken subject manifestations ", list(set(f_subject_manifestations))
print "broken subject origin ", list(set(f_origin))
print "broken subject mimetypes ", list(set(f_mimetypes))
print "broken subject texts ", list(set(f_texts))
print "broken subject storages ", list(set(f_storages))









