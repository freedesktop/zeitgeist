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

DB_PATH = os.path.join(BaseDirectory.save_data_path("zeitgeist"),
    "database.sqlite")
 
class FocusVertexRegister(object):
    def __init__(self):
        self.last_app = -1
        self.last_doc = -1
        self.last_timestamp = -1
        self.cursor = None
        
        self._create_db()
        
    def _create_db(self):
        """Create the database and return a default cursor for it"""
        dbfile = DB_PATH
        #log.info("Creating database: %s" % file_path)
        conn = sqlite3.connect(dbfile)
        conn.row_factory = sqlite3.Row
        self.cursor = conn.cursor()
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
        
        return result
    
    def get_focused_to_items(self, uri, min_timestamp=0, max_timestamp=sys.maxint, limit=100):
        rel = self.cursor.execute("""
                SELECT value, COUNT(value) AS focusto FROM uri WHERE id IN (
                    SELECT to_doc_id FROM focus_switch
                        WHERE from_doc_id = (SELECT id FROM uri WHERE value=?) 
                        AND timestamp >= ? 
                        AND timestamp <=? 
                        AND from_doc_id != -1)
                    GROUP BY value
                    ORDER BY focusto DESC LIMIT ?
                """, (uri, min_timestamp, max_timestamp, limit)).fetchall()
                
        result = {}
        for x in rel:
            result[x[0]] = x[1]
        return result
    
    def get_focused_from_items(self, uri, min_timestamp=0, max_timestamp=sys.maxint, limit=100):
        rel = self.cursor.execute("""
                SELECT value, COUNT(value) AS focusfrom FROM uri WHERE id IN (
                    SELECT from_doc_id FROM focus_switch
                        WHERE to_doc_id = (SELECT id FROM uri WHERE value=?) 
                        AND timestamp >= ? 
                        AND timestamp <=? 
                        AND to_doc_id != -1)
                    GROUP BY value
                    ORDER BY focusfrom DESC LIMIT ?
                """, (uri, min_timestamp, max_timestamp, limit)).fetchall()
                
        result = {}
        for x in rel:
            result[x[0]] = x[1]
        return result
        
    
    def clear_table(self): 
        self.cursor.execute("""
            DELETE FROM focus_switch
            """)
        self.cursor.connection.commit()
    
             
         
     
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
    
    result = fvr.get_relevant_items_to_item(doc2)
    print result
    result = fvr.get_focused_to_items(doc2)
    print ""
    print result
    result = fvr.get_focused_from_items(doc2)
    print result
    
    