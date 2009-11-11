
import sqlite3
from time import time

from _zeitgeist.engine import DB_PATH

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
	
	
lastrowid = 0

def focus_change(document):
	global lastrowid
	now = time()
	if not cursor.lastrowid is None:
		cursor.execute("""
					UPDATE focus_duration 
					SET focus_out = ?
					WHERE ROWID = ?""", (now, lastrowid))
	if not document == "":
		cursor.execute("""
					INSERT INTO focus_duration 
					VALUES (?,?,?) """, (document, now, now))
		lastrowid = cursor.lastrowid
					
def get_focus_time(document, start, end):
	cursor.execute("""
					SELECT SUM(focus_in), SUM(focus_out) FROM focus_duration
					WHERE document_id = ? AND focus_in > start AND focus_out < end
					""", (str(document)))
	for row in cursor:
		return row[1] - row[0]
					