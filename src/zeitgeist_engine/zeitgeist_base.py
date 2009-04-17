import datetime
import gc
import sys
import time
import os
from threading import Thread
import gobject
from gettext import ngettext, gettext as _

class DataProvider(gobject.GObject, Thread):
	# Clear cached items after 4 minutes of inactivity
	CACHE_CLEAR_TIMEOUT_MS = 1000 * 60 * 4
	
	__gsignals__ = {
		"reload" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
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
		gobject.GObject.__init__(self)
		
		self.name = name
		self.icon = icon
		self.comment = comment
		self.uri = uri
		self.mimetype = "zeitgeist/item-source"
		self.timestamp = 0
		
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
	
	def get_name(self):
		return self.name
	
	def get_icon_string(self):
		return self.icon
	
	def get_items(self, min=0, max=sys.maxint):
		'''
		Return cached items if available, otherwise get_items_uncached() is
		called to create a new cache, yielding each result along the way.  A
		timeout is set to invalidate the cached items to free memory.
		'''
		
		for i in self.get_items_uncached():
			if i["timestamp"] >= min and i["timestamp"] < max:
				yield i
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
	
	def items_contains_uri(self, items, uri):
		if uri in (item["uri"] for item in items):
			return True
		return False
