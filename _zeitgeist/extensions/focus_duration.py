# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Alexander Gabriel <einalex@mayanna.org>

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
from time import time

from _zeitgeist.engine import DB_PATH


class FocusDurationRegister():
	"""
	"""
	
	def __init__(self):
		self.lastrowid = 0
	
	def create_db(self):
		conn = sqlite3.connect(DB_PATH)
		conn.row_factory = sqlite3.Row
		cursor = conn.cursor()
		cursor.execute("""
			CREATE TABLE IF NOT EXISTS focus_duration
			(document_id INTEGER, 
			focus_in INTEGER, 
			focus_out INTEGER,
			CONSTRAINT unique_event UNIQUE (document_id, focus_in, focus_out))""")
		cursor.execute("""
			CREATE INDEX IF NOT EXISTS focus_duration_document_id
			ON focus_duration(document_id)""")

	def focus_change(self, document):
		now = time()
		if not cursor.lastrowid is None:
			cursor.execute("""
						UPDATE focus_duration 
						SET focus_out = ?
						WHERE ROWID = ?""", (now, self.lastrowid))
		if not document == "":
			cursor.execute("""
						INSERT INTO focus_duration 
						VALUES (?,?,?) """, (document, now, now))
			self.lastrowid = cursor.lastrowid
	
	def get_focus_duration(self, document, start, end):
		cursor.execute("""
						SELECT SUM(focus_in), SUM(focus_out) FROM focus_duration
						WHERE document_id = ? AND focus_in > start AND focus_out < end
						""", (str(document)))
		for row in cursor:
			return row[1] - row[0]
	