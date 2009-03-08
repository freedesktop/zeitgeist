import os
import re

import gtk
from gettext import gettext as _

from zeitgeist_base import Data, DataProvider

class RecentlyUsedManagerGtk(DataProvider):
	
	def __init__(self):
		DataProvider.__init__(self)
		self.recent_manager = gtk.recent_manager_get_default()
		self.recent_manager.set_limit(-1)
		self.recent_manager.connect("changed", lambda m: self.emit("reload"))
		
	def get_items_uncached(self):
		for info in self.recent_manager.get_items():
			counter=0
			if info.exists() and not info.get_private_hint() and info.get_uri().find("/tmp") < 0:
				use = None
				timestamp=max([info.get_added(), info.get_modified(), info.get_visited()])
				if info.get_added() == timestamp:
					use = "first usage"	
				elif info.get_visited() == timestamp:
					use = "opened"
				elif info.get_modified() == timestamp:
					use = "modified"
				
				# Create a string of tags based on the file's path
				# e.g. the file /home/natan/foo/bar/example.py would be tagged with "foo" and "bar"
				# Note: we only create tags for files under the users home folder
				tags = ""
				#tags=info.get_groups()
				tmp = info.get_uri()[7:]		# strip off "file://" from the uri
				tmp = os.path.dirname(tmp)		# remove the filename from the string
				home = os.path.expanduser("~")  # get the users home folder
				if tmp.startswith(home):
					tmp = tmp.replace(home + "/", "", 1)
					if tmp != "":
		                                tmp = tmp.replace("%20", " ")
						tags = tmp.replace("/", ",")
							
				yield Data(name=info.get_display_name(),
					uri=info.get_uri(),
					mimetype=info.get_mime_type(),
					timestamp=timestamp,
					tags=tags,
					count=counter,
					use=use)
						
class RecentlyUsed(DataProvider):
	'''
	Recently-used documents, log stored in ~/.recently-used.
	'''
	def __init__(self, name, icon="stock_calendar"):
		DataProvider.__init__(self, name=name, icon=icon)
		recent_model.connect("reload", lambda m: self.emit("reload"))
		self.counter = 0
	
	def get_items_uncached(self):
		self.counter = self.counter + 1
		for item in recent_model.get_items():
			# Check whether to include this item
			if self.include_item(item):
				yield item
	
	def include_item(self, item):
		return True

class RecentlyUsedOfMimeType(RecentlyUsed):
	'''
	Recently-used items filtered by a set of mimetypes.
	'''
	def __init__(self, name, icon, mimetype_list, filter_name,inverse=False):
		RecentlyUsed.__init__(self, name, icon)
		self.mimetype_list = mimetype_list
		self.filter_name = filter_name
		self.inverse = inverse

	def include_item(self, item):
		item_mime = item.get_mimetype()
		for mimetype in self.mimetype_list:
			if hasattr(mimetype, "match") and mimetype.match(item_mime) or item_mime == mimetype:
				return True
		return False
	
	def get_items_uncached(self):
		for item in RecentlyUsed.get_items_uncached(self):
			counter = 0
			info = recent_model.recent_manager.lookup_item(item.uri)
			
			for app in info.get_applications():
				appinfo=info.get_application_info(app)
				counter=counter+appinfo[1]
			
			yield Data(name=item.name,
						uri=item.get_uri(),
						timestamp=item.timestamp,
						count=counter,use=item.use,
						type=self.filter_name,
						mimetype=item.mimetype,
						tags=item.tags)

class RecentlyUsedDocumentsSource(RecentlyUsedOfMimeType):
	### FIXME: This is lame, we should generate this list somehow.
	DOCUMENT_MIMETYPES = [
		# Covers:
		#	 vnd.corel-draw
		#	 vnd.ms-powerpoint
		#	 vnd.ms-excel
		#	 vnd.oasis.opendocument.*
		#	 vnd.stardivision.*
		#	 vnd.sun.xml.*
		re.compile("application/vnd.*"),
		# Covers: x-applix-word, x-applix-spreadsheet, x-applix-presents
		re.compile("application/x-applix-*"),
		# Covers: x-kword, x-kspread, x-kpresenter, x-killustrator
		re.compile("application/x-k(word|spread|presenter|illustrator)"),
		"application/ms-powerpoint",
		"application/msword",
		"application/pdf",
		"application/postscript",
		"application/ps",
		"application/rtf",
		"application/x-abiword",
		"application/x-gnucash",
		"application/x-gnumeric",
		"application/x-java*",
		]
	
	def __init__(self):
		RecentlyUsedOfMimeType.__init__(self,
										name=_("Documents"),
										icon="stock_new-presentation",
										mimetype_list=self.DOCUMENT_MIMETYPES,
										filter_name="Documents")
				  
class RecentlyUsedOthersSource(RecentlyUsedOfMimeType):
	### FIXME: This is lame, we should generate this list somehow.
	DOCUMENT_MIMETYPES = [
		# Covers:
		#	 vnd.corel-draw
		#	 vnd.ms-powerpoint
		#	 vnd.ms-excel
		#	 vnd.oasis.opendocument.*
		#	 vnd.stardivision.*
		#	 vnd.sun.xml.*
		re.compile("text/*"),
		"application/x-asp",
		"application/x-bittorrent",
		"application/x-blender",
		"application/x-cgi",
		"application/x-dia-diagram",
		"application/x-dvi",
		"application/x-glade",
		"application/x-iso-image",
		"application/x-jbuilder-project",
		"application/x-magicpoint",
		"application/x-mrproject",
		"application/x-php",
		"application/tar",
		"application/x-tar",
		"applicaton/x-gtar",
		"multipart/x-tar",
		"application/x-compress",
		"application/x-compressed",
		"application/x-javascript",
		"application/javascript",
		]
	
	def __init__(self):
		RecentlyUsedOfMimeType.__init__(self,
										name=_("Other"),
										icon="applications-other",
										mimetype_list=self.DOCUMENT_MIMETYPES,
										filter_name="Other",
										inverse = True)
			
class RecentlyUsedImagesSource(RecentlyUsedOfMimeType):
	### FIXME: This is lame, we should generate this list somehow.
	DOCUMENT_MIMETYPES = [
		# Covers:
		#	 vnd.corel-draw
		re.compile("application/vnd.corel-draw"),
		# Covers: x-kword, x-kspread, x-kpresenter, x-killustrator
		re.compile("application/x-k(illustrator)"),
		re.compile("image/*"),
		]
	
	def __init__(self):
		RecentlyUsedOfMimeType.__init__(self,
										name=_("Images"),
										icon="gnome-mime-image",
										mimetype_list=self.DOCUMENT_MIMETYPES,
										filter_name="Images")
										
class RecentlyUsedMusicSource(RecentlyUsedOfMimeType):
	### FIXME: This is lame, we should generate this list somehow.
	MEDIA_MIMETYPES = [
		re.compile("audio/*"),
		"application/ogg"
		]

	def __init__(self):
		RecentlyUsedOfMimeType.__init__(self,
										name=_("Music"),
										icon="gnome-mime-audio",
										mimetype_list=self.MEDIA_MIMETYPES,
										filter_name="Music")
					   
class RecentlyUsedVideoSource(RecentlyUsedOfMimeType):
	### FIXME: This is lame, we should generate this list somehow.
	MEDIA_MIMETYPES = [
		re.compile("video/*"),
		"application/ogg"
		]

	def __init__(self):
		RecentlyUsedOfMimeType.__init__(self,
										name=_("Videos"),
										icon="gnome-mime-video",
										mimetype_list=self.MEDIA_MIMETYPES,
										filter_name="Videos")

recent_model = RecentlyUsedManagerGtk()
