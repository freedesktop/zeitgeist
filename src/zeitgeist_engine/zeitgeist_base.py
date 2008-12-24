import datetime
import gc
import string
import sys
import time
import os
from threading import Thread

import gobject
import gtk
from gettext import ngettext, gettext as _
import glob

from zeitgeist_util import Thumbnailer,icon_factory, launcher,difffactory

class Data(gobject.GObject):
	__gsignals__ = {
		"reload" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
		"open" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
		}

	def __init__(self,
				 uri = None,
				 name = None,
				 comment = "",
				 timestamp = 0,
				 mimetype = "XYZ",
				 icon = None,
				 tags = "",
				 count=1,
				 use = "first use",
				 type = "N/A"):
		gobject.GObject.__init__(self)
		
		
		self.uri = uri
		self.name = name
		self.count = count
		self.comment = comment
		self.mimetype = mimetype
		self.use = use
		self.diff=""
		
		# Timestamps
		# TODO: Remove all of the below attributes except for self.datestring and either self.timestamp or self.ctimestamp
		# The conversion between different formats and between integers and strings is processor intensive and uses up 
		# extra memory. A better way to do this would be to add functions to generate the time and/or date based on the
		# timestamp _only_ when it's needed. It _may_ make sense to cache those strings after they've been created.
		self.timestamp = timestamp
		self.time =  datetime.datetime.fromtimestamp(self.timestamp).strftime(_("%l:%M:%S %p"))
		# format is "weekday day month year"
		self.datestring =  datetime.datetime.fromtimestamp(self.timestamp).strftime(_("%a %d %b %Y"))
		
		self.type = type
		self.icon = icon
		self.tags = tags
		self.thumbnailer = None
		self.original_source = None
		
		
	def get_icon(self, icon_size):
		try:
			if self.uri == "gzg/twitter":
				loc = glob.glob(os.path.expanduser("~/.Zeitgeist/twitter.png"))
				self.icon = gtk.gdk.pixbuf_new_from_file_at_size(loc[0], -1, int(24))
			elif self.type=="Twitter":
				loc = glob.glob(os.path.expanduser("~/.Zeitgeist/twitter.png"))
				self.icon = gtk.gdk.pixbuf_new_from_file_at_size(loc[0], -1, int(16))
			elif self.uri.find("http") > -1 or self.uri.find("ftp") > -1:
			         self.icon="firefox"
			elif self.mimetype =="x-tomboy/note":
				    self. icon="stock_notes"
		except:
			pass
		
		if self.icon:
			  return icon_factory.load_icon(self.icon, icon_size)
		if not self.thumbnailer:
			  self.thumbnailer = Thumbnailer(self.get_uri(), self.get_mimetype())
		return self.thumbnailer.get_icon(icon_size, self.timestamp)
		
		
	def get_mimetype(self):
		return self.mimetype

	def get_uri(self):
		return self.uri

	def get_name(self):
		return self.name

	def get_time(self):
		return self.time.strip()

	def get_comment(self):
		return self.comment

	def do_open(self):
		
		if self.mimetype =="x-tomboy/note":
			uri_to_open = "note://tomboy/%s" % os.path.splitext(os.path.split(self.get_uri())[1])[0]
		else:
			uri_to_open = self.get_uri()
		if uri_to_open:
			self.timestamp = time.time()
			launcher.launch_uri(uri_to_open, self.get_mimetype())
		else:
			pass
			#print " !!! Data has no URI to open: %s" % self
	
	def open(self):
		self.emit("open")
		
	def open_from_timestamp(self):
		path = difffactory.restore_file(self)
		launcher.launch_uri(path, self.get_mimetype())
		del path
		gc.collect()
		
	def populate_popup(self, menu):
		open = gtk.ImageMenuItem (gtk.STOCK_OPEN)
		open.connect("activate", lambda w: self.open())
		open.show()
		menu.append(open)

		'''
		if self.type=="Documents" or self.type=="Other":
			timemachine = gtk.MenuItem("Open from timestamp")
			timemachine.connect("activate", lambda w: self.open_from_timestamp())
			timemachine.show()
			menu.append(timemachine)
			del timemachine
		'''
		
		relate = gtk.MenuItem("get relationships")
		relate.connect("activate", lambda w:  self.relate())
		relate.show()
		menu.append(relate)
		
		tag = gtk.MenuItem("Edit Tags")
		tag.connect("activate", lambda w:  self.tag_item())
		tag.show()
		menu.append(tag)
		
		del open,tag,menu
	
	def relate(self,x=None):
		self.emit("reload")
	
	def tag_item(self):
		taggingwindow = gtk.Window()
		taggingwindow.set_border_width(5)
		taggingwindow.set_size_request(400,100)
		taggingwindow.set_title("Edit Tags for " + self.get_name())
		textview=gtk.TextView()
			
		textview.get_buffer().set_text(self.tags)  
		
		okbtn = gtk.Button("Add")
		cbtn = gtk.Button("Cancel")
		cbtn.connect("clicked", lambda w: taggingwindow.destroy())
		okbtn.connect("clicked",lambda w: self.set_tags(textview.get_buffer().get_text(*textview.get_buffer().get_bounds()) ))
		okbtn.connect("clicked",lambda w:  taggingwindow.destroy())
		vbox=gtk.VBox()
		hbox=gtk.HBox()
		hbox.pack_start(okbtn)
		hbox.pack_start(cbtn)
		vbox.pack_start(textview,True,True,5)
		vbox.pack_start(hbox,False,False)
		taggingwindow.add(vbox)
		taggingwindow.show_all()
		
	def set_tags(self, tags):
		from zeitgeist_datasink import datasink
		self.tags = tags
		datasink.update_item(self)
		
		
class DataProvider(Data, Thread):
	# Clear cached items after 4 minutes of inactivity
	CACHE_CLEAR_TIMEOUT_MS = 1000 * 60 * 4
	
	def __init__(self,
				name=None,
				icon=None,
				comment=None,
				uri=None,
				filter_by_date=True):
		
		# Initialize superclasses
		Data.__init__(self, name=name, icon=icon, comment=comment,
			uri=uri, mimetype="zeitgeist/item-source")
		Thread.__init__(self)
		
		# Set attributes
		self.filter_by_date = filter_by_date
		self.clear_cache_timeout_id = None
		
		# Clear cached items on reload
		self.connect("reload", lambda x: self.set_items(None))
		self.hasPref = None
		self.counter = 0
		self.needs_view=True
		self.active=True
	
	def run(self):
		self.get_items()
	
	def get_items(self, min=0, max=sys.maxint):
		'''
		Return cached items if available, otherwise get_items_uncached() is
		called to create a new cache, yielding each result along the way.  A
		timeout is set to invalidate the cached items to free memory.
		'''
		
		if self.clear_cache_timeout_id:
			gobject.source_remove(self.clear_cache_timeout_id)
		self.clear_cache_timeout_id = gobject.timeout_add(DataProvider.CACHE_CLEAR_TIMEOUT_MS, lambda: self.set_items(None))
		
		for i in self.get_items_uncached():
			if i.timestamp >= min and i.timestamp <max:
				yield i
				
		gc.collect()
				
	def get_items_uncached(self):
		'''Subclasses should override this to return/yield Datas. The results
		will be cached.'''
		return []

	def set_items(self, items):
		'''Set the cached items.  Pass None for items to reset the cache.'''
		self.items = items
		del items
		gc.collect()
		
	   # delitems
	
	def set_active(self,bool):
		self.active=bool
		del bool
		
	def get_active(self):
		return self.active

	
	def items_contains_uri(self,items,uri):
		for i in items:
			if i.uri == uri:
				return True
		return False
	
	def comparecount(self,a,b):
		return cmp(a.type, b.type)
	
	def comparecount(self,a, b):
		return cmp(b.count, a.count) # compare as integers
	
	def comparetime(self,a, b):
		return cmp(a.timestamp, b.timestamp) # compare as integers
