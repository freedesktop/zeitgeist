# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Alex Graveley <alex.graveley@beatniksoftewarel.com>
# Copyright © 2009 Markus Korn <thekorn@gmx.de>
# Copyright © 2009 Natan Yellin <aantny@gmail.com>
# Copyright © 2009 Seif Lotfy <seif@lotfy.com>
# Copyright © 2009 Shane Fagan <shanepatrickfagan@yahoo.ie>
# Copyright © 2009 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
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
import re
import fnmatch
import urllib
import time
import logging
from xdg import BaseDirectory

from zeitgeist import _config
from zeitgeist.datamodel import Event, Subject, Interpretation, Manifestation
from _zeitgeist.loggers.zeitgeist_base import DataProvider

log = logging.getLogger("zeitgeist.logger.datasources.recent")

try:
	import gtk
	if gtk.pygtk_version >= (2, 15, 2):
		recent_manager = gtk.recent_manager_get_default
	else:
		from _recentmanager import RecentManager
		recent_manager = RecentManager
except ImportError:
	log.exception(_("Could not import GTK; data source disabled."))
	enabled = False
else:
	enabled = True

class SimpleMatch(object):
	""" Wrapper around fnmatch.fnmatch which allows to define mimetype
	patterns by using shell-style wildcards.
	"""

	def __init__(self, pattern):
		self.__pattern = pattern

	def match(self, text):
		return fnmatch.fnmatch(text, self.__pattern)

	def __repr__(self):
		return "%s(%r)" %(self.__class__.__name__, self.__pattern)

DOCUMENT_MIMETYPES = [
		# Covers:
		#	 vnd.corel-draw
		#	 vnd.ms-powerpoint
		#	 vnd.ms-excel
		#	 vnd.oasis.opendocument.*
		#	 vnd.stardivision.*
		#	 vnd.sun.xml.*
		SimpleMatch(u"application/vnd.*"),
		# Covers: x-applix-word, x-applix-spreadsheet, x-applix-presents
		SimpleMatch(u"application/x-applix-*"),
		# Covers: x-kword, x-kspread, x-kpresenter, x-killustrator
		re.compile(u"application/x-k(word|spread|presenter|illustrator)"),
		u"application/ms-powerpoint",
		u"application/msword",
		u"application/pdf",
		u"application/postscript",
		u"application/ps",
		u"application/rtf",
		u"application/x-abiword",
		u"application/x-gnucash",
		u"application/x-gnumeric",
		SimpleMatch("application/x-java*"),
		u"text/plain"
]

IMAGE_MIMETYPES = [
		# Covers:
		#	 vnd.corel-draw
		u"application/vnd.corel-draw",
		# Covers: x-kword, x-kspread, x-kpresenter, x-killustrator
		re.compile(u"application/x-k(word|spread|presenter|illustrator)"),
		SimpleMatch(u"image/*"),
]

AUDIO_MIMETYPES = [
		SimpleMatch(u"audio/*"),
		u"application/ogg"
]

VIDEO_MIMETYPES = [
		SimpleMatch(u"video/*"),
		u"application/ogg"
]

DEVELOPMENT_MIMETYPES = [
		u"text/x-python",
		u"application/x-perl",
		u"application/x-sql",
		u"text/x-java",
		u"text/x-csrc",
		u"text/x-c++src",
		u"text/css",
		U"application/x-shellscript",
		U"application/x-object",
		u"application/x-php",
		u"application/x-java-archive",
		u"text/html",
		u"application/xml",
		u"text/x-dsrc",
		u"text/x-pascal",
		u"text/x-patch",
		u"application/x-csh",
		u"text/x-eiffel",
		u"application/x-fluid",
		u"text/x-chdr",
		u"text/x-idl",
		u"application/javascript",
		u"text/x-lua",
		u"text/x-objcsrc",
		u"application/x-m4",
		u"text/x-ocaml",
		u"text/x-tcl",
		u"text/x-vhdl",
		u"application/xhtml+xml",
		u"text/x-gettext-translation",
		u"text/x-gettext-translation-template",
		u"application/x-glade",
		u"application/x-designer",
		u"text/x-makefile",
		u"text/x-sql",
		u"application/x-desktop",
		u"text/x-csharp",
		u"application/ecmascript",
		u"text/x-haskell",
		u"text/x-copying"
]

ALL_MIMETYPES = DOCUMENT_MIMETYPES + IMAGE_MIMETYPES + AUDIO_MIMETYPES +\
				VIDEO_MIMETYPES + DEVELOPMENT_MIMETYPES

class MimeTypeSet(set):
	""" Set which allows to match against a string or an object with a
	match() method.
	"""

	def __init__(self, *items):
		super(MimeTypeSet, self).__init__()
		self.__pattern = set()
		for item in items:
			if isinstance(item, (str, unicode)):
				self.add(item)
			elif hasattr(item, "match"):
				self.__pattern.add(item)
			else:
				raise ValueError("Bad mimetype '%s'" %item)

	def __contains__(self, mimetype):
		result = super(MimeTypeSet, self).__contains__(mimetype)
		if not result:
			for pattern in self.__pattern:
				if pattern.match(mimetype):
					return True
		return result
		
	def __len__(self):
		return super(MimeTypeSet, self).__len__() + len(self.__pattern)

	def __repr__(self):
		items = ", ".join(sorted(map(repr, self | self.__pattern)))
		return "%s(%s)" %(self.__class__.__name__, items)


class RecentlyUsedManagerGtk(DataProvider):
	
	FILTERS = {
		# dict of name as key and the matching mimetypes as value
		# if the value is None this filter matches all mimetypes
		u"Document": MimeTypeSet(*DOCUMENT_MIMETYPES),
		u"Image": MimeTypeSet(*IMAGE_MIMETYPES),
		u"Music": MimeTypeSet(*AUDIO_MIMETYPES),
		u"Video": MimeTypeSet(*VIDEO_MIMETYPES),
		u"SourceCode": MimeTypeSet(*DEVELOPMENT_MIMETYPES),
	}
	
	def __init__(self):
		DataProvider.__init__(self, name="Recently Used Documents")
		self.recent_manager = recent_manager()
		self.recent_manager.set_limit(-1)
		self.recent_manager.connect("changed", lambda m: self.emit("reload"))
		self.config.connect("configured", lambda m: self.emit("reload"))
		self._timestamp_last_run = 0
	
	@staticmethod
	def _find_desktop_file_for_application(application):
		""" Searches for a .desktop file for the given application in
		$XDG_DATADIRS and returns the path to the found file. If no file
		is found, returns None.
		"""
		
		desktopfiles = \
			list(BaseDirectory.load_data_paths("applications", "%s.desktop" % application))
		if desktopfiles:
			return unicode(desktopfiles[0])
		else:
			for path in BaseDirectory.load_data_paths("applications"):
				for filename in (name for name in os.listdir(path) if name.endswith(".desktop")):
					fullname = os.path.join(path, filename)
					for line in open(fullname):
						if line.startswith("Exec") and \
						line.split("=", 1)[-1].strip().split()[0] == application:
							return unicode(fullname)
		return None
	
	def _get_interpretation_for_mimetype(self, mimetype):
		matching_filter = None
		for filter_name, mimetypes in self.FILTERS.iteritems():
			if mimetype and mimetype in mimetypes:
				matching_filter = filter_name
				break
		if matching_filter:
			return getattr(Interpretation, matching_filter.upper()).uri
		return Interpretation.UNKNOWN.uri
	
	def _get_items(self):
		timestamp_last_run = time.time()
		
		events = []
		
		for (num, info) in enumerate(self.recent_manager.get_items()):
			if info.exists() and not info.get_private_hint() and not info.get_uri_display().startswith("/tmp/"):
				subject = Subject.new_for_values(
					uri = unicode(info.get_uri()),
					interpretation = self._get_interpretation_for_mimetype(
						unicode(info.get_mime_type())),
					manifestation = Manifestation.FILE.uri,
					text = info.get_display_name(),
					mimetype = unicode(info.get_mime_type()),
				)
				
				last_application = info.last_application().strip()
				application = info.get_application_info(last_application)[0].split()[0]
				desktopfile = self._find_desktop_file_for_application(application)
				times = (
					(info.get_added(), Interpretation.CREATE_EVENT.uri),
					(info.get_visited(), Interpretation.VISIT_EVENT.uri),
					(info.get_modified(), Interpretation.MODIFY_EVENT.uri)
				)
				
				is_new = False
				for timestamp, use in times:
					if timestamp <= self._timestamp_last_run:
						continue
					is_new = True
					events.append(Event.new_for_values(
						timestamp = timestamp,
						interpretation = use,
						manifestation = Manifestation.USER_ACTIVITY.uri,
						actor = desktopfile or u"",
						subjects = [subject]
						))
			if num % 50 == 0:
				self._process_gobject_events()
		self._timestamp_last_run = timestamp_last_run
		return events

if enabled:
	__datasource__ = RecentlyUsedManagerGtk()
