# -.- encoding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Seif Lotfy <seif@lotfy.com>
# Copyright © 2009 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
# Copyright © 2009 Natan Yellin <aantny@gmail.com>
# Copyright © 2009 Markus Korn <thekorn@gmx.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os.path
import shutil
import sqlite3 as db
import gettext
import dbus
import gio
from ConfigParser import ConfigParser, NoOptionError
from xdg import BaseDirectory

from zeitgeist.loggers.zeitgeist_base import DataProvider
from zeitgeist import config

gettext.install("zeitgeist", config.localedir, unicode=1)

class FirefoxSource(DataProvider):
	
	FIREFOX_DIR = os.path.expanduser("~/.mozilla/firefox")
	PROFILE_FILE = os.path.join(FIREFOX_DIR, "profiles.ini")
	PATH = os.path.join(BaseDirectory.xdg_cache_home, "zeitgeist")
	LOCATION = os.path.join(PATH, "firefox.sqlite")
	
	@staticmethod
	def get_last_timestamp():
		# Connect to D-Bus
		bus = dbus.SessionBus()
		try:
			remote_object = bus.get_object("org.gnome.zeitgeist", "/org/gnome/eitgeist")
		except dbus.exceptions.DBusException:
			print >> sys.stderr, "Zeitgeist Logger: Error: Could not connect to D-Bus."
			return 0
		iface = dbus.Interface(remote_object, "org.gnome.zeitgeist")
		return iface.GetLastInsertionDate(u"/usr/share/applications/firefox.desktop")
	
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
		self.cursor = None
		
		for profile_dir in self.get_profile_dirs():
			db_file = os.path.join(profile_dir, "places.sqlite")
			
			# Make sure that this particular places.sqlite file exists.
			if os.path.isfile(db_file):
				self.history_dbs.append(db_file)
		
		if self.history_dbs:
			self.history_db = self.history_dbs[0]
			
			try:
				file_object = gio.File(self.history_db)
				self.note_path_monitor = file_object.monitor_file()
				self.note_path_monitor.connect("changed", self.reload_proxy_filemonitor)
			except Exception, e:
				print("Unable to monitor Firefox history %s: %s" % 
					(self.history_db, str(e)))
			else:
				print("Monitoring Firefox history: %s" % (self.history_db))
				
				self.last_timestamp = self.get_last_timestamp()
				self.__copy_sqlite()
		else:
			print("No Firefox profile found")
		self.config.connect("configured", self.reload_proxy_config)
	
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
	
	def reload_proxy_filemonitor(self, filemonitor, file, other_file, event_type):
		if event_type in (
				gio.FILE_MONITOR_EVENT_CHANGED,
				gio.FILE_MONITOR_EVENT_CREATED,
				gio.FILE_MONITOR_EVENT_DELETED,
				gio.FILE_MONITOR_EVENT_ATTRIBUTE_CHANGED
		):
			self.reload_proxy()
			
	def reload_proxy_config(self, configuration):
		self.reload_proxy()
			
	def reload_proxy(self):
		self.last_timestamp = self.get_last_timestamp()
		self.__copy_sqlite()
		self.emit("reload")
	
	def get_items_uncached(self):
		# create a connection to firefox's sqlite database
		
		# retrieve all urls from firefox history
		contents = "id, place_id, visit_date,visit_type"
		try:
			history = self.cursor.execute(
				"SELECT " + contents + " FROM moz_historyvisits WHERE visit_date>?",
				(self.last_timestamp*1000000,)
			).fetchall()
		except db.OperationalError, e:
			print "Firefox database error:", e
		else:
			for j, i in enumerate(history):
				# TODO: Fetch full rows above so that we don't need to do another query here
				contents = "id, url, title, visit_count, rev_host, favicon_id"
				item = self.cursor.execute("SELECT " + contents + " FROM moz_places WHERE title!='' and id=" + str(i[1])).fetchone()
				if item:
					if item[5]:
						icon = self.cursor.execute("SELECT url FROM moz_favicons WHERE id=" + str(item[5])).fetchone()
						icon = unicode(icon[0])
					else:
						icon = u"gnome-globe"
					
					self.last_timestamp = history[j][2]
					use = "http://gnome.org/zeitgeist/schema/Event#link"
					if history[j][3] in (2, 3, 5):
						use = "http://gnome.org/zeitgeist/schema/Event#visit"
					
					bookmark = False
					temp = self.cursor.execute("SELECT * FROM moz_bookmarks WHERE fk=" + str(item[0])).fetchone()
					if temp:
						bookmark = True
						
					item = {
						"timestamp": int(self.last_timestamp / (1000000)),
						"uri": unicode(item[1]),
						"text": unicode(item[2]),
						"source": u"Firefox History",
						"content": u"Web",
						"use": unicode(use),
						"mimetype": u"text/html", # TODO: Can we get a mime-type here?
						"tags": u"",
						"icon": icon,
						"bookmark": bookmark,
						"app": u"/usr/share/applications/firefox.desktop",
						"origin":  unicode(item[4][::-1][1:] if item[4] else u"")
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
