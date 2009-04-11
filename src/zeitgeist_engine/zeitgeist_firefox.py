import os
import glob
import shutil
import sqlite3 as db
from gettext import gettext as _

from zeitgeist_util import FileMonitor
from zeitgeist_base import Data, DataProvider


class FirefoxSource(DataProvider):
	
	def __init__(self, name="Firefox History", icon="gnome-globe", uri="gzg/firefox"):
		DataProvider.__init__(self, name=name, icon=icon, uri = uri)
		self.name = "Firefox History"
		self.icon="gnome-globe"
		self.type = self.name
		self.comment = "websites visited with Firefox"
		
		mozpath = os.path.expanduser("~/.mozilla/firefox/")
		historydbs = glob.glob(os.path.join(mozpath, "*/places.sqlite"))
		
		self.historydb = None
		if len(historydbs) == 1:
			self.historydb = historydbs[0]
		elif len(historydbs) > 1:
			# Determine which Firefox profile is the default one
			profiles_file = os.path.join(mozpath, "profiles.ini")
			if os.path.isfile(profiles_file):
				from ConfigParser import SafeConfigParser
				profiles = SafeConfigParser()
				profiles.readfp(open(profiles_file))
				for section in profiles.sections():
					if profiles.has_option(section, "Default") and profiles.has_option(section, "Path"):
						if profiles.get_boolean(section, "Default"):
							path = os.path.normpath(os.path.join(mozpath, profiles.get(section, "Path"), "places.sqlite"))
							if path in historydbs:
								self.historydb = path
								break
		
		print "===>>>Firefox: Reading from %s" % self.historydb
		
		if self.historydb:
			self.note_path_monitor = FileMonitor(self.historydb)
			self.note_path_monitor.connect("event", self.reload_proxy)
			self.note_path_monitor.open()
		
		try:
			self.loc = glob.glob(os.path.expanduser("~/.Zeitgeist/"))
			self.loc = self.loc[0] + "firefox.sqlite"
		except Exception:
			pass
		
		try:
			self.last_timestamp = self.get_latest_timestamp()
		except Exception,ex:
			print ex
			self.last_timestamp = 0.0
	
	def get_latest_timestamp(self): 
		self.connection = db.connect(self.loc, True)
		cursor = self.connection.cursor()
		
		contents = "visit_date"
		try:
			history = cursor.execute("SELECT " + contents + " FROM moz_historyvisits ORDER BY visit_date DESC").fetchone()
		except db.OperationalError, e:
			print e
		else:
			self.timestamp=history[0]
	
	def reload_proxy(self,x=None,y=None,z=None):
		self.__copy_sqlite()
		self.emit("reload")
	
	def get_items_uncached(self):
		# create a connection to firefox's sqlite database
		self.connection = db.connect( self.loc,True)
		cursor = self.connection.cursor()
		
		# retrieve all urls from firefox history
		contents = "id, place_id, visit_date,visit_type"
		try:
			history = cursor.execute("SELECT " + contents + " FROM moz_historyvisits WHERE visit_date>?",(self.timestamp,)).fetchall()
		except db.OperationalError, e:
			print 'Firefox database error:', e
		else:
			j = 0
			for i in history:
				# TODO: Fetch full rows above so that we don't need to do another query here
				contents = "id, url, title, visit_count"
				item = cursor.execute("SELECT " + contents +" FROM moz_places WHERE title!='' and id=" +str(i[1])).fetchone()
				if item:
					url = item[1]
					name = item[2]
					count = item[3]
					timestamp = history[j][2] / (1000000)
					self.timestamp =  history[j][2]
					if history[j][3]==2 or history[j][3]==3 or history[j][3]==5:
						yield Data(uri=url,
							name=name,
							timestamp=timestamp,
							count=count,
							icon = "gnome-globe",
							use="visited",
							type="Firefox History")
					else:
						yield Data(uri=url,
							name=name,
							timestamp=timestamp,
							icon = "gnome-globe",
							count=count,
							use="linked",
							type="Firefox History")
				j += 1
			
		cursor.close()
    
	def __copy_sqlite(self):
		'''
		Copy the sqlite file to avoid file locks when it's being used by firefox.
		'''
		try:
			shutil.copy2(self.historydb[0],  self.loc)
		except:
			pass
