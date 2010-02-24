#! /usr/bin/env python
# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2010 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
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

import sqlite3
import optparse

from zeitgeist import _config
_config.setup_path()

from zeitgeist.client import ZeitgeistDBusInterface
from _zeitgeist.engine.sql import get_default_cursor

# For --version and --help
parser = optparse.OptionParser(version = _config.VERSION)
about_text = optparse.OptionGroup(parser, "About this command",
    "This will update the \"actor\" entries in Zeitgeist's database "
    "to the new format, delete bogus data, optimize the database on disk "
    "(vacuum), etc. If Zeitgeist is running when this command is executed, "
    "it will be stopped first.")
parser.add_option_group(about_text)
(_config.options, _config.arguments) = parser.parse_args()

print "Attempting to end any running Zeitgeist instances..."
try:
    # TODO: Add a method to zeitgeist.client to check whether Zeitgeist is
    # running, so that we don't start it (and quit again) here when it isn't
    # already running.
    client = ZeitgeistDBusInterface()
    client.Quit()
except RuntimeError:
    pass

print "Connecting to Zeitgeist's database..."
cursor = get_default_cursor()

# TODO: Implement this, once we have cascade deletion in the database
#print "Deleting any bogus events created by test cases..."
#cursor.execute("DELETE FROM event  id FROM actor WHERE value LIKE 'actor%'")

print "Fetching old-style actor entries...",
i = 0
for i, row in enumerate(cursor.execute(
    "SELECT * FROM actor WHERE value LIKE '/usr/%'").fetchall()):
    value = "application://%s" % row[1].split('/')[-1]
    try:
        cursor.execute("UPDATE actor SET value=? WHERE id=?", (value, row[0]))
    except sqlite3.IntegrityError:
        # The correct actor already exists, update references to point to it.
        cursor.execute("""
            UPDATE OR IGNORE event
                SET actor=(SELECT id FROM actor WHERE value=?)
                WHERE actor=?
            """, (value, row[0]))
        # If there are any duplicate entries they will remain unchanged and
        # we can now delete them.
        cursor.execute("DELETE FROM event WHERE actor=?", (row[0],))
        # Finally, we can delete the old actor.
        cursor.execute("DELETE FROM actor WHERE id=?", (row[0],))
print "Updated %d entries." % i

print "Optimizing database (VACUUM)..."
cursor.execute("VACUUM")
