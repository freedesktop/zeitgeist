# -.- encoding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Markus Korn <thekorn@gmx.de>
# Copyright © 2009 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
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

import urllib
import gobject
import gio
import os.path
import time
import logging
from xml.dom.minidom import parse as minidom_parse

from _zeitgeist.loggers.iso_strptime import iso_strptime

DST = bool(time.mktime(time.gmtime(0)))
log = logging.getLogger("zeitgeist.logger._recentmanager")

class FileInfo(object):
	
	@staticmethod
	def convert_timestring(time_str):
		# My observation is that all times in self.RECENTFILE are in UTC (I might be wrong here)
		# so we need to parse the time string into a timestamp
		# and correct the result by the timezone difference
		try:
			timetuple = time.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")
		except ValueError:
			timetuple = iso_strptime(time_str.rstrip("Z")).timetuple()
		result = int(time.mktime(timetuple))
		if DST:
			result -= time.altzone
		return result
	
	def __init__(self, node):
		self._uri = node.getAttribute("href")
		self._path = "/%s" % self._uri.split("///", 1)[-1]
		self._added = self.convert_timestring(node.getAttribute("added"))
		self._modified = self.convert_timestring(node.getAttribute("modified"))
		self._visited = self.convert_timestring(node.getAttribute("visited"))
		
		mimetype = node.getElementsByTagNameNS(
			"http://www.freedesktop.org/standards/shared-mime-info",
			"mime-type")
		if not mimetype:
			raise ValueError, "Could not find mimetype for item: %s" % self._uri
		self._mimetype = mimetype[-1].getAttribute("type")
		
		applications = node.getElementsByTagNameNS(
			"http://www.freedesktop.org/standards/desktop-bookmarks",
			"applications")
		assert applications
		application = applications[0].getElementsByTagNameNS(
			"http://www.freedesktop.org/standards/desktop-bookmarks",
			"application")
		if not application:
			raise ValueError, "Could not find application for item: %s" % self._uri
		self._application = application[-1].getAttribute("exec").strip("'")
		
	def get_mime_type(self):
		return self._mimetype
	
	def get_visited(self):
		return self._visited
	
	def get_added(self):
		return self._added
	
	def get_modified(self):
		return self._modified
	
	def get_uri_display(self):
		return self._path
	
	def get_uri(self):
		return self._uri
	
	def get_display_name(self):
		return unicode(os.path.basename(urllib.unquote(str(self._path))))
	
	def exists(self):
		if not self._uri.startswith("file:///"):
			return True # Don't check online resources
		return gio.File(self._path).get_path() is not None
	
	def get_private_hint(self):
		return False # FIXME: How to get this?
	
	def last_application(self):
		# Not necessary, our get_application_info always returns the info of
		# the last application
		return ""
	
	def get_application_info(self, app):
		return (self._application, None, None)

class RecentManager(gobject.GObject):
	
	RECENTFILE = os.path.expanduser("~/.recently-used.xbel")
	
	def __init__(self):
		super(RecentManager, self).__init__()
		if not os.path.exists(self.RECENTFILE):
			raise OSError("Can't use alternative RecentManager, '%s' not found" % self.RECENTFILE)
		
		self._fetching_items = None
		file_object = gio.File(self.RECENTFILE)
		self.file_monitor = file_object.monitor_file()
		self.file_monitor.set_rate_limit(1600) # for to high rates RecentManager
											   # gets hickup, not sure what's optimal here
		self.file_monitor.connect("changed", self._content_changed)
	
	def _content_changed(self, monitor, fileobj, _, event):
		# Only emit the signal if we aren't already parsing RECENTFILE
		if not self._fetching_items:
			self.emit("changed")
	
	def get_items(self):
		self._fetching_items = True
		xml = minidom_parse(self.RECENTFILE)
		for bookmark in xml.getElementsByTagName("bookmark"):
			yield FileInfo(bookmark)
		self._fetching_items = False
	
	def set_limit(self, limit):
		pass

gobject.type_register(RecentManager)

gobject.signal_new("changed", RecentManager,
	gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())
