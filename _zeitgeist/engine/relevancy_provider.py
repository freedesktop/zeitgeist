# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Seif Lotfy <seif@lotfy.com>
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

import sys
import sqlite3
import time
import os
import logging
from xdg import BaseDirectory

from dbutils import *
from __init__ import DB_PATH

class FocusSwitchRegister(object):
    
    def __init__(self, cursor):
        self.last_app = -1
        self.last_doc = -1
        self.last_timestamp = -1
        self.cursor = cursor
        
        self._create_db()
        
    def _create_db(self):
        """Create the database and return a default cursor for it"""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS focus_switch
            (timestamp REAL, from_actor_id INTEGER, from_subj_id INTEGER, to_actor_id, to_subj_id)
            """)
    
    def focus_change(self, timestamp, app, doc):
        
        self.cursor.execute("""
            INSERT INTO focus_switch VALUES (?,
                (SELECT id FROM actor WHERE value=?),
                (SELECT id FROM uri WHERE value=?),
                (SELECT id FROM actor WHERE value=?),
                (SELECT id FROM uri WHERE value=?))
            """, (timestamp, self.last_app, self.last_doc, app, doc)
            )
        
        self.last_app = app
        self.last_doc = doc
        self.last_timestamp = timestamp
        self.cursor.connection.commit()
        
    def get_relevant_subjects(self, uri, min_timestamp=0, max_timestamp=sys.maxint, limit=10):
        rel = self.cursor.execute("""
            SELECT (SELECT value FROM uri WHERE id=from_subj_id) FROM focus_switch
                WHERE to_subj_id = (SELECT id FROM uri WHERE value=?) 
                AND timestamp >= ? 
                AND timestamp <=? 
                AND from_subj_id != -1
            UNION ALL 
            SELECT (SELECT value FROM uri WHERE id=to_subj_id) FROM focus_switch 
                WHERE from_subj_id = (SELECT id FROM uri WHERE value=?) 
                AND timestamp >= ? 
                AND timestamp <=? 
                AND to_subj_id != -1
            """, (uri, min_timestamp, max_timestamp, uri, min_timestamp, max_timestamp)
            ).fetchall()
        
        result = {}
        for (x,) in rel:
            if not result.has_key(x):
                result[x] = 0
            result[x] +=1
        
        results = [(v, k) for (k, v) in result.iteritems()]
        results.sort()
        results.reverse()
        results = [k[1] for k in results]
            
        return results[:limit]
    
    def get_most_focused_to_subjects(self, uri, min_timestamp=0, max_timestamp=sys.maxint, limit=100):
       rel = self.cursor.execute("""
            SELECT (SELECT value FROM uri WHERE id=from_subj_id) FROM focus_switch
                WHERE to_subj_id = (SELECT id FROM uri WHERE value=?) 
                AND timestamp >= ? 
                AND timestamp <=? 
                AND from_subj_id != -1
            """, (uri, min_timestamp, max_timestamp)
            ).fetchall()
        
       result = {}
       for (x,) in rel:
            if not result.has_key(x):
                result[x] = 0
            result[x] +=1
        
       results = [(v, k) for (k, v) in result.iteritems()]
       results.sort()
       results.reverse()
       results = [k[1] for k in results]
           
       return results[:limit]
    
    
    def get_most_focused_from_subject(self, uri, min_timestamp=0, max_timestamp=sys.maxint, limit=100):
        rel = self.cursor.execute("""
            SELECT (SELECT value FROM uri WHERE id=to_subj_id) FROM focus_switch
                WHERE from_subj_id = (SELECT id FROM uri WHERE value=?) 
                AND timestamp >= ? 
                AND timestamp <=? 
                AND to_subj_id != -1
            """, (uri, min_timestamp, max_timestamp)
            ).fetchall()
            
        
        result = {}
        for (x,) in rel:
            if not result.has_key(x):
                result[x] = 0
            result[x] +=1
        
        results = [(v, k) for (k, v) in result.iteritems()]
        results.sort()
        results.reverse()
        results = [k[1] for k in results]
           
        return results[:limit]
    
    
    def clear_table(self): 
        self.cursor.execute("""
            DELETE FROM focus_switch
            """)
        self.cursor.connection.commit()

class FocusDurationRegister():
    """
    """
    
    def __init__(self, cursor):
        self.lastrowid = 0
        self.cursor = cursor
        self._create_db()
        self.doc_table.set_cursor(self.cursor)
        self.app_table.set_cursor(self.cursor)
    
    def _create_db(self):
        """Create the database and return a default cursor for it"""
        dbfile = DB_PATH
        #log.info("Creating database: %s" % file_path)
        conn = sqlite3.connect(dbfile)
        conn.row_factory = sqlite3.Row
        self.cursor = conn.cursor()
        # focus duration
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS focus_duration
            (subject INTEGER,
            actor INTEGER,
            focus_in REAL, 
            focus_out REAL,
            CONSTRAINT unique_event UNIQUE (subject, actor, focus_in, focus_out))""")
        
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS focus_duration_subject
            ON focus_duration(subject)""")
    
    def focus_change(self, now, document, application):
        doc_id = self.doc_table.lookup_or_create(document)
        app_id = self.app_table.lookup_or_create(application)
        if self.cursor.lastrowid:
            self.cursor.execute("""
                        UPDATE focus_duration 
                        SET focus_out = ?
                        WHERE ROWID = ?""", (str(now), str(self.lastrowid)))
        if not document:
            self.cursor.execute("""
                        INSERT INTO focus_duration 
                        VALUES (?,?,?,?) """, (str(app_id), str(doc_id), str(now), str(now)))
            self.lastrowid = self.cursor.lastrowid
        self.cursor.connection.commit()
    
    def get_subject_focus_duration(self, document, start, end):
        doc_id = self.doc_table.lookup_or_create(document)
        self.cursor.execute("""
                        SELECT SUM(focus_out) - SUM(focus_in) AS DIFF FROM focus_duration
                        WHERE subject_id = ? AND focus_in > start AND focus_out < end
                        """, (str(doc_id)))
        for row in self.cursor:
            return row[0]

    def get_actor_focus_duration(self, application, start, end):
        app_id = self.app_table.lookup_or_create(application)
        self.cursor.execute("""
                        SELECT SUM(focus_out) - SUM(focus_in) AS DIFF FROM focus_duration
                        WHERE application_id = ? AND focus_in > start AND focus_out < end
                        """, (str(app_id)))
        for row in self.cursor:
            return row[0]

    def get_longest_used_subjects(self, num, start, end):
        doc_id = self.doc_table.lookup_or_create(document)
        self.cursor.execute("""
            SELECT subject,
                SUM(focus_out) - SUM(focus_in) AS diff
            FROM focus_duration
            WHERE focus_in > start AND focus_out < end
            GROUP BY subject
            ORDER BY diff DESC
            """)
        docs = []
        for row in self.cursor:
            docs.append(self.doc_table.lookup_by_id(row[0]))
        return docs
    
    def get_longest_used_actors(self, num, start, end):
        app_id = self.app_table.lookup_or_create(application)
        self.cursor.execute("""
            SELECT actor, SUM(focus_out) - SUM(focus_in) AS diff
            FROM focus_duration
            WHERE focus_in > start AND focus_out < end
            GROUP BY actor
            ORDER BY diff
            """)
        apps = []
        for row in self.cursor:
            apps.append(self.app_table.lookup_by_id(row[0]))
        return apps
