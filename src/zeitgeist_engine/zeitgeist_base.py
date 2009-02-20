import datetime
import gc
import string
import sys
import time
import os
from threading import Thread

import gobject
import gtk
import glob
from gettext import ngettext, gettext as _

from zeitgeist_util import Thumbnailer, icon_factory, launcher, difffactory

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
		
		# Remove characters that might be interpreted by pango as formatting
		try:
			name = name.replace("<","")
			name = name.replace(">","")
		except:
			pass
			
		self.name=name
		self.count = count
		self.comment = comment
		self.mimetype = mimetype
		self.use = use
		self.diff=""
		
		
		# Timestamps
		self.timestamp = timestamp
		self.time =  datetime.datetime.fromtimestamp(self.timestamp).strftime(_("%l:%M:%S %p"))
		self.datestring =  datetime.datetime.fromtimestamp(self.timestamp).strftime(_("%d %b %Y"))
		
		self.type = type
		self.icon = icon
		self.tags = tags
		self.thumbnailer = None
		self.original_source = None
		self.textview = gtk.TextView()
		
		
	def get_icon(self, icon_size):
		
		temp = self.get_icon_static(icon_size)
		if temp != None:
			self.icon = temp
		if self.icon:
			return icon_factory.load_icon(self.icon, icon_size)
		if not self.thumbnailer:
			  self.thumbnailer = Thumbnailer(self.get_uri(), self.get_mimetype())
		return self.thumbnailer.get_icon(icon_size, self.timestamp)
	
	def get_icon_static(self,icon_size):
		try:
			if self.uri == "gzg/twitter":
				loc = glob.glob(os.path.expanduser("~/.Zeitgeist/twitter.png"))
				self.icon = gtk.gdk.pixbuf_new_from_file_at_size(loc[0], -1, int(24))
			elif self.type=="Twitter":
				loc = glob.glob(os.path.expanduser("~/.Zeitgeist/twitter.png"))
				self.icon = gtk.gdk.pixbuf_new_from_file_at_size(loc[0], -1, int(16))
			elif self.uri.find("http") > -1 or self.uri.find("ftp") > -1:
				self.icon="gnome-globe"
			elif self.mimetype =="x-tomboy/note":
				self. icon="stock_notes"
			elif self.type=="Mail":
				self. icon="stock_mail"
			return self.icon
		except:
			return None
		
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
	
	def get_tags(self):
		tags = []
		for tag in self.tags.split(","):
			tags.append(tag)
		return tags
					
	def open(self):
		self.emit("open")
		
	def open_from_timestamp(self):
		path = difffactory.restore_file(self)
		launcher.launch_uri(path, self.get_mimetype())
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
		
		relate = gtk.MenuItem("Show related files")
		relate.connect("activate", lambda w:  self.relate())
		relate.show()
		menu.append(relate)
		
		tag = gtk.MenuItem("Edit Tags")
		tag.connect("activate", lambda w:  self.tag_item())
		tag.show()
		menu.append(tag)
	
	def relate(self, x=None):
		self.emit("reload")
	
	def tag_item(self):
		taggingwindow = gtk.Window()
		taggingwindow.set_border_width(5)
		taggingwindow.set_size_request(400,-1)
		taggingwindow.set_title("Edit Tags for " + self.get_name())
			
		self.textview.get_buffer().set_text(self.tags)	
		
		okbtn = gtk.Button("Add")
		cbtn = gtk.Button("Cancel")
		cbtn.connect("clicked", lambda w: taggingwindow.destroy())
		okbtn.connect("clicked",lambda w: self.set_tags(self.textview.get_buffer().get_text(*self.textview.get_buffer().get_bounds()) ))
		okbtn.connect("clicked",lambda w:  taggingwindow.destroy())
		vbox=gtk.VBox()
		hbox=gtk.HBox()
		hbox.pack_start(okbtn)
		hbox.pack_start(cbtn)
		vbox.pack_start(self.textview,True,True,5)

		self.tbox = self.get_tagbox()
		
		vbox.pack_start(self.tbox,True,True)
		vbox.pack_start(hbox,False,False)
		
		
		taggingwindow.add(vbox)
		taggingwindow.show_all()
		
	def set_tags(self, tags):
		from zeitgeist_datasink import datasink
		self.tags = tags
		datasink.update_item(self)

	def get_tagbox(self):
		# Initialize superclass
		tbox = gtk.VBox()
		label = gtk.Label("Most used tags")
		# Add a frame around the label
		evbox = gtk.EventBox()
		evbox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
		evbox1 = gtk.EventBox()
		evbox1.set_border_width(1)
		evbox1.add(label)
		evbox.add(evbox1)
		#tbox.set_size_request(400, -1)
		label.set_padding(5, 5) 
		tbox.pack_start(evbox, False, False)
		
		scroll = gtk.ScrolledWindow()
		view = gtk.HBox()
		view.set_size_request(-1, 40)
		scroll.add(view)
		scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		tbox.pack_start(scroll,False,False)
		tbox.show_all()
		
		self.get_common_tags(view)
		return tbox
	
	def get_common_tags(self, view):
		from zeitgeist_datasink import datasink
		for tag in datasink.get_most_used_tags(10):
			print tag[0]
			btn = gtk.ToggleButton(tag[0])
			btn.set_relief(gtk.RELIEF_NONE)
			btn.set_focus_on_click(False)
			#label.set_use_underline(True)
			view.pack_start(btn,False,False)
			btn.connect("toggled",self.toggle_tags)
		view.show_all()
		
	def toggle_tags(self, x=None):
		tags = self.tags
		if x.get_active():
			if tags.find(x.get_label()) == -1:
				if tags.strip()=="":
					tags = x.get_label()
				else:
					tags = tags+","+x.get_label()
		else:
			if tags.find(","+x.get_label()) > -1:
				 tags = tags.replace(","+x.get_label(), "")
			elif tags.find(x.get_label()+",") > -1:
				 tags = tags.replace(x.get_label()+"," ,",")
			elif tags.find(x.get_label()) > -1:
				 tags = tags.replace(x.get_label(), "")
		
		while tags.find(",,")>-1:
				 tags = tags.replace(",," ,",")
				 tags.strip()
						
		if tags.strip().startswith(",") == True:
			tags = tags.replace(",", "",1)
		
		self.tags=tags
		
		self.textview.get_buffer().set_text(self.tags)	
		
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
		gc.collect()
	
	def set_active(self,bool):
		self.active = bool
		
	def get_active(self):
		return self.active

	def items_contains_uri(self,items,uri):
		for i in items:
			if i.uri == uri:
				return True
		return False