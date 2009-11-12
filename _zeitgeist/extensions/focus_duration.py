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
from _zeitgeist.engine.dbutils import EntityTable

class FocusDurationRegister():
	"""
	"""
	
	def __init__(self):
		self.lastrowid = 0
		self.doc_table = EntityTable("uri")
		self.app_table = EntityTable("actor")
	
	def create_db(self):
		conn = sqlite3.connect(DB_PATH)
		conn.row_factory = sqlite3.Row
		cursor = conn.cursor()
		cursor.execute("""
			CREATE TABLE IF NOT EXISTS focus_duration
			(document_id INTEGER,
			application_id INTEGER,
			focus_in INTEGER, 
			focus_out INTEGER,
			CONSTRAINT unique_event UNIQUE (document_id, application_id, focus_in, focus_out))""")
		cursor.execute("""
			CREATE INDEX IF NOT EXISTS focus_duration_document_id
			ON focus_duration(document_id)""")
		cursor.execute("""
			CREATE INDEX IF NOT EXISTS focus_duration_application_id
			ON focus_duration(application_id)""")
		self.doc_table.set_cursor(cursor)
		self.app_table.set_cursor(cursor)

	def focus_change(self, document, application):
		doc_id = self.app_table.lookup_or_create(document)
		app_id = self.doc_table.lookup_or_create(application)
		now = time()
		if not cursor.lastrowid is None:
			cursor.execute("""
						UPDATE focus_duration 
						SET focus_out = ?
						WHERE ROWID = ?""", (now, self.lastrowid))
		if not document == "":
			cursor.execute("""
						INSERT INTO focus_duration 
						VALUES (?,?,?,?) """, (app_id, doc_id, now, now))
			self.lastrowid = cursor.lastrowid
	
	def get_document_focus_duration(self, document, start, end):

		doc_id = self.doc_table.lookup_or_create(document)
		cursor.execute("""
						SELECT SUM(focus_out) - SUM(focus_in) AS DIFF FROM focus_duration
						WHERE document_id = ? AND focus_in > start AND focus_out < end
						""", (str(doc_id)))
		for row in cursor:
			return row[0]

	def get_application_focus_duration(self, application, start, end):
		app_id = self.app_table.lookup_or_create(application)
		cursor.execute("""
						SELECT SUM(focus_out) - SUM(focus_in) AS DIFF FROM focus_duration
						WHERE application_id = ? AND focus_in > start AND focus_out < end
						""", (str(app_id)))
		for row in cursor:
			return row[0]

	def get_longest_used_documents(self, num, start, end):
		doc_id = self.doc_table.lookup_or_create(document)
		cursor.execute("""
						SELECT document_id, SUM(focus_out) - SUM(focus_in) AS DIFF FROM focus_duration
						WHERE focus_in > start AND focus_out < end
						GROUP BY document_id
						ORDER BY DIFF
						""")
		docs = []
		for row in cursor:
			docs.append(self.doc_table.lookup_by_id(row[0]))
		return docs
			

	def get_longest_used_applications(self, num, start, end):
		app_id = self.app_table.lookup_or_create(application)
		cursor.execute("""
						SELECT application_id, SUM(focus_out) - SUM(focus_in) AS DIFF FROM focus_duration
						WHERE focus_in > start AND focus_out < end
						GROUP BY application_id
						ORDER BY DIFF
						""")
		apps = []
		for row in cursor:
			apps.append(self.app_table.lookup_by_id(row[0]))
		return apps
