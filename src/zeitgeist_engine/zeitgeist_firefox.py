# -.- encoding: utf-8 -.-

import os
import glob
import shutil
import sqlite3 as db
import gettext

from os.path import join, expanduser, isfile
from ConfigParser import ConfigParser, NoOptionError

from zeitgeist_engine.zeitgeist_util import FileMonitor
from zeitgeist_engine.zeitgeist_base import DataProvider

class FirefoxSource(DataProvider):
    FIREFOX_DIR = expanduser("~/.mozilla/firefox")
    PROFILE_FILE = join(FIREFOX_DIR, "profiles.ini")
    
    def __init__(self, name="Firefox History", icon="gnome-globe", uri="gzg/firefox"):
        
        DataProvider.__init__(self, name=name, icon=icon, uri = uri)
        self.name = "Firefox History"
        self.icon="gnome-globe"
        self.type = self.name
        self.comment = "websites visited with Firefox"
        
        # Holds a list of all places.sqlite files.
        self.historydb = []
        
        # Parse the profiles.ini file to get the location of all Firefox
        # profiles.
        profile_parser = ConfigParser()
        profile_parser.read(self.PROFILE_FILE)
        
        for section in profile_parser.sections():
            try:
                is_relative = profile_parser.getboolean(section, "isRelative")
                path = profile_parser.get(section, "Path")
            except NoOptionError:
                # This section does not represent a profile (for example the
                # `General` section).
                pass
            else:
                if is_relative:
                    path = join(self.FIREFOX_DIR, path)
                
                places_db = join(path, "places.sqlite")
                
                if isfile(places_db):
                    self.historydb.append(places_db)
        
        # TODO: Be more sensible about: a) old profiles being present
        # (look at profiles.ini to find the correct one), and b) more
        # than one Firefox version being used (eg., current and alpha).
        try:
            self.note_path_monitor = FileMonitor(self.historydb[0])
            self.note_path_monitor.connect("event", self.reload_proxy)
            self.note_path_monitor.open()
        except Exception:
            print "Are you using Firefox?"
        else:
            print 'Reading from', self.historydb[0]
        
        if not hasattr(self, "cursor"):
            self.cursor = None
        if self.cursor:
            self.last_timestamp = self.get_latest_timestamp()
        else:
            self.last_timestamp = 0.0
        
        self.loc = os.path.expanduser("~/.zeitgeist/firefox.sqlite")
        
        self.__copy_sqlite()
    
    def get_latest_timestamp(self): 
        
        contents = "visit_date"
        try:
            history = self.cursor.execute("SELECT " + contents + " FROM moz_historyvisits ORDER BY visit_date DESC").fetchone()
        except db.OperationalError, e:
            raise
        else:
            self.timestamp = history[0]
    
    def reload_proxy(self,x=None,y=None,z=None):
        self.__copy_sqlite()
        self.emit("reload")
    
    def get_items_uncached(self):
        # create a connection to firefox's sqlite database
        
        # retrieve all urls from firefox history
        contents = "id, place_id, visit_date,visit_type"
        try:
            history = self.cursor.execute("SELECT " + contents + " FROM moz_historyvisits WHERE visit_date>?",(self.last_timestamp,)).fetchall()
        except db.OperationalError, e:
            print "Firefox database error:", e
        else:
            for j, i in enumerate(history):
                # TODO: Fetch full rows above so that we don't need to do another query here
                contents = "id, url, title, visit_count, rev_host"
                item = self.cursor.execute("SELECT " + contents + " FROM moz_places WHERE title!='' and id=" + str(i[1])).fetchone()
                if item:
                    self.last_timestamp = history[j][2]
                    use = "linked"
                    if history[j][3] in (2, 3, 5):
                        use = "visited"
                    item = {
                        "timestamp": int(self.last_timestamp / (1000000)),
                        "uri": unicode(item[1]),
                        "name": unicode(item[2]),
                        "comment": unicode(item[4][::-1] if item[4] else u""),
                        "type": u"Firefox History",
                        "count": item[3],
                        "use": unicode(use),
                        "mimetype": u"", # TODO: Can we get a mime-type here?
                        "tags": u"",
                        "icon": u"gnome-globe"
                        }
                    yield item
    
    def __copy_sqlite(self):
        '''
        Copy the sqlite file to avoid file locks when it's being used by Firefox.
        '''
        if self.cursor:
            self.cursor.close()
        shutil.copy2(self.historydb[0],  self.loc)
        self.connection = db.connect(self.loc, True)
        self.cursor = self.connection.cursor()
