# -.- encoding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Seif Lotfy <seif@lotfy.com>
# Copyright © 2009 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
# Copyright © 2009 Natan Yellin <aantny@gmail.com>
# Copyright © 2009 Markus Korn <thekorn@gmx.de>
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

import os
import shutil
import sqlite3 as db
import gettext
import logging
import dbus
import gio
from xdg import BaseDirectory

from _zeitgeist.loggers.zeitgeist_base import DataProvider

log = logging.getLogger("zeitgeist.logger.datasources.evolution")

class EvolutionSource(DataProvider):
	
	EVOLUTION_DIR = os.path.expanduser("~/.evolution/mail/local")
	DATABASE = os.path.join(EVOLUTION_DIR, "folders.db")
	PATH = os.path.join(BaseDirectory.xdg_cache_home, "zeitgeist")
	LOCATION = os.path.join(PATH, "evolution_folders.sqlite")
	
	@staticmethod
	def get_last_timestamp():
		# Connect to D-Bus
		bus = dbus.SessionBus()
		try:
			remote_object = bus.get_object("org.gnome.zeitgeist", "/org/gnome/zeitgeist")
		except dbus.exceptions.DBusException:
			log.error("Could not connect to D-Bus.")
			return 0
		iface = dbus.Interface(remote_object, "org.gnome.zeitgeist")
		return iface.GetLastInsertionDate(u"/usr/share/applications/evolution.desktop")
	
	def __init__(self, name="Mail", icon="stock_mail", uri="gzg/evolution"):
		DataProvider.__init__(self, name=u"Evolution")
		self.cursor = None
		try:
			file_object = gio.File(self.DATABASE)
			self.note_path_monitor = file_object.monitor_file()
			self.note_path_monitor.connect("changed", self.reload_proxy_filemonitor)
		except Exception, e:
			log.exception(_("Unable to monitor Evolution: %s: %s") % \
				(self.DATABASE, str(e)))
		else:
			log.debug(_("Monitoring Evolution: %s") % self.DATABASE)
			
			self.last_timestamp = self.get_last_timestamp()
			self.__copy_sqlite()
		self.config.connect("configured", self.reload_proxy_config)
		
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
		if self.cursor is None:
			logr.warning("Can not connect to: %s" % self.DATABASE)
			raise StopIteration
		try:
			# retrieve all urls from evolution's history
			contents = "dsent, subject, mail_to"
			history = self.cursor.execute("SELECT " + contents + 
				" FROM Sent WHERE dsent>?", (self.last_timestamp,)).fetchall()
		except db.OperationalError, e:
			log.exception("Evolution database error: %s" % e)
		else:
			for timestamp, subject, mail_to in history:
				item = {
					"timestamp": int(timestamp),
					"uri": u"mailto:%s" %mail_to,
					"text": unicode(subject),
					"source": u"Evolution History",
					"content": u"Mail",
					"use": u"http://gnome.org/zeitgeist/schema/1.0/core#CreateEvent",
					"mimetype": u"mail", # TODO: what's the correct mime type for mails?
										 # do we know if it is text or html mail?
					"tags": u"",
					"icon": u"",
					"bookmark": False,
					"app": u"/usr/share/applications/evolution.desktop",
					"origin": u"",
				}
				yield item
	
	def __copy_sqlite(self):
		"""
		Copy the sqlite file to avoid file locks when it's being used by evolution.
		"""
		if not os.path.isdir(self.PATH):
			os.mkdir(self.PATH)
		if self.cursor:
			self.cursor.close()
		try:
			shutil.copy2(self.DATABASE,  self.LOCATION)
		except IOError:
			self.cursor = None
		else:
			self.connection = db.connect(self.LOCATION, True)
			self.cursor = self.connection.cursor()

__datasource__ = EvolutionSource()
