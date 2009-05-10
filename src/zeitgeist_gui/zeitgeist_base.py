# -.- encoding: utf-8 -.-

import datetime
import gc
import time
import os
import gobject
import gtk
import gettext

from zeitgeist_gui.zeitgeist_util import icon_factory, thumbnailer, launcher, favicons
# Some imports are in-place to avoid a circular dependency


class Data(gobject.GObject):
	
	__gsignals__ = {
		"relate" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
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
		if name:
			name = name.replace("<","")
			name = name.replace(">","")
			
		
		self.uri = uri.replace("%20"," ")
		self.name = name
		self.count = count
		self.comment = comment
		self.mimetype = mimetype
		self.use = use
		self.diff = ""
		self.bookmark = bookmark
		self.timestamp = timestamp
		
		self.type = type
		self.icon = icon
		self.tags = tags
		self.thumbnailer = None
		self.original_source = None
		self.textview = None
		
		self.exists = exists(self.uri)
	
	def get_timestamp(self):
		return self.timestamp
	
	def get_datestring(self):
		return datetime.datetime.fromtimestamp(self.timestamp).strftime("%a %d %b %Y")
	
	def get_icon(self, icon_size):
		if  self.exists and self.uri.startswith("file"):
			thumb = thumbnailer.get_icon(self.get_uri(), self.get_mimetype(), icon_size, self.timestamp)
			return thumb
		
		'''
		if self.uri.startswith("http") and not self.comment.strip()=="":
			if self.comment[0] == ".":
				uri = "http://" + self.comment[1:] +"/"
			else: 
				uri = "http://" + self.comment +"/"
			icon =  favicons.get_icon(uri)
			if icon:
				return icon
		'''
		
		if self.icon:
			icon =  icon_factory.load_icon(self.icon, icon_size)
			if not self.exists:
				icon = icon_factory.transparentize(icon,75)
			return icon
		
		return None
	
	def open(self):
		if self.get_mimetype() == "x-tomboy/note":
			uri_to_open = "note://tomboy/%s" % os.path.splitext(os.path.split(self.get_uri())[1])[0]
		else:
			uri_to_open = self.get_uri()
		if uri_to_open:
			self.timestamp = time.time()
			launcher.launch_uri(uri_to_open, self.get_mimetype())
	
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
		# TODO: Should it be possible to switch to 12-hour clock ("%l:%M %p")?
		return datetime.datetime.fromtimestamp(self.timestamp).strftime("%H:%M").strip()
	
	def get_comment(self):
		return self.comment
	
	def get_count(self):
		return self.count
	
	def get_use(self):
		return self.use
	
	def get_bookmark(self):
		return self.bookmark
	
	def get_tags(self):
		return [tag.strip() for tag in self.tags.split(",") if tag.strip()]
	
	def open_from_timestamp(self):
		'''
		path = difffactory.restore_file(self)
		launcher.launch_uri(path, self.get_mimetype())
		'''
		pass
	
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
			bookmark = gtk.MenuItem(_("Unbookmark"))
		else:
			bookmark = gtk.MenuItem(_("Bookmark"))
		bookmark.connect("activate", lambda w: self.add_bookmark())
		bookmark.show()
		menu.append(bookmark)
		
		relate = gtk.MenuItem(_("Show related files"))
		relate.connect("activate", lambda w: self.relate())
		relate.show()
		menu.append(relate)
		
		tag = gtk.MenuItem(_("Edit tags..."))
		tag.connect("activate", lambda w: self.tag_item())
		tag.show()
		menu.append(tag)
		
		# Add a separator (we could use SeparatorMenuItem but that's
		# just an alias for calling MenuItem without arguments).
		tag = gtk.MenuItem()
		tag.show()
		menu.append(tag)
		
		tag = gtk.MenuItem(_("Delete item from Zeitgeist"))
		tag.connect("activate", lambda w: self.delete_item())
		tag.show()
		menu.append(tag)
	
	def relate(self, x=None):
		self.emit("relate")
	
	def add_bookmark(self, x=None):
		
		self.bookmark = not self.bookmark
		from zeitgeist_engine_wrapper import engine
		engine.update_item(self)
		from zeitgeist_gui.zeitgeist_bookmarker import bookmarker
		bookmarker.reload_bookmarks()
	
	def set_bookmark(self, bookmark):
		
		self.bookmark = bookmark
		from zeitgeist_engine_wrapper import engine
		engine.update_item(self)
		from zeitgeist_gui.zeitgeist_bookmarker import bookmarker
		bookmarker.reload_bookmarks()
	
	def tag_item(self):
		if not self.textview:
			self.textview = gtk.TextView()
		taggingwindow = gtk.Window()
		taggingwindow.set_border_width(5)
		taggingwindow.set_size_request(400,-1)
		taggingwindow.set_title(_("Edit tags for %s") % self.get_name())
		
		self.textview.get_buffer().set_text(self.tags)	
		
		# Use real Cancel/OK buttons. Those are not compliant with HIG.
		okbtn = gtk.Button(_("Add"))
		cbtn = gtk.Button(_("Cancel"))
		cbtn.connect("clicked", lambda w: taggingwindow.destroy())
		okbtn.connect("clicked", lambda w: self.set_tags(self.textview.get_buffer().get_text(*self.textview.get_buffer().get_bounds()) ))
		okbtn.connect("clicked", lambda w: taggingwindow.destroy())
		vbox = gtk.VBox()
		hbox = gtk.HBox()
		hbox.pack_start(okbtn)
		hbox.pack_start(cbtn)
		vbox.pack_start(self.textview,True,True,5)
		
		self.tbox = self.get_tagbox()
		vbox.pack_start(self.tbox, True,True)
		vbox.pack_start(hbox, False,False)
		
		taggingwindow.add(vbox)
		taggingwindow.show_all()
	
	def delete_item(self):
		from zeitgeist_engine_wrapper import engine
		engine.delete_item(self.uri)
		engine.emit_signal_updated() # TODO: No need to reload, just remove the single item
	
	def set_tags(self, tags):
		self.tags = tags
		from zeitgeist_engine_wrapper import engine
		engine.update_item(self)
	
	def get_tagbox(self):
		# Initialize superclass
		tbox = gtk.VBox()
		label = gtk.Label(_("Most used tags"))
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
		from zeitgeist_engine_wrapper import engine
		for tag in engine.get_most_used_tags(10, 0, 0):
			# TODO: This code is duplicated in zeitgeist_widgets.py
			btn = gtk.ToggleButton(tag)
			btn.set_relief(gtk.RELIEF_NONE)
			btn.set_focus_on_click(False)
			view.pack_start(btn, False, False)
			btn.connect("toggled", self.toggle_tags)
		view.show_all()
	
	def toggle_tags(self, x, *discard):
		# TODO: Clean this mess up. Use a list comprehension or sth.
		
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
		
		self.tags = tags
		self.textview.get_buffer().set_text(self.tags)

	
	def has_search(self, search):
		if search.strip() == "":
			return True
		if self.comment.lower().find(search) > -1:
			return True
		if self.name.lower().find(search) > -1:
			return True
		for tag in self.get_tags():
			if tag == search:
				return True
		return False


def objectify_data(item_list):
	return Data(
			timestamp = item_list[0],
			uri = item_list[1], # uri
            name = item_list[2], # name
            comment = item_list[3], # comment
            tags = item_list[4], # tags
            use = item_list[5] or "first use", # use
            icon =  item_list[6], # icon
            bookmark = item_list[7], # bookmark
            mimetype = item_list[8] or "N/A", # mimetype
            count = item_list[9] or 1, # count
            type = item_list[10] or "N/A", # type
            )


def exists(uri):
	if not uri.startswith("file"):
		return True
	
	if os.path.exists(uri[7:]):
		return True
	
	return False
