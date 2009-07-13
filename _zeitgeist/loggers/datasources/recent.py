# -.- encoding: utf-8 -.-

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
from xdg import DesktopEntry, BaseDirectory

from zeitgeist import _config
from _zeitgeist.loggers.zeitgeist_base import DataProvider

log = logging.getLogger("zeitgeist.logger.datasources.recent")

try:
	import gtk
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
		
# helpers

def get_desktopentry_for_application(application):
	""" searches for a .desktop file for a given application in
	$XDG_DATADIRS and returns a tuple of the path to the found file and
	the related DesktopEntry object. If no .desktop file for the
	application was found it returns the result for 'firefox'
	"""
	desktopfiles = list(
		BaseDirectory.load_data_paths("applications", "%s.desktop" %application)
	)
	if desktopfiles:
		# What do we do in cases where multible .desktop files are found for one application?
		# take the one in the users $HOME? or raise an error?
		filename = desktopfiles.pop(0)
		return filename, DesktopEntry.DesktopEntry(filename)
	else:
		# What to do when there is no .desktop file for an application?
		# raise an error? or try to get an alternative file?
		# Example gimp-s.6 has no .desktop file
		return get_desktopentry_for_application("firefox") # just for now, for testing
														   # this might cause an endless loop
														   # if firefox.desktop is not found


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
		
		
class InverseMimeTypeSet(MimeTypeSet):
	
	def __contains__(self, mimetype):
		return not super(InverseMimeTypeSet, self).__contains__(mimetype)
		

class RecentlyUsedManagerGtk(DataProvider):
	
	FILTERS = {
		# dict of name as key and  the matching mimetypes as value
		# if the value is None this filter matches all mimetypes
		u"Documents": MimeTypeSet(*DOCUMENT_MIMETYPES),
		u"Other": InverseMimeTypeSet(*ALL_MIMETYPES),
		u"Images": MimeTypeSet(*IMAGE_MIMETYPES),
		u"Music": MimeTypeSet(*AUDIO_MIMETYPES),
		u"Videos": MimeTypeSet(*VIDEO_MIMETYPES),
		u"Development": MimeTypeSet(*DEVELOPMENT_MIMETYPES),
	}
	
	def __init__(self):
		DataProvider.__init__(self, name="Recently Used Documents")
		self.recent_manager = gtk.recent_manager_get_default()
		self.recent_manager.set_limit(-1)
		self.recent_manager.connect("changed", lambda m: self.emit("reload"))
		self.config.connect("configured", lambda m: self.emit("reload"))
		self._timestamp_last_run = 0
		
	def get_items_uncached(self):
		timestamp_last_run = time.time()
		for info in self.recent_manager.get_items():
			if info.exists() and not info.get_private_hint() and "/tmp" not in info.get_uri_display():
				# Create a string of tags based on the file's path
				# e.g. the file /home/natan/foo/bar/example.py would be tagged with "foo" and "bar"
				# Note: we only create tags for files under the users home folder
				tags = ""
				tmp = info.get_uri_display()
				tmp = os.path.dirname(tmp)		# remove the filename from the string
				home = os.path.expanduser("~")	# get the users home folder
				
				if tmp.startswith(home):
					tmp = tmp[len(home)+1:]
				if tmp:
					tmp = unicode(urllib.unquote(tmp))
					tags = tmp.replace(",", " ").replace("/", ",")
				
				uri = unicode(info.get_uri())
				text = info.get_display_name()
				mimetype = unicode(info.get_mime_type())
				last_application = info.last_application().strip()
				application_info = info.get_application_info(last_application)
				application = application_info[0].split()[0]
				desktopfile, desktopentry = get_desktopentry_for_application(application)
				times = (
					(info.get_added(), u"CreateEvent"),
					(info.get_visited(), u"VisitEvent"),
					(info.get_modified(), u"ModifyEvent")
				)
				
				for timestamp, use in times:
					if timestamp < self._timestamp_last_run:
						continue
					for filter_name, mimetypes in self.FILTERS.iteritems():
						if mimetype and mimetype in mimetypes:
							item = {
								"timestamp": timestamp,
								"uri": uri,
								"text": text,
								"source": filter_name,
								"content": u"File",
								"use": u"http://gnome.org/zeitgeist/schema/1.0/core#%s" %use,
								"mimetype": mimetype,
								"tags": tags,
								"icon": u"",
								"app": unicode(desktopfile),
								"origin": u"", 	# we are not sure about the origin of this item,
												# let's make it NULL; it has to be a string
							}
							yield item
		self._timestamp_last_run = timestamp_last_run

if enabled:
	__datasource__ = RecentlyUsedManagerGtk()
