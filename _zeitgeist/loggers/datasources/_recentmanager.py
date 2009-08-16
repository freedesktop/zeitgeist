# -.- encoding: utf-8 -.-

# Zeitgeist
#
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
	
	@classmethod
	def create(cls, node):
		args = dict()
		for prop in ("href", "added", "modified", "visited"):
			args[prop] = node.getAttribute(prop)
		mimetype = node.getElementsByTagNameNS("http://www.freedesktop.org/standards/shared-mime-info", "mime-type")
		if mimetype:
			args["mimetype"] = mimetype.pop().getAttribute("type")
		else:
			raise ValueError
		applications = node.getElementsByTagNameNS("http://www.freedesktop.org/standards/desktop-bookmarks", "applications")
		assert applications
		application = applications[0].getElementsByTagNameNS("http://www.freedesktop.org/standards/desktop-bookmarks", "application")
		if application:
			args["application"] = application.pop().getAttribute("exec").strip("'")
		else:
			raise ValueError
		return cls(**args)
	
	@staticmethod
	def convert_timestring(time_str):
		# My observation is that all times in self.RECENTFILE are in UTC (I might be wrong here)
		# so we need to parse the time string into a timestamp
		# and correct the result by the timezone differenz
		try:
			timetuple = time.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")
		except ValueError:
			timetuple = iso_strptime(time_str.rstrip("Z")).timetuple()
		result = int(time.mktime(timetuple))
		if DST:
			result -= time.altzone
		return result
	
	def __init__(self, href, added, modified, visited, mimetype, application):
		self._uri = href
		self._path = "/%s" %href.split("///", 1).pop()
		self._added = self.convert_timestring(added)
		self._modified = self.convert_timestring(modified)
		self._visited = self.convert_timestring(visited)
		self._mimetype = mimetype
		self._application = application
		
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
		return os.path.basename(self._path)
				
	def exists(self):
		return os.path.exists(self._path)
		
	def get_private_hint(self):
		return False #how to get this??
		
	def last_application(self):
		return ""
		
	def get_application_info(self, app):
		return (self._application, None, None)

class RecentManager(gobject.GObject):
	
	RECENTFILE = os.path.expanduser("~/.recently-used.xbel")
	
	@staticmethod
	def _parse_recentfile(filename):
		doc = minidom_parse(filename)
		bookmarks = doc.getElementsByTagName("bookmark")
		for bookmark in bookmarks:
			yield FileInfo.create(bookmark)
	
	def __init__(self):
		super(RecentManager, self).__init__()
		if not os.path.exists(self.RECENTFILE):
			raise OSError("Can't use alternative RecentManager, '%s' not found" % self.RECENTFILE)
		self._recent = None
		file_object = gio.File(self.RECENTFILE)
		self.file_monitor = file_object.monitor_file()
		self.file_monitor.set_rate_limit(1600) # for to high rates RecentManager
											   # gets hickup, not sure what's optimal here
		self.file_monitor.connect("changed", self._content_changed)
	
	def _content_changed(self, monitor, fileobj, _, event):
		# maybe we should handle events differently
		if self._recent is None:
			# only emit signal if we aren't currently parsing RECENTFILE
			self.emit("changed")
	
	def get_items(self):
		if self._recent is not None:
			self._recent.close()
		self._recent = self._parse_recentfile(self.RECENTFILE)
		for n, info in enumerate(self._recent):
			yield info
		self._recent.close()
		self._recent = None
		
	def set_limit(self, limit):
		pass

gobject.type_register(RecentManager)

gobject.signal_new("changed", RecentManager,
				   gobject.SIGNAL_RUN_LAST,
				   gobject.TYPE_NONE,
				   tuple())
