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
            INSERT INTO focus_switch VALUES (?,?,?,?,?)
            """,(timestamp, self.last_app, self.last_doc, app, doc)
            )
        
        self.last_app = app
        self.last_doc = doc
        self.cursor.connection.commit()
        
    def get_relevant_items_to_item(self, uri_id, min_timestamp=0, max_timestamp=sys.maxint, limit=10):
        uris = self.cursor.execute("""
            SELECT from_doc_id FROM focus_switch
                WHERE to_doc_id = ? AND timestamp >= ? AND timestamp <=? AND from_doc_id != -1
            UNION ALL SELECT to_doc_id FROM focus_switch 
                WHERE from_doc_id = ? AND timestamp >= ? AND timestamp <=? AND to_doc_id != -1
            """, (uri_id, min_timestamp, max_timestamp, uri_id, min_timestamp, max_timestamp)
            ).fetchall()

        result = {}
        for (uri,) in uris:
            if not result.has_key(str(uri)):
                result[str(uri)] = 0
            result[str(uri)] +=1
            
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
    fvr.insert_focus(time.time(), 0, 1)
    fvr.insert_focus(time.time(), 0, 2)
    fvr.insert_focus(time.time(), 0, 4)
    fvr.insert_focus(time.time(), 0, 8)
    fvr.insert_focus(time.time(), 0, 2)
    fvr.insert_focus(time.time(), 0, 1)
    fvr.insert_focus(time.time(), 0, 2)
    
    
    result = fvr.get_relevant_items_to_item(2)
    print result
    
    