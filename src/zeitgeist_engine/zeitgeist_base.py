import datetime
import gc
import sys
import time
import os
from threading import Thread
import gobject
from gettext import ngettext, gettext as _


class Data(gobject.GObject):
	
	__gsignals__ = {
		"reload" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
		"relate" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
		"open" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
	}
	
	def __init__(self,
				 uri		= None,
				 name		= None,
				 comment	= "",
				 timestamp	= 0,
				 mimetype	= "N/A",
				 icon		= None,
				 tags		= "",
				 count		= 1,
				 use		= "first use",
				 type		= "N/A",
				 bookmark	= False):
		
		gobject.GObject.__init__(self)
		
		# Remove characters that might be interpreted by pango as formatting
		try:
			name = name.replace("<","")
			name = name.replace(">","")
		except:
			pass
		
		self.uri = uri
		self.name = name
		self.count = count
		self.comment = comment
		self.mimetype = mimetype
		self.use = use
		self.diff = ""
		self.bookmark = bookmark
		# Timestamps
		self.timestamp = timestamp
		self.time =  datetime.datetime.fromtimestamp(self.timestamp).strftime(_("%l:%M %p")).strip()
		self.datestring =  datetime.datetime.fromtimestamp(self.timestamp).strftime(_("%a %d %b %Y"))
		
		self.type = type
		self.icon = icon
		self.tags = tags
		self.original_source = None
	
	def get_timestamp(self):
		return self.timestamp
	
	def get_icon_string(self):
		return self.icon
	
	def get_mimetype(self):
		return self.mimetype
	
	def get_type(self):
		return self.type

	def get_uri(self):
		return self.uri

	def get_name(self):
		return self.name

	def get_time(self):
		return self.time

	def get_comment(self):
		return self.comment
	
	def get_count(self):
		return self.count
	
	def get_use(self):
		return self.use
	
	def get_bookmark(self):
		return self.bookmark
	
	def get_tags(self):
		return [tag for tag in self.tags.split(",") if tag]


class DataProvider(Data, Thread):
	# Clear cached items after 4 minutes of inactivity
	CACHE_CLEAR_TIMEOUT_MS = 1000 * 60 * 4
	
	__gsignals__ = {
		"reload_send" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_PYOBJECT, ()),
	}
	
	def __init__(self,
				name=None,
				icon=None,
				comment=None,
				uri=None,
				filter_by_date=True):
		
		# Initialize superclasses
		Thread.__init__(self)
		Data.__init__(self, name=name, icon=icon,comment=comment,uri=uri, mimetype="zeitgeist/item-source")
		
		# Set attributes
		self.filter_by_date = filter_by_date
		self.clear_cache_timeout_id = None
		
		# Clear cached items on reload
		self.connect("reload", lambda x: self.set_items(None))
		self.hasPref = None
		self.counter = 0
		self.needs_view = True
		self.active = True
	
	def run(self):
		self.get_items()
	
	def get_items(self, min=0, max=sys.maxint):
		'''
		Return cached items if available, otherwise get_items_uncached() is
		called to create a new cache, yielding each result along the way.  A
		timeout is set to invalidate the cached items to free memory.
		'''
		
		for i in self.get_items_uncached():
			if i.timestamp >= min and i.timestamp < max:
				yield i
			
		gc.collect()
	
	def get_items_uncached(self):
		'''Subclasses should override this to return/yield Datas. The results
		will be cached.'''
		return []

	def set_items(self, items):
		'''Set the cached items. Pass None for items to reset the cache.'''
		self.items = items
		gc.collect()
	
	def set_active(self,bool):
		self.active = bool
	
	def get_active(self):
		return self.active
	
	def items_contains_uri(self,items,uri):
		if uri in (i.uri for i in items):
			return True
		return False
