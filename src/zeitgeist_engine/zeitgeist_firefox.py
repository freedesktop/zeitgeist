import os
import glob
import shutil
import sqlite3 as db
from gettext import gettext as _

from zeitgeist_engine.zeitgeist_util import FileMonitor
from zeitgeist_engine.zeitgeist_base import DataProvider


class FirefoxSource(DataProvider):
    
    def __init__(self, name="Firefox History", icon="gnome-globe", uri="gzg/firefox"):
        DataProvider.__init__(self, name=name, icon=icon, uri = uri)
        self.name = "Firefox History"
        self.icon="gnome-globe"
        self.type = self.name
        self.comment = "websites visited with Firefox"
        
        self.historydb = glob.glob(os.path.expanduser("~/.mozilla/firefox/*/places.sqlite"))
        
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
        
        try:
            self.last_timestamp = self.get_latest_timestamp()
        except Exception,ex:
            print ex
            self.last_timestamp = 0.0
            
        try:
            self.loc = glob.glob(os.path.expanduser("~/.zeitgeist/"))
            self.loc = self.loc[0] + "firefox.sqlite"
        except:
            pass
            
        self.__copy_sqlite()
    
    def get_latest_timestamp(self): 
        
        contents = "visit_date"
        try:
            history = self.cursor.execute("SELECT " + contents + " FROM moz_historyvisits ORDER BY visit_date DESC").fetchone()
        except db.OperationalError, e:
            print e
        else:
            self.timestamp=history[0]
    
    def reload_proxy(self,x=None,y=None,z=None):
        self.__copy_sqlite()
        self.emit("reload")
    
    def get_items_uncached(self):
        try:
            # create a connection to firefox's sqlite database
            
            # retrieve all urls from firefox history
            contents = "id, place_id, visit_date,visit_type"
            try:
                history = self.cursor.execute("SELECT " + contents + " FROM moz_historyvisits WHERE visit_date>?",(self.last_timestamp,)).fetchall()
            except db.OperationalError, e:
                print 'Firefox database error:', e
            else:
                j = 0
                for i in history:
                    # TODO: Fetch full rows above so that we don't need to do another query here
                    contents = "id, url, title, visit_count"
                    item = self.cursor.execute("SELECT " + contents +" FROM moz_places WHERE title!='' and id=" +str(i[1])).fetchone()
                    if item:
                        self.last_timestamp =  history[j][2]
                        use = "linked"
                        if history[j][3]==2 or history[j][3]==3 or history[j][3]==5:
                            use = "visited"
                        item = {
                            "timestamp": int(	self.last_timestamp / (1000000)),
                            "uri": item[1],
                            "name": item[2],
                            "comment": "",
                            "type": "Firefox History",
                            "count": item[3],
                            "use": use,
                            "mimetype": "",
                            "tags": "",
                            "icon": "gnome-globe"
                            }
                        yield item
                    j += 1
        except Excpetion, ex:
            print ex
    
    def __copy_sqlite(self):
        '''
        Copy the sqlite file to avoid file locks when it's being used by firefox.
        '''
        try:
        	try: 
        		self.cursor.close()
        	except:
        	 	pass
        	shutil.copy2(self.historydb[0],  self.loc)
        	self.connection = db.connect(self.loc, True)
        	self.cursor = self.connection.cursor()
        except:
            pass
