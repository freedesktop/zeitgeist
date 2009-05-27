# -.- encoding: utf-8 -.-

import os.path
import shutil
import sqlite3 as db
import gettext
from ConfigParser import ConfigParser, NoOptionError
from xdg import BaseDirectory

from zeitgeist.loggers.zeitgeist_base import DataProvider
from zeitgeist.loggers.util import FileMonitor

class FirefoxSource(DataProvider):
    
    FIREFOX_DIR = os.path.expanduser("~/.mozilla/firefox")
    PROFILE_FILE = os.path.join(FIREFOX_DIR, "profiles.ini")
    PATH = os.path.join(BaseDirectory.xdg_cache_home, "zeitgeist")
    LOCATION = os.path.join(PATH, "firefox.sqlite")
    
    def __init__(self):
        DataProvider.__init__(self,
            name=_(u"Firefox History"),
            icon="gnome-globe",
            uri="gzg/firefox",
            comment=_(u"Websites visited with Firefox"))
        
        self.type = "Firefox History"
        
        # Holds a list of all places.sqlite files. The file that belongs to the
        # default profile will be the at the top of the list.
        self.history_dbs = []
        
        # The places.sqlite file monitored by Zeitgeist.
        # TODO: Handle multiple Firefox profiles.
        self.history_db = ""
        
        for profile_dir in self.get_profile_dirs():
            db_file = os.path.join(profile_dir, "places.sqlite")
            
            # Make sure that this particular places.sqlite file exists.
            if os.path.isfile(db_file):
                self.history_dbs.append(db_file)
        
        if self.history_dbs:
            self.history_db = self.history_dbs[0]
            
            try:
                note_path_monitor = FileMonitor(self.history_db)
                note_path_monitor.connect("event", self.reload_proxy)
                note_path_monitor.open()
            except Exception, e:
                print("Unable to monitor Firefox history %s: %s" % 
                    (self.history_db, str(e)))
            else:
                print("Monitoring Firefox history: %s" % (self.history_db))
                
                if not hasattr(self, "cursor"):
                    self.cursor = None
                
                if self.cursor:
                    self.last_timestamp = self.get_latest_timestamp()
                else:
                    self.last_timestamp = 0.0
                
                self.__copy_sqlite()
        else:
            print("No Firefox profile found")
    
    @classmethod
    def get_profile_dirs(cls):
        """
        Returns a list of all Firefox profile directories.
        
        The default profile is located at the top of the list.
        """
        
        profiles = []
        
        # Parse the profiles.ini file to get the location of all Firefox
        # profiles.
        profile_parser = ConfigParser()
        
        # Doesn't raise an exception if the file doesn't exist.
        profile_parser.read(cls.PROFILE_FILE)
        
        for section in profile_parser.sections():
            try:
                is_relative = profile_parser.getboolean(section, "isRelative")
                path = profile_parser.get(section, "Path")
            except NoOptionError:
                # This section does not represent a profile (for example the
                # `General` section).
                pass
            else:
                try:
                    is_default = profile_parser.getboolean(section, "Default")
                except (NoOptionError, ValueError):
                    is_default = False
                
                if is_relative:
                    path = os.path.join(cls.FIREFOX_DIR, path)
                
                if is_default:
                    profiles.insert(0, path)
                else:
                    profiles.append(path)
        
        return profiles
    
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
                        "use": unicode(use),
                        "mimetype": u"", # TODO: Can we get a mime-type here?
                        "tags": u"",
                        "icon": u"gnome-globe",
                        "app": u"/usr/share/applications/firefox.desktop",
                        "count": 0
                        }
                    yield item
    
    def __copy_sqlite(self):
        """
        Copy the sqlite file to avoid file locks when it's being used by Firefox.
        """
        if not os.path.isdir(self.PATH):
            os.mkdir(self.PATH)
        if self.cursor:
            self.cursor.close()
        shutil.copy2(self.history_db,  self.LOCATION)
        self.connection = db.connect(self.LOCATION, True)
        self.cursor = self.connection.cursor()

__datasource__ = FirefoxSource()
