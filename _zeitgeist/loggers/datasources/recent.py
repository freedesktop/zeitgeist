# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Alex Graveley <alex.graveley@beatniksoftewarel.com>
# Copyright © 2009 Markus Korn <thekorn@gmx.de>
# Copyright © 2009 Natan Yellin <aantny@gmail.com>
# Copyright © 2009 Seif Lotfy <seif@lotfy.com>
# Copyright © 2009 Shane Fagan <shanepatrickfagan@yahoo.ie>
# Copyright © 2009-2010 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
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

from __future__ import with_statement
import os
import re
import fnmatch
import urllib
import time
import logging
from xdg import BaseDirectory

from zeitgeist import _config
from zeitgeist.datamodel import Event, Subject, Interpretation, Manifestation, \
	DataSource, get_timestamp_for_now
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
		SimpleMatch(u"application/x-java*"),
		SimpleMatch(u"*/x-tex"),
		SimpleMatch(u"*/x-latex"),
		SimpleMatch(u"*/x-dvi"),
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
		u"application/ecmascript",
		u"application/javascript",
		u"application/x-csh",
		u"application/x-designer",
		u"application/x-desktop",
		u"application/x-dia-diagram",
		u"application/x-fluid",
		u"application/x-glade",
		u"application/xhtml+xml",
		u"application/x-java-archive",
		u"application/x-m4",
		u"application/xml",
		u"application/x-object",
		u"application/x-perl",
		u"application/x-php",
		u"application/x-ruby",
		u"application/x-shellscript",
		u"application/x-sql",
		u"text/css",
		u"text/html",
		u"text/x-c",
		u"text/x-c++",
		u"text/x-chdr",
		u"text/x-copying",
		u"text/x-credits",
		u"text/x-csharp",
		u"text/x-c++src",
		u"text/x-csrc",
		u"text/x-dsrc",
		u"text/x-eiffel",
		u"text/x-gettext-translation",
		u"text/x-gettext-translation-template",
		u"text/x-haskell",
		u"text/x-idl",
		u"text/x-java",
		u"text/x-lisp",
		u"text/x-lua",
		u"text/x-makefile",
		u"text/x-objcsrc",
		u"text/x-ocaml",
		u"text/x-pascal",
		u"text/x-patch",
		u"text/x-python",
		u"text/x-sql",
		u"text/x-tcl",
		u"text/x-troff",
		u"text/x-vala",
		u"text/x-vhdl",
]

ALL_MIMETYPES = DOCUMENT_MIMETYPES + IMAGE_MIMETYPES + AUDIO_MIMETYPES + \
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
		"DOCUMENT": MimeTypeSet(*DOCUMENT_MIMETYPES),
		"IMAGE": MimeTypeSet(*IMAGE_MIMETYPES),
		"MUSIC": MimeTypeSet(*AUDIO_MIMETYPES),
		"Video": MimeTypeSet(*VIDEO_MIMETYPES),
		"SOURCE_CODE": MimeTypeSet(*DEVELOPMENT_MIMETYPES),
	}
	
	def __init__(self, client):
		DataProvider.__init__(self,
			unique_id="com.zeitgeist-project,datahub,recent",
			name="Recently Used Documents",
			description="Logs events from GtkRecentlyUsed",
			event_templates=[Event.new_for_values(interpretation=i) for i in (
				Interpretation.CREATE_EVENT,
				Interpretation.ACCESS_EVENT,
				Interpretation.MODIFY_EVENT
			)],
			client=client)
		self._load_data_sources_registry()
		self.recent_manager = recent_manager()
		self.recent_manager.set_limit(-1)
		self.recent_manager.connect("changed", lambda m: self.emit("reload"))
		self.config.connect("configured", lambda m: self.emit("reload"))
	
	def _load_data_sources_registry(self):
		self._ignore_apps = {}
		def _data_source_registered(datasource):
			for tmpl in datasource[DataSource.EventTemplates]:
				actor = tmpl[0][Event.Actor]
				if actor:
					if not actor in self._ignore_apps:
						self._ignore_apps[actor] = set()
					interp = tmpl[0][Event.Interpretation]
					if interp:
						self._ignore_apps[actor].add(interp)
		for datasource in self._registry.GetDataSources():
			_data_source_registered(datasource)
		self._registry.connect("DataSourceRegistered", _data_source_registered)
	
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
					try:
						with open(fullname) as desktopfile:
							for line in desktopfile:
								if line.startswith("Exec=") and \
								line.split("=", 1)[-1].strip().split()[0] == \
								application:
									return unicode(fullname)
					except IOError:
						pass # file may be a broken symlink (LP: #523761)
		return None
	
	def _get_interpretation_for_mimetype(self, mimetype):
		matching_filter = None
		for filter_name, mimetypes in self.FILTERS.iteritems():
			if mimetype and mimetype in mimetypes:
				matching_filter = filter_name
				break
		if matching_filter:
			return getattr(Interpretation, matching_filter).uri
		return ""
	
	def _get_items(self):
		# We save the start timestamp to avoid race conditions
		last_seen = get_timestamp_for_now()
		
		events = []
		
		for (num, info) in enumerate(self.recent_manager.get_items()):
			uri = info.get_uri()
			if info.exists() and not info.get_private_hint() and not uri.startswith("file:///tmp/"):
				last_application = info.last_application().strip()
				application = info.get_application_info(last_application)[0].split()[0]
				desktopfile = self._find_desktop_file_for_application(application)
				if not desktopfile:
					continue
				actor = u"application://%s" % os.path.basename(desktopfile)
				
				subject = Subject.new_for_values(
					uri = unicode(uri),
					interpretation = self._get_interpretation_for_mimetype(
						unicode(info.get_mime_type())),
					manifestation = Manifestation.FILE_DATA_OBJECT.uri,
					text = info.get_display_name(),
					mimetype = unicode(info.get_mime_type()),
					origin = uri.rpartition("/")[0]
				)
				
				times = set()
				for meth, interp in (
					(info.get_added, Interpretation.CREATE_EVENT.uri),
					(info.get_visited, Interpretation.ACCESS_EVENT.uri),
					(info.get_modified, Interpretation.MODIFY_EVENT.uri)
					):
					if actor not in self._ignore_apps or \
						(self._ignore_apps[actor] and
						interp not in self._ignore_apps[actor]):
						times.add((meth() * 1000, interp))
				
				is_new = False
				for timestamp, use in times:
					if timestamp <= self._last_seen:
						continue
					is_new = True
					events.append(Event.new_for_values(
						timestamp = timestamp,
						interpretation = use,
						manifestation = Manifestation.USER_ACTIVITY.uri,
						actor = actor,
						subjects = [subject]
						))
			if num % 50 == 0:
				self._process_gobject_events()
		self._last_seen = last_seen
		return events

if enabled:
	__datasource__ = RecentlyUsedManagerGtk
