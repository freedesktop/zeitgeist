# -.- encoding: utf-8 -.-

import os
import re
import urllib
import gtk
import gettext

from zeitgeist.loggers.zeitgeist_base import DataProvider

DOCUMENT_MIMETYPES = [
		# Covers:
		#	 vnd.corel-draw
		#	 vnd.ms-powerpoint
		#	 vnd.ms-excel
		#	 vnd.oasis.opendocument.*
		#	 vnd.stardivision.*
		#	 vnd.sun.xml.*
		re.compile(u"application/vnd.*"),
		# Covers: x-applix-word, x-applix-spreadsheet, x-applix-presents
		re.compile(u"application/x-applix-*"),
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
		u"application/x-java*",
		u"text/plain"
		]

IMAGE_MIMETYPES = [
		# Covers:
		#	 vnd.corel-draw
		re.compile(u"application/vnd.corel-draw"),
		# Covers: x-kword, x-kspread, x-kpresenter, x-killustrator
		re.compile(u"application/x-k(illustrator)"),
		re.compile(u"image/*"),
		]

AUDIO_MIMETYPES = [
		re.compile(u"audio/*"),
		u"application/ogg"
		]

VIDEO_MIMETYPES = [
		re.compile(u"video/*"),
		u"application/ogg"
		]


class RecentlyUsedManagerGtk(DataProvider):
	
	def __init__(self):
		DataProvider.__init__(self)
		self.recent_manager = gtk.recent_manager_get_default()
		self.recent_manager.set_limit(-1)
		self.recent_manager.connect("changed", lambda m: self.emit("reload"))
		
	def get_items_uncached(self):
		for info in self.recent_manager.get_items():
			if info.exists() and not info.get_private_hint() and info.get_uri().find("/tmp") < 0:
				use = None
				
				# Create a string of tags based on the file's path
				# e.g. the file /home/natan/foo/bar/example.py would be tagged with "foo" and "bar"
				# Note: we only create tags for files under the users home folder
				tags = ""
				tmp = info.get_uri()[info.get_uri().find('://') + 3:]
				tmp = os.path.dirname(tmp)		# remove the filename from the string
				home = os.path.expanduser("~")	# get the users home folder
				
				if tmp.startswith(home):
					tmp = tmp[len(home)+1:]
				if tmp != "":
					tmp = unicode(urllib.unquote(tmp))
					tags = tmp.replace("/", ",")
				
				item = {
					"uri": unicode((info.get_uri()), 'utf-8'),
					"name": unicode(urllib.unquote(info.get_display_name())),
					"comment": unicode(info.get_display_name()),
					"mimetype": unicode(info.get_mime_type()),
					"tags": unicode(tags),
					"app": info.last_application(),
				}
				
				item["timestamp"] = info.get_added()
				item["use"] = unicode("first usage")
				yield item
				
				item["timestamp"] = info.get_visited()
				item["use"] = unicode("opened")
				yield item
				
				item["timestamp"] = info.get_modified()
				item["use"] = unicode("modified")
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
		return (item for item in recent_model.get_items() if self.include_item(item))
	
	def include_item(self, item):
		return True


class RecentlyUsedOfMimeType(RecentlyUsed):
	"""
	Recently-used items filtered by a set of mimetypes.
	"""
	def __init__(self, name, icon, mimetype_list, filter_name,inverse=False):
		RecentlyUsed.__init__(self, name, icon)
		self.mimetype_list = mimetype_list
		self.filter_name = filter_name
		self.inverse = inverse
		self.icon = icon

	def include_item(self, item):
		item_mime = item["mimetype"]
		for mimetype in self.mimetype_list:
			if hasattr(mimetype, "match") and mimetype.match(item_mime) or item_mime == mimetype:
				return True
		return False
	
	def get_items_uncached(self):
		for item in RecentlyUsed.get_items_uncached(self):
			
			counter = 0
			info = recent_model.recent_manager.lookup_item(item["uri"])
			
			for app in info.get_applications():
				appinfo = info.get_application_info(app)
				counter = counter + appinfo[1]
				item["type"] = self.name
			 	item["icon"] = self.icon
			
			yield item


class RecentlyUsedDocumentsSource(RecentlyUsedOfMimeType):
	
	def __init__(self):
		RecentlyUsedOfMimeType.__init__(self,
										name="Documents",
										icon="stock_new-presentation",
										mimetype_list=DOCUMENT_MIMETYPES,
										filter_name=_("Documents"))


class RecentlyUsedOthersSource(RecentlyUsedOfMimeType):
	
	OTHER_MIMETYPES = DOCUMENT_MIMETYPES + IMAGE_MIMETYPES + AUDIO_MIMETYPES + VIDEO_MIMETYPES
	
	def __init__(self):
		RecentlyUsedOfMimeType.__init__(self,
										name="Other",
										icon="applications-other",
										mimetype_list=self.OTHER_MIMETYPES,
										filter_name=_("Other"),
										inverse = True)
	
	def include_item(self, item):
		item_mime = item["mimetype"]
		for mimetype in self.mimetype_list:
			if hasattr(mimetype, "match") and mimetype.match(item_mime) or item_mime == mimetype:
				return False		
		item["icon"]=self.icon
		return True


class RecentlyUsedImagesSource(RecentlyUsedOfMimeType):
	
	def __init__(self):
		RecentlyUsedOfMimeType.__init__(self,
										name="Images",
										icon="gnome-mime-image",
										mimetype_list=IMAGE_MIMETYPES,
										filter_name=_("Images"))


class RecentlyUsedMusicSource(RecentlyUsedOfMimeType):
	
	def __init__(self):
		RecentlyUsedOfMimeType.__init__(self,
										name="Music",
										icon="gnome-mime-audio",
										mimetype_list=AUDIO_MIMETYPES,
										filter_name=_("Music"))


class RecentlyUsedVideoSource(RecentlyUsedOfMimeType):
	
	def __init__(self):
		RecentlyUsedOfMimeType.__init__(self,
										name="Videos",
										icon="gnome-mime-video",
										mimetype_list=VIDEO_MIMETYPES,
										filter_name=_("Videos"))

recent_model = RecentlyUsedManagerGtk()

__datasource__ = (RecentlyUsedDocumentsSource(),
	RecentlyUsedImagesSource(), RecentlyUsedMusicSource(),
	RecentlyUsedOthersSource(), RecentlyUsedVideoSource())
