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
            (timestamp INTEGER, from_app_id INTEGER, from_doc_id INTEGER, to_app_id, to_doc_id)
            """)
    
    def insert_focus(self, timestamp, app, doc):
        
        self.cursor.execute("""
            INSERT INTO focus_switch VALUES (?,
                (SELECT item_id FROM app WHERE info=?),
                (SELECT id FROM uri WHERE value=?),
                (SELECT item_id FROM app WHERE info=?),
                (SELECT id FROM uri WHERE value=?))
            """, (timestamp, self.last_app, self.last_doc, app, doc)
            )
        
        self.last_app = app
        self.last_doc = doc
        self.last_timestamp = timestamp
        self.cursor.connection.commit()
        
    def get_relevant_items_to_item(self, uri, min_timestamp=0, max_timestamp=sys.maxint, limit=10):
        rel = self.cursor.execute("""
            SELECT (SELECT value FROM uri WHERE id=from_doc_id) FROM focus_switch
                WHERE to_doc_id = (SELECT id FROM uri WHERE value=?) 
                AND timestamp >= ? 
                AND timestamp <=? 
                AND from_doc_id != -1
            UNION ALL 
            SELECT (SELECT value FROM uri WHERE id=to_doc_id) FROM focus_switch 
                WHERE from_doc_id = (SELECT id FROM uri WHERE value=?) 
                AND timestamp >= ? 
                AND timestamp <=? 
                AND to_doc_id != -1
            """, (uri, min_timestamp, max_timestamp, uri, min_timestamp, max_timestamp)
            ).fetchall()
        
        result = {}
        for (x,) in rel:
            #print x
            if not result.has_key(x):
                result[x] = 0
            result[x] +=1
        
        results = [(v, k) for (k, v) in result.iteritems()]
        results.sort()
        results.reverse()
        results = [k[1] for k in results]
            
        return results[:limit]
    
    def get_focused_to_items(self, uri, min_timestamp=0, max_timestamp=sys.maxint, limit=100):
       rel = self.cursor.execute("""
            SELECT (SELECT value FROM uri WHERE id=from_doc_id) FROM focus_switch
                WHERE to_doc_id = (SELECT id FROM uri WHERE value=?) 
                AND timestamp >= ? 
                AND timestamp <=? 
                AND from_doc_id != -1
            """, (uri, min_timestamp, max_timestamp)
            ).fetchall()
        
       result = {}
       for (x,) in rel:
            #print x
            if not result.has_key(x):
                result[x] = 0
            result[x] +=1
        
       results = [(v, k) for (k, v) in result.iteritems()]
       results.sort()
       results.reverse()
       results = [k[1] for k in results]
           
       return results[:limit]
    
    
    def get_focused_from_items(self, uri, min_timestamp=0, max_timestamp=sys.maxint, limit=100):
        rel = self.cursor.execute("""
            SELECT (SELECT value FROM uri WHERE id=to_doc_id) FROM focus_switch
                WHERE from_doc_id = (SELECT id FROM uri WHERE value=?) 
                AND timestamp >= ? 
                AND timestamp <=? 
                AND to_doc_id != -1
            """, (uri, min_timestamp, max_timestamp)
            ).fetchall()
            
        
        result = {}
        for (x,) in rel:
            #print x
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
        self.doc_table = EntityTable("uri")
        self.app_table = EntityTable("actor")
        self.cursor = cursor
        self._create_db()
        self.doc_table.set_cursor(self.cursor)
        self.app_table.set_cursor(self.cursor)

    def _create_db(self):
        """Create the database and return a default cursor for it"""
        # focus duration
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS focus_duration
            (document_id INTEGER,
            application_id INTEGER,
            focus_in INTEGER, 
            focus_out INTEGER,
            CONSTRAINT unique_event UNIQUE (document_id, application_id, focus_in, focus_out))""")
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS focus_duration_document_id
            ON focus_duration(document_id)""")
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS focus_duration_application_id
            ON focus_duration(application_id)""")


    def focus_change(self, now, document, application):
        doc_id = self.doc_table.lookup_or_create(document)
        app_id = self.app_table.lookup_or_create(application)
        
        if not self.cursor.lastrowid is None:
            self.cursor.execute("""
                        UPDATE focus_duration 
                        SET focus_out = ?
                        WHERE ROWID = ?""", (str(now), str(self.lastrowid)))
        if not document == "":
            self.cursor.execute("""
                        INSERT INTO focus_duration 
                        VALUES (?,?,?,?) """, (str(app_id), str(doc_id), str(now), str(now)))
            self.lastrowid = self.cursor.lastrowid
        self.cursor.connection.commit()
    
    def get_document_focus_duration(self, document, start, end):
        doc_id = self.doc_table.lookup_or_create(document)
        self.cursor.execute("""
                        SELECT SUM(focus_out) - SUM(focus_in) AS DIFF FROM focus_duration
                        WHERE document_id = ? AND focus_in > start AND focus_out < end
                        """, (str(doc_id)))
        for row in self.cursor:
            return row[0]

    def get_application_focus_duration(self, application, start, end):
        app_id = self.app_table.lookup_or_create(application)
        self.cursor.execute("""
                        SELECT SUM(focus_out) - SUM(focus_in) AS DIFF FROM focus_duration
                        WHERE application_id = ? AND focus_in > start AND focus_out < end
                        """, (str(app_id)))
        for row in self.cursor:
            return row[0]

    def get_longest_used_documents(self, num, start, end):
        doc_id = self.doc_table.lookup_or_create(document)
        self.cursor.execute("""
                        SELECT document_id, SUM(focus_out) - SUM(focus_in) AS DIFF FROM focus_duration
                        WHERE focus_in > start AND focus_out < end
                        GROUP BY document_id
                        ORDER BY DIFF
                        """)
        docs = []
        for row in self.cursor:
            docs.append(self.doc_table.lookup_by_id(row[0]))
        return docs
            

    def get_longest_used_applications(self, num, start, end):
        app_id = self.app_table.lookup_or_create(application)
        self.cursor.execute("""
                        SELECT application_id, SUM(focus_out) - SUM(focus_in) AS DIFF FROM focus_duration
                        WHERE focus_in > start AND focus_out < end
                        GROUP BY application_id
                        ORDER BY DIFF
                        """)
        apps = []
        for row in self.cursor:
            apps.append(self.app_table.lookup_by_id(row[0]))
        return apps


if __name__=="__main__":
    ################
    fvr = FocusVertexRegister()
    fvr.clear_table()
    
    app = "/usr/share/applications/firefox.desktop"
    
    doc1 = "file:///home/seif/Downloads/eise_aufgabenblatt_01.pdf"
    doc2 = "http://www.facebook.com/home.php?"
    doc4 = "http://www.grillbar.org.com/"
    doc8 = "http://www.sqlite.org/lang.html"
    
    fvr.insert_focus(time.time(), app, doc1)
    fvr.insert_focus(time.time(), app, doc2)
    fvr.insert_focus(time.time(), app, doc4)
    fvr.insert_focus(time.time(), app, doc8)
    fvr.insert_focus(time.time(), app, doc2)
    fvr.insert_focus(time.time(), app, doc1)
    fvr.insert_focus(time.time(), app, doc2)
    
   # result = fvr.get_relevant_items_to_item(doc2)
    result = fvr.get_focused_to_items(doc2)
    result = fvr.get_focused_from_items(doc2)
    print result
