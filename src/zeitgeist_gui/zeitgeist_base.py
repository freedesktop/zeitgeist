import datetime
import gc
import sys
import time
import os
import gobject
import gtk
from gettext import ngettext, gettext as _

from zeitgeist_engine.zeitgeist_util import icon_factory, launcher, difffactory, thumbnailer
from zeitgeist_engine.zeitgeist_datasink import datasink
from zeitgeist_engine.zeitgeist_base import DataProvider
from zeitgeist_gui.zeitgeist_dbus import iface

class Data(gobject.GObject):
	
	__gsignals__ = {
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
		self.thumbnailer = None
		self.original_source = None
		self.textview = gtk.TextView()
	
	def get_timestamp(self):
		return self.timestamp
	
	def get_icon(self, icon_size):
			temp = self.icon
			
			if temp != None:
				self.icon = temp
			
			if self.icon:
				icon =  icon_factory.load_icon(self.icon, icon_size)
				return icon
			
			thumb = thumbnailer.get_icon(self.get_uri(),self.get_mimetype(),icon_size, self.timestamp)
			return thumb
	
	def get_icon_string(self):
		return self.icon
	
	def get_icon_static_done(self, icon_size):
		if self.icon:
			return icon_factory.load_icon(self.icon, icon_size)
	
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
		return [tag for tag in self.tags.split(",") if tag]
	
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
		if self.bookmark:
			bookmark = gtk.MenuItem("Unbookmark")
			bookmark.connect("activate", lambda w: self.add_bookmark())
			bookmark.show()
			menu.append(bookmark)
		else:
			bookmark = gtk.MenuItem("Bookmark")
			bookmark.connect("activate", lambda w: self.add_bookmark())
			bookmark.show()
			menu.append(bookmark)
		
		relate = gtk.MenuItem("Show related files")
		relate.connect("activate", lambda w:  self.relate())
		relate.show()
		menu.append(relate)
		
		tag = gtk.MenuItem("Edit Tags")
		tag.connect("activate", lambda w:  self.tag_item())
		tag.show()
		menu.append(tag)
		
		# Add a separator (we could use SeparatorMenuItem but that's
		# just an alias for calling MenuItem without arguments).
		tag = gtk.MenuItem()
		tag.show()
		menu.append(tag)
		
		tag = gtk.MenuItem("Delete item")
		tag.connect("activate", lambda w:  self.delete_item())
		tag.show()
		menu.append(tag)
	
	def relate(self, x=None):
		self.emit("relate")
		pass
	
	def add_bookmark(self, x=None):
		if self.bookmark == False:
			self.bookmark = True
		else:
			self.bookmark = False
		datasink.update_item(self)
		bookmarker.reload_bookmarks()
	
	def set_bookmark(self, bookmark):
		self.bookmark = bookmark
		datasink.update_item(self)
		bookmarker.reload_bookmarks()
		
	def tag_item(self):
		taggingwindow = gtk.Window()
		taggingwindow.set_border_width(5)
		taggingwindow.set_size_request(400,-1)
		taggingwindow.set_title(_("Edit Tags for %s") % self.get_name())
		
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
	
	def delete_item(self):
		from zeitgeist_datasink import datasink
		datasink.delete_item(self)
	
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
			if tag:
				btn = gtk.ToggleButton(tag)
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


class Bookmarker(DataProvider):
	
	def __init__(self,
				name=_("Bookmarker"),
				icon=None,
				uri="source:///Bookmarker"):
		
		DataProvider.__init__(self)
		self.bookmarks=[]
		self.reload_bookmarks()
		
	def get_bookmark(self,uri):
		if self.bookmarks.count(uri) > 0:
			return True
		return False
	
	def add_bookmark(self,item):
		if self.bookmarks.count(item.uri) == 0:
			self.bookmarks.append(item.uri)
	
	def reload_bookmarks(self):
		print "------------------------------------"
		self.bookmarks = []
		for item in datasink.get_bookmarks():
			self.add_bookmark(item)
			print "bookmarking "+item.uri
		print "------------------------------------"
		iface.emit_signal_updated()
	
	def get_items_uncached(self):
		for i in datasink.get_bookmarks():
			yield i

bookmarker = Bookmarker()
