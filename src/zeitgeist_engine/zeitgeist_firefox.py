# -.- encoding: utf-8 -.-

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
    LOCATION = expanduser("~/.zeitgeist/firefox.sqlite")
    
    def __init__(self):
        DataProvider.__init__(self,
            name=_(u"Firefox History"),
            icon="gnome-globe",
            uri="gzg/firefox",
            comment=_(u"Websites visited with Firefox"))
        
        self.type = self.name
        
        # Holds a list of all places.sqlite files. The one that belongs to the
        # default one will be the at the top of the list.
        self.historydb = []
        
        for profile_dir in self.get_profile_dirs():
            db_file = join(profile_dir, "places.sqlite")
            
            if isfile(db_file):
                self.historydb.append(db_file)
        
        # TODO: Handle more than one Firefox profile.
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
        
        self.__copy_sqlite()
    
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
                    path = join(cls.FIREFOX_DIR, path)
                
                if is_default:
                    profiles.insert(0, path)
                else:
                    profile.append(path)
        
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
        shutil.copy2(self.historydb[0],  self.LOCATION)
        self.connection = db.connect(self.LOCATION, True)
        self.cursor = self.connection.cursor()
