# -.- encoding: utf-8 -.-# -.- encoding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Seif Lotfy <seif@lotfy.com>
# Copyright © 2009 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
# Copyright © 2009 Natan Yellin <aantny@gmail.com>
# Copyright © 2009 Alex Graveley <alex.graveley@beatniksoftewarel.com>
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

import os
import re
import fnmatch
import urllib
import gtk
import gettext


from xdg import DesktopEntry, BaseDirectory

from zeitgeist.loggers.zeitgeist_base import DataProvider
from zeitgeist import config

gettext.install("zeitgeist", config.localedir, unicode=1)
		
# helpers

def get_desktopentry_for_application(application):
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
		return get_desktopentry_for_application("firefox") #just for now, for testing
			

class SimpleMatch(object):

	def __init__(self, pattern):
		self.__pattern = pattern

	def match(self, text):
		return fnmatch.fnmatch(text, self.__pattern)

	def __repr__(self):
		return "%s(%r)" %(self.__class__.__name__, self.__pattern)


class MimeTypeSet(set):

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

	def __repr__(self):
		items = ", ".join(map(repr, self | self.__pattern))
		return "%s(%s)" %(self.__class__.__name__, items)
		

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
		u"text/x-haskell"
		]
		

BROKEN_APPS = [
			   u"Document Viewer",
			   u"Text Editor",
			   u"Totem Movie Player",
			   u"File Manager"
			   ]

class RecentlyUsedManagerGtk(DataProvider):
	
	def __init__(self):
		DataProvider.__init__(self)
		self.recent_manager = gtk.recent_manager_get_default()
		self.recent_manager.set_limit(-1)
		self.recent_manager.connect("changed", lambda m: self.emit("reload"))
		
	def get_items_uncached(self):
		for info in self.recent_manager.get_items():
			if info.exists() and not info.get_private_hint() and "/tmp" not in info.get_uri_display():
				use = None
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
				
				uri = unicode(info.get_uri_display())
				text = info.get_display_name()
				mimetype = unicode(info.get_mime_type())
				last_application = info.last_application().strip()
				# this causes a  *** glibc detected *** python: double free or corruption (!prev): 0x0000000001614850 ***
				# bug in pygtk, reported as (lp: #386035) and upstream
				print last_application
				if BROKEN_APPS.count(unicode(last_application.strip())) == 0:
					print BROKEN_APPS
					application_info = info.get_application_info(last_application)
					#
					application = application_info[0].split()[0]
					desktopfile, desktopentry = get_desktopentry_for_application(application)
					icon = desktopentry.getIcon()
					origin = u"%s:///" %info.get_uri().split(":///")[0]
					times = (
						(info.get_added(), u"CreateEvent"),
						(info.get_visited(), u"VisitEvent"),
						(info.get_modified(), u"ModifyEvent")
					)
					
					for timestamp, use in times:
						item = {
							"timestamp": timestamp,
							"uri": uri,
							"text": text,
							#~ "source": u"File",
							"content": u"File",
							"use": u"http://gnome.org/zeitgeist/schema/1.0/core#%s" %use,
							"mimetype": mimetype,
							"tags": tags,
							"icon": icon,
							"app": unicode(desktopfile),
							"origin": "",
						}
						yield item


class RecentlyUsed(DataProvider):
	"""
	Recently-used documents, log stored in ~/.recently-used.
	"""
	def __init__(self, name, icon="stock_calendar"):
		DataProvider.__init__(self, name=name, icon=icon)
		recent_model.connect("reload", lambda m: self.emit("reload"))
		self.counter = 0
		self.last_uri = None
	
	def get_items_uncached(self):
		self.counter = self.counter + 1
		print "RecentlyUsed"
		print recent_model
		if recent_model:
			for item in recent_model.get_items_uncached():
				if self.include_item(item):
					yield item
				
	def include_item(self, item):
		return True


class RecentlyUsedOfMimeType(RecentlyUsed):
	"""
	Recently-used items filtered by a set of mimetypes.
	"""
	mimetype_list = MimeTypeSet()
	
	def __init__(self, name, icon, filter_name,inverse=False):
		RecentlyUsed.__init__(self, name, icon)
		self.filter_name = filter_name
		self.inverse = inverse
		self.icon = icon

	def include_item(self, item):
		return item["mimetype"] in self.mimetype_list
	
	def get_items_uncached(self):
		print "RecentlyUsedOfMimeType"
		for item in RecentlyUsed.get_items_uncached(self):
			print "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
			item["icon"] = self.icon
			item["source"] = unicode(self.filter_name)
			yield item


class RecentlyUsedDocumentsSource(RecentlyUsedOfMimeType):
	
	mimetype_list = MimeTypeSet(*DOCUMENT_MIMETYPES)
	
	def __init__(self):
		RecentlyUsedOfMimeType.__init__(self,
										name="Documents",
										icon="stock_new-presentation",
										filter_name=_("Documents"))


class RecentlyUsedOthersSource(RecentlyUsedOfMimeType):
	
	mimetype_list = MimeTypeSet(*(DOCUMENT_MIMETYPES +\
								  IMAGE_MIMETYPES +\
								  AUDIO_MIMETYPES +\
								  VIDEO_MIMETYPES +\
								  DEVELOPMENT_MIMETYPES)
								)
	
	def __init__(self):
		RecentlyUsedOfMimeType.__init__(self,
										name="Other",
										icon="applications-other",
										filter_name=_("Other"),
										inverse = True)
	
	def include_item(self, item):
		#~ item["icon"]=self.icon #waht is this supposed to do???
		return not item["mimetype"] in self.mimetype_list


class RecentlyUsedImagesSource(RecentlyUsedOfMimeType):
	
	mimetype_list = MimeTypeSet(*IMAGE_MIMETYPES)
	
	def __init__(self):
		RecentlyUsedOfMimeType.__init__(self,
										name="Images",
										icon="gnome-mime-image",
										filter_name=_("Images"))


class RecentlyUsedMusicSource(RecentlyUsedOfMimeType):
	
	mimetype_list = MimeTypeSet(*AUDIO_MIMETYPES)
	
	def __init__(self):
		RecentlyUsedOfMimeType.__init__(self,
										name="Music",
										icon="gnome-mime-audio",
										filter_name=_("Music"))


class RecentlyUsedVideoSource(RecentlyUsedOfMimeType):
	
	mimetype_list = MimeTypeSet(*VIDEO_MIMETYPES)
	
	def __init__(self):
		RecentlyUsedOfMimeType.__init__(self,
										name="Videos",
										icon="gnome-mime-video",
										filter_name=_("Videos"))

class RecentlyUsedDevelopmentSource(RecentlyUsedOfMimeType):

	mimetype_list = MimeTypeSet(*DEVELOPMENT_MIMETYPES)

	def __init__(self):
		RecentlyUsedOfMimeType.__init__(self,
										name="Development",
										icon="applications-development",
										filter_name=_("Development"))

recent_model = RecentlyUsedManagerGtk()

__datasource__ = (RecentlyUsedDocumentsSource(),
	RecentlyUsedImagesSource(), RecentlyUsedMusicSource(),
	RecentlyUsedOthersSource(), RecentlyUsedVideoSource(),
	RecentlyUsedDevelopmentSource())
