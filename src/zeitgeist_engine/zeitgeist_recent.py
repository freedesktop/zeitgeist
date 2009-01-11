import datetime
import gc
import os
import re
import sys
import time
import urllib
import urlparse

import gnome.ui
import gnomevfs
import gnomevfs.async
import gobject
import gtk
from gettext import gettext as _
from zeitgeist_base import Data, DataProvider
from zeitgeist_dbcon import db

class RecentlyUsedManagerGtk(DataProvider):
	def __init__(self):
		DataProvider.__init__(self)
		self.recent_manager = gtk.recent_manager_get_default()
		self.recent_manager.set_limit(-1)
		self.recent_manager.connect("changed", lambda m: self.emit("reload"))
		
		
	def get_items_uncached(self):
		# 
	   # delself.temp_list
	   for info in self.recent_manager.get_items():
			counter=0
			if info.exists():
				if not info.get_private_hint():					
						use = None
						timestamp=max( [info.get_added(),info.get_modified(),info.get_visited()])
						if info.get_uri().find("/tmp/") < 0:
							
							#print str(info.get_uri())+"	"+ str(info.get_added())+"		"+str(info.get_modified())+"		"+str(info.get_visited())
							#print info.get_groups()
							if info.get_added() == timestamp:
								use = "first usage"
								
							elif info.get_visited() == timestamp:
								use = "opened"
							
							elif info.get_modified() == timestamp:
								use = "modified"
							
							yield Data(name=info.get_display_name(),
								uri=info.get_uri(),
								mimetype=info.get_mime_type(),
								timestamp=timestamp,
								tags=info.get_groups(),
								count=counter,
								use=use,
								)
						
class RecentlyUsed(DataProvider):
	'''
	Recently-used documents, log stored in ~/.recently-used.
	'''
	def __init__(self, name, icon = "stock_calendar"):
		DataProvider.__init__(self, name=name, icon=icon)
		recent_model.connect("reload", lambda m: self.emit("reload"))
		self.counter = 0
	
	def get_items_uncached(self):
	   # 
		self.counter  =self.counter  + 1
		#print ( " getting recently used " + str(self.counter))
	   # delself.temp_list
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
	def __init__(self, name, icon, mimetype_list):
		RecentlyUsed.__init__(self, name, icon)
		self.mimetype_list = mimetype_list

	def include_item(self, item):
		item_mime = item.get_mimetype()
		for mimetype in self.mimetype_list:
			if hasattr(mimetype, "match") and mimetype.match(item_mime) \
				   or item_mime == mimetype:
				return True
		return False


class RecentlyUsedDocumentsSource(RecentlyUsedOfMimeType):
	### FIXME: This is lame, we should generate this list somehow.
	DOCUMENT_MIMETYPES = [
		# Covers:
		#	vnd.corel-draw
		#	vnd.ms-powerpoint
		#	vnd.ms-excel
		#	vnd.oasis.opendocument.*
		#	vnd.stardivision.*
		#	vnd.sun.xml.*
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
		]
	
	def __init__(self):
		RecentlyUsedOfMimeType.__init__(self,
										name=_("Documents"),
										icon="stock_new-presentation",
										mimetype_list=self.DOCUMENT_MIMETYPES)
		self.name = _("Documents")
		self.comment = " documnets opened"
	def get_items_uncached(self):
		print "---------------------------------------------------------------------------"
		for item in RecentlyUsedOfMimeType.get_items_uncached(self):
			print item.name
			counter = 0
			info = recent_model.recent_manager.lookup_item(item.uri)
			for app in info.get_applications():
				appinfo=info.get_application_info(app)
				counter=counter+appinfo[1]
			yield Data(name= item.name,uri=item.get_uri(), timestamp=item.timestamp,count=counter,use=item.use ,type="Documents", mimetype=item.mimetype)
				  
class RecentlyUsedOthersSource(RecentlyUsedOfMimeType):
	### FIXME: This is lame, we should generate this list somehow.
	DOCUMENT_MIMETYPES = [
		# Covers:
		#	vnd.corel-draw
		#	vnd.ms-powerpoint
		#	vnd.ms-excel
		#	vnd.oasis.opendocument.*
		#	vnd.stardivision.*
		#	vnd.sun.xml.*
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
		]
	
	def __init__(self):
		RecentlyUsedOfMimeType.__init__(self,
										name=_("Other"),
										icon="applications-other",
										mimetype_list=self.DOCUMENT_MIMETYPES)
		self.name = _("Other")
		self.comment = " other opened"
	def get_items_uncached(self):
		print "---------------------------------------------------------------------------"
		for item in RecentlyUsedOfMimeType.get_items_uncached(self):
			print item.name
			counter = 0
			info = recent_model.recent_manager.lookup_item(item.uri)
			for app in info.get_applications():
				appinfo=info.get_application_info(app)
				counter=counter+appinfo[1]
			yield Data(name= item.name,uri=item.get_uri(), timestamp=item.timestamp,count=counter,use=item.use, type="Other", mimetype=item.mimetype)
			
class RecentlyUsedImagesSource(RecentlyUsedOfMimeType):
	### FIXME: This is lame, we should generate this list somehow.
	DOCUMENT_MIMETYPES = [
		# Covers:
		#	vnd.corel-draw
		re.compile("application/vnd.corel-draw"),
		# Covers: x-kword, x-kspread, x-kpresenter, x-killustrator
		re.compile("application/x-k(illustrator)"),
		re.compile("image/*"),
		]
	
	def __init__(self):
		RecentlyUsedOfMimeType.__init__(self,
										name=_("Images"),
										icon="gnome-mime-image",
										mimetype_list=self.DOCUMENT_MIMETYPES)
		self.name = _("Images")
		self.comment = " images displayed"
	
	
	def get_items_uncached(self):
		for item in RecentlyUsedOfMimeType.get_items_uncached(self):
				counter = 0
				info = recent_model.recent_manager.lookup_item(item.uri)
				for app in info.get_applications():
					appinfo=info.get_application_info(app)
					counter=counter+appinfo[1]
				yield Data(name= item.name,uri=item.get_uri(), timestamp=item.timestamp,count=counter,use=item.use, type="Images", mimetype=item.mimetype)
		
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
										mimetype_list=self.MEDIA_MIMETYPES)
		self.name = _("Music")
		self.comment = " Music listened to"
	def get_items_uncached(self):
		for item in RecentlyUsedOfMimeType.get_items_uncached(self):
				counter = 0
				info = recent_model.recent_manager.lookup_item(item.uri)
				for app in info.get_applications():
					appinfo=info.get_application_info(app)
					counter=counter+appinfo[1]
				yield Data(name= item.name,uri=item.get_uri(), timestamp=item.timestamp,count=counter,use=item.use, type="Music", mimetype=item.mimetype)
			   
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
										mimetype_list=self.MEDIA_MIMETYPES)
		
		self.comment = " videos watched"
		
	def get_items_uncached(self):
		for item in RecentlyUsedOfMimeType.get_items_uncached(self):
				counter = 0
				info = recent_model.recent_manager.lookup_item(item.uri)
				for app in info.get_applications():
					appinfo=info.get_application_info(app)
					counter=counter+appinfo[1]
				yield Data(name= item.name,uri=item.get_uri(), timestamp=item.timestamp,count=counter,use=item.use, type="Videos", mimetype=item.mimetype)
			 


recent_model = RecentlyUsedManagerGtk()
