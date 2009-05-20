# -.- encoding: utf-8 -.-

import datetime
import gc
import os
import time
import sys
import gtk
import gobject
import pango
import gettext

from zeitgeist.gui.zeitgeist_util import launcher, icon_factory
from zeitgeist.gui.zeitgeist_util import launcher, color_palette
from zeitgeist.gui.zeitgeist_engine_wrapper import engine
from zeitgeist.gui.zeitgeist_bookmarker import bookmarker
from zeitgeist.shared.zeitgeist_shared import *
from zeitgeist import config

today = str(datetime.datetime.today().strftime("%d %m %Y")).split(" ")

class CellRendererPixbuf(gtk.CellRendererPixbuf):
	
	__gsignals__ = {
		'toggled': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE,
		(gobject.TYPE_STRING,))
	}
	def __init__(self):
		gtk.CellRendererPixbuf.__init__(self)
		self.set_property('mode', gtk.CELL_RENDERER_MODE_ACTIVATABLE)
	
	def do_activate(self, event, widget, path, background_area, cell_area, flags):
		model = widget.get_model()
		if model[path][6]:
			self.emit("toggled",path)
		
class DataIconView(gtk.TreeView):
	'''
	Icon view which displays Datas in the style of the Nautilus horizontal mode,
	where icons are right aligned and each column is of a uniform width.  Also
	handles opening an item and displaying the item context menu.
	'''
	
	def __init__(self,parentdays=False):
		
		gtk.TreeView.__init__(self)
		
		self.parentdays = parentdays
		self.datestring = None
		
		self.set_property("can-default", False)
		self.set_property("can-focus", False)
		
		TARGET_TYPE_TEXT = 80
		TARGET_TYPE_PIXMAP = 81
		
		self.fromImage = [ ( "text/plain", 0, TARGET_TYPE_TEXT ), ( "image/x-xpixmap", 0, TARGET_TYPE_PIXMAP ) ]
		
		self.active_image = gtk.gdk.pixbuf_new_from_file_at_size(
			"%s/bookmark-new.svg" % config.pkgdatadir, 24, 24) 
		
		self.inactive_image = icon_factory.greyscale(self.active_image)
		self.inactive_image = icon_factory.transparentize(self.inactive_image,50)

		#self.connect('window-state-event', self.window_state_event_cb)
		self.store = gtk.TreeStore(gtk.gdk.Pixbuf, str, str, gobject.TYPE_BOOLEAN, gobject.TYPE_PYOBJECT, str,  gtk.gdk.Pixbuf)
		
		self.set_tooltip_column(5)
		
		icon_cell = gtk.CellRendererPixbuf()
		icon_cell.set_property("yalign", 0.0)
		icon_column = gtk.TreeViewColumn("",icon_cell,pixbuf=0)
		#icon_column.set_fixed_width(32)
		icon_column.set_expand(False)
		
		name_cell = gtk.CellRendererText()
		name_cell.set_property("yalign", 0.0)
		name_cell.set_property("wrap-mode", pango.WRAP_WORD_CHAR)
		name_cell.set_property("wrap-width", 125)
		name_column = gtk.TreeViewColumn(_("Name"), name_cell, markup=1)
		name_column.set_expand(True)
		name_column.set_properties("sensitive",False)
		self.name_cell = name_cell
		
		time_cell = gtk.CellRendererText()
		time_cell.set_property("yalign", 0.0)
		time_column = gtk.TreeViewColumn(_("Time"), time_cell, markup=2)
		#time_column.set_fixed_width(32)
		time_column.set_expand(False)
		
		bookmark_cell = CellRendererPixbuf()
		bookmark_cell.set_property("yalign", 0.0)
		bookmark_cell.connect("toggled", self.toggle_bookmark, self.store )
		bookmark_column = gtk.TreeViewColumn("bookmark", bookmark_cell, pixbuf =6)
		bookmark_column.set_expand(False)
				
		self.append_column(icon_column)
		self.append_column(name_column)
		self.append_column(time_column)
		self.append_column(bookmark_column)
	 
		self.set_model(self.store)
		self.set_headers_visible(False)
			
		self.set_expander_column(icon_column)
		
		self.connect("row-activated", self._open_item)
		self.connect("row-expanded", self._expand_row)
		self.connect("row-collapsed", self._collapse_row)
		self.connect("button-press-event", self._show_item_popup)
		self.connect("drag-data-get", self._item_drag_data_get)
		self.connect("drag_data_received", self.drag_data_received_data)
		self.connect("focus-out-event", self.unselect_all)
		
		self.set_double_buffered(True)
		#self.get_selection().set_mode(gtk.SELECTION_MULTIPLE)		
		
		self.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, [("text/uri-list", 0, 100)], gtk.gdk.ACTION_LINK | gtk.gdk.ACTION_COPY)
		self.enable_model_drag_dest(self.fromImage, gtk.gdk.ACTION_MOVE) 
		
		self.last_item=None
		self.last_iter = None
		
		self.intype = False
		
		self.day=None
		engine.connect("signal_updated", lambda *args: self._do_refresh_rows())
		
		#self.store.set_sort_column_id(2, gtk.SORT_ASCENDING)
		self.types = {}
		self.days={}
		self.items_uris=[]
		self.item_type_count = {}
			
	def _do_refresh_rows(self):
		
		iter = self.store.get_iter_root()
		
		try:
			item = self.store.get_value(iter, 4)
			self.check_rows(iter)
		except Exception:
			pass
		
		while True:
			try:
				iter = self.store.iter_children()
				if iter:
					iter = self.check_rows(iter)
				else:
					break
			except:
				break
	
	def check_rows(self,iter):
		item = self.store.get_value(iter, 4)
		name = self.store.get_value(iter,1)
		
		try:
			self.store.set(iter,3,bookmarker.get_bookmark(item.uri))
			icon = self.inactive_image
			if bookmarker.get_bookmark(item.uri) == True:
				icon = self.active_image
			self.store.set(iter,6,icon)
		except Exception, ex:
			pass
		
		return self.store.iter_next(iter)
	
	def _expand_row(self,model,iter,path):
		type = self.store.get_value(iter, 1)
		substrings = type.split("\n")
		type = substrings[0].replace("<span color='black'>","")
		type = type.replace("</span>","")
		type = type.strip()
		expanded_views[self.datestring][type] = True
		
	def _collapse_row(self,model,iter,path):
		type = self.store.get_value(iter, 1)
		substrings = type.split("\n")
		type = substrings[0].replace("<span color='black'>","")
		type = type.replace("</span>","")
		type = type.strip()
		expanded_views[self.datestring][type] = False
	
	
	def reload_name_cell_size(self,width):
		self.name_cell.set_property("wrap-width",width -125)
		
	def append_item(self, item, group=True):
		self._set_item(item, group=group)
	
	def prepend_item(self, item,group=True):
		self._set_item(item, False, group=group)
	
	def remove_item(self,item):
		# TODO: Maybe filtering should be done on a UI level
		pass
	
	def clear_store(self):
		self.types.clear()
		self.days.clear()
		self.day=None
		self.items_uris=[]
		self.last_item = None
		self.last_iter = None
		self.store.clear()
	
	def unselect_all(self,x=None,y=None):
		try:
			treeselection = self.get_selection()
			model, iter = treeselection.get_selected()
			self.last_item = model.get_value(iter, 4)
			treeselection.unselect_all()
		except Exception:
			pass
	
	def _open_item(self, view, path, x=None):		 
		item = self.get_selected_item()
		if item.get_mimetype() == "x-tomboy/note":
			uri_to_open = "note://tomboy/%s" % os.path.splitext(os.path.split(item.get_uri())[1])[0]
		else:
			uri_to_open = item.get_uri()
		if uri_to_open:
			item.timestamp = time.time()
			launcher.launch_uri(uri_to_open, item.get_mimetype())
	
	def get_selected_item(self):
		try:
			treeselection = self.get_selection()
			model, iter = treeselection.get_selected()
			item = model.get_value(iter, 4)
			return item
		except Exception:   
			pass
	
	def _show_item_popup(self, view, ev):
		if ev.button == 3:
			(path,col,x,y) = view.get_path_at_pos(int(ev.x),int(ev.y))
			iter = self.store.get_iter(path)
			item = self.store.get_value(iter, 4)	
			menu = gtk.Menu()
			menu.attach_to_widget(view, None)
			item.populate_popup(menu)
			menu.popup(None, None, None, ev.button, ev.time)
					
					
	
	def _item_drag_data_get(self, view, drag_context, selection_data, info, timestamp):
		# TODO: Prefer ACTION_LINK if available
		uris = []
		uris.append(self.last_item.get_uri())
		selection_data.set_uris(uris)
	
	def drag_data_received_data(self, iconview, context, x, y, selection, info, etime):
		
		data = selection.data
		if data[0:6] == "tag://":
			data = data[6:]
			try:
				drop_info = self.get_dest_row_at_pos(x, y)
				if drop_info:
					(model, paths) = self.get_selection().get_selected_rows()
					path, position = drop_info
					iter = model.get_iter(path)
					
				item = model.get_value(iter, 4)
				if item.tags.strip()=="" or item.tags == None:
					tags = data
				else:
					tags = item.tags + "," + data
				item.set_tags(tags)
				
				tooltip = self.get_tooltip(item)
				model.set_value(iter,5,tooltip)
				
			except Exception, ex:
				print ex
	
	def toggle_bookmark( self, cell, path, model ):
		"""
		Sets the toggled state on the toggle button to true or false.
		"""
		model[path][3] = not model[path][3]
		item = model[path][4]
		item.set_bookmark(model[path][3])
		
		icon = self.inactive_image
		if model[path][3] == True:
			icon = self.active_image
		
		model[path][6] = icon
				
	def _set_item(self, item, append=True, group=False, parent=False):
				
		bookmark = bookmarker.get_bookmark(item.uri)
		self.items_uris.append(item.uri)
			
		if self.last_item:
			if item.uri == self.last_item.uri:
				if  item.timestamp - self.last_item.timestamp <=10:
					return
		
		date = ""
		if not item.timestamp == -1.0:
			date = "<span size='small' color='blue'>%s</span>" % item.get_time()
		
		name = "<span color='%s'>%s</span>" % \
			("black" if item.exists else "grey", item.get_name())
		
		icon = self.inactive_image
		if bookmark == True:
			icon = self.active_image
		
		
		if not self.types.has_key(item.type):
			if group:
				self.item_type_count[item.type] = 0
			
				iter = self.store.append(None, [icon_factory.load_icon(item.icon, 24),
									 "<span size='large' color='%s'>%s</span>" % \
			("black", item.type),
									"",
									True,
									None,
									"Bookmarked "+item.type,
									None,
									])
			else:
				iter = None
			self.types[item.type] = iter
		
		if parent:
			if self.last_item and self.last_item.comment.strip() != "" and self.last_item.comment == item.comment:
				self.store.append(self.last_iter, 
					[item.get_icon(24),
					name,
					date,
					bookmark,
					item,
					self.get_tooltip(item),
					icon,
					])
		
			elif self.last_item and self.last_item.tags != "" and self.last_item.tags == item.tags:
				self.store.append(self.last_iter, 
					[item.get_icon(24),
					name,
					date,
					bookmark,
					item,
					self.get_tooltip(item),
					icon,
					])
		
		else:
			if group:
				if not expanded_views.has_key(item.get_datestring()):
					expanded_views[item.get_datestring()] = {}
				if not expanded_views[item.get_datestring()].has_key(item.type):
					expanded_views[item.get_datestring()][item.type] = False
				
				self.item_type_count[item.type] +=1
				iter = self.types[item.type] 
				if self.item_type_count[item.type] > 1:
					self.store.set(iter,1,"<span color='%s'>%s</span>"\
								    "\n<span size='small' color='blue'> (%i activities)</span>"  % \
										 ("black", item.type, self.item_type_count[item.type]) )
				else:
					self.store.set(iter,1,"<span color='%s'>%s</span>"\
								    "\n<span size='small' color='blue'> (%i activity)</span>"  % \
										 ("black", item.type, self.item_type_count[item.type]) )
				if expanded_views[item.get_datestring()][item.type]:
					path = self.store.get_path(iter)
					self.expand_row(path,True)
					
			self.last_iter = self.store.append(self.types[item.type], 
				[item.get_icon(24),
				name,#"<span size='small'>%s</span>" % name,
				date,
				bookmark,
				item,
				self.get_tooltip(item),
				icon,
				])
		
		self.datestring = item.get_datestring()
		self.last_item = item
	
	def get_tooltip(self,item):
		tooltip = item.uri + "\n\n" + item.comment
		if not len(item.tags) == 0:
			tooltip += "\n\n" + _("Tagged with:") + "\n" + ", ".join(item.tags.split(","))
		if not item.exists:	
			tooltip = _("The file has been removed from") + "\n" + tooltip
		return tooltip
		
class NewFromTemplateDialog(gtk.FileChooserDialog):
	'''
	Dialog to create a new document from a template
	'''
	
	__gsignals__ = {
		"response" : "override"
		}
	
	def __init__(self, name, source_uri):
		# Extract the template's file extension
		try:
			self.file_extension = name[name.rindex('.'):]
			name = name[:name.rindex('.')]
		except ValueError:
			self.file_extension = None
		self.source_uri = source_uri
		parent = gtk.Window()
		gtk.FileChooserDialog.__init__(self,
									   _("New Document"),
									   parent,
									   gtk.FILE_CHOOSER_ACTION_SAVE,
									   (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
										gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT))
		self.set_current_name(name)
		self.set_current_folder(os.path.expanduser("~/"))
		self.set_do_overwrite_confirmation(True)
		self.set_default_response(gtk.RESPONSE_ACCEPT)
	
	def do_response(self, response):
		if response == gtk.RESPONSE_ACCEPT:
			file_uri = self.get_filename()

			# Create a new document from the template and display it
			try:
				if not self.source_uri:
					# Create an empty file
					f = open(file_uri, 'w')
					f.close()
				else:
					shutil.copyfile(self.source_uri, file_uri)
				launcher.launch_uri(file_uri)
			except IOError:
				pass

		self.destroy()

class RelatedWindow(gtk.Window):
	
	def __init__(self):
		
		# Initialize superclass
		gtk.Window.__init__(self)
		
		self.set_resizable(True)
		self.connect("destroy", lambda w: self.destroy)
		
		self.baseitem = gtk.HBox(False)
		self.img = gtk.Image()
		self.itemlabel = gtk.Label()
		self.baseitem.pack_start(self.img,False,False,5)
		self.baseitem.pack_start(self.itemlabel,False,False,5)
		
		self.vbox=gtk.VBox()
		self.vbox.pack_start(self.baseitem,False,False,5)
		self.label = gtk.Label(_("Related files"))
		# Add a frame around the label
		self.label.set_padding(5, 5) 
		self.vbox.pack_start(self.label, False, False)
		
		self.scroll = gtk.ScrolledWindow()
		self.view = DataIconView()
		self.scroll.add_with_viewport(self.view)
		self.set_border_width(5)
		self.scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self.vbox.set_size_request(400, 400)
		self.vbox.pack_start(self.scroll)
		self.add(self.vbox)
		self.show_all()
		self.items = []
	
	def set_relation(self, item):
		'''
		Find the items that share same tags with the current item
		Later to be done by monitoring the active files
		'''
		self.img.set_from_pixbuf(item.get_icon(64))
		# TODO: Use proper, separate widgets for this
		string = item.get_name() + "\n\n" + _("Last usage:") + "\t" + \
			item.get_datestring() + " " + item.get_time() + "\n\n" + \
			_("Tags:") + "\t" + ", ".join(item.get_tags()) + "\n"
		self.itemlabel.set_label(string)
		self.set_title("GNOME Zeitgeist - " + _("Files related to %s") % item.name)
		self.view.clear_store()
		uris = {}
		from zeitgeist.gui.zeitgeist_journal_widgets import timeline
		if not item.tags == "":
			for i in timeline.items:
				for tag in item.get_tags():
					try:
						if i.tags.index(tag) >= 0:
							i.timestamp=-1.0
							uris[i.uri]=i
						else:
							pass
					except Exception: # TODO: Why this?
						pass
		items = []
		for uri in uris.keys():
			if items.count(uri) == 0:
				items.append(uri)
				self.view.append_item(uris[uri])
		
		for related_item in engine.get_related_items(item):
			if items.count(related_item.uri) == 0:
				items.append(related_item.uri)
				self.view.append_item(related_item)
		
		items = []

class DayBox(gtk.VBox):
	
	def __init__(self,date, show_date=True):
		
		gtk.VBox.__init__(self)
		self.date=date
		vbox = gtk.VBox()
		
		self.ev = gtk.EventBox()
			
		'''
		FIXME: export the code somehwere else
		This makes the headers of the days fit the tooltip color
		'''
		
		#self.ev.modify_bg(gtk.STATE_NORMAL, color_palette.get_tooltip_color())
		
		self.ev.add(vbox)
		if show_date:
			if datetime.datetime.now().strftime("%a %d %b %Y") == date:
				self.label = gtk.Label(_("Today"))
			else:
				self.label = gtk.Label(date)
			vbox.pack_start(self.label, True, True, 5)
		self.pack_start(self.ev, False, False)
		
		self.view = DataIconView()
		if date.startswith("Sat") or date.startswith("Sun"):
			color = gtk.gdk.rgb_get_colormap().alloc_color('#FFF9D0')
			self.view.modify_base(gtk.STATE_NORMAL, color)
		
		self.scroll = gtk.ScrolledWindow()		
		self.scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
		self.scroll.add_with_viewport(self.view)
		self.pack_start(self.scroll)
		self.show_all()
		self.item_count = 0
	
	def refresh(self, date):
		self.date = date
		if datetime.datetime.now().strftime("%a %d %b %Y")  == date:
			self.label.set_label(_("Today"))
		else:
			self.label.set_label(date)
		if self.date.startswith("Sat") or self.date.startswith("Sun"):
			color = gtk.gdk.rgb_get_colormap().alloc_color('#FFF9D0')
			self.view.modify_base(gtk.STATE_NORMAL,color)
		else:
			color = gtk.gdk.rgb_get_colormap().alloc_color('#FFFFFF')
			self.view.modify_base(gtk.STATE_NORMAL,color)
	
	def format_color_string(self, color):
		""" Convert 48-bit gdk.Color to 24-bit "RRR GGG BBB" triple. """
		return (color.red, color.green,  color.blue)	
	
	def append_item(self, item, group=False):
		self.view.append_item(item, group)
		self.item_count += 1
	
	def clear(self):
		self.view.clear_store()
		self.item_count = 0
	
	def set_label(self, text):
		self.label.set_label(text)
	  
	def emit_focus(self):
		self.emit("set-focus-child", self)
			
class BookmarksBox(DayBox):
	def __init__(self, label = "Bookmark"):
		DayBox.__init__(self, _(label),False)
		self.set_border_width(5)
			
	def append_item(self, item):
		self.view.append_item(item, group = False)
		self.item_count += 1
		
class BookmarksView(gtk.ScrolledWindow):
	def __init__(self):
		gtk.ScrolledWindow.__init__(self)
		self.notebook = gtk.Notebook()
		self.notebook.set_property("tab-pos",gtk.POS_LEFT)
		self.add_with_viewport(self.notebook)		
		self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_NEVER)
		engine.connect("signal_updated", self.get_bookmarks)
		self.boxes = {}
		
		self.all_star = BookmarksBox()
		starred = "%s/bookmark-new.svg" % config.pkgdatadir
		box = self.create_tab_label(_("All favourites"),starred)
		self.notebook.append_page((self.all_star),box)
		self.notebook.set_tab_label_packing(self.all_star, True, True, gtk.PACK_START)
		
		self.get_bookmarks()
		
	def get_bookmarks(self, x=None , text=[]):
		self.all_star.clear()
		self.types = {}
		for box in self.boxes.values():
			box.clear()
		
		for item in bookmarker.get_items_uncached():
			if len(text) > 0:
				for tag in text:
					self.append_item(tag, item)
			else:
				self.append_item("", item)
				
		for key in self.boxes.keys():
			if not self.types.has_key(key):
				box = self.boxes[key]
				self.notebook.remove(box)
				del self.boxes[key]
		
	def append_item(self,tag,item):
		if item.has_search(tag):
			self.all_star.append_item(item)
			if self.types.has_key(item.type):
				self.types[item.type].append(item)
			else:
				self.types[item.type]=[item]
			
			if self.boxes.has_key(item.type):
				self.boxes[item.type].append_item(item)
				self.boxes[item.type].show_all()
			else:
				bookmarkbox = BookmarksBox(item.type)
				bookmarkbox.append_item(item)
				self.boxes[item.type] = bookmarkbox
				box = self.create_tab_label(item.type,item.icon)
				self.notebook.append_page((bookmarkbox),box)
				self.notebook.set_tab_label_packing(bookmarkbox, True, True, gtk.PACK_START)
		
	def clean_up_dayboxes(self,width):
		self.all_star.view.reload_name_cell_size(width)
		for box in self.boxes.values():
			box.view.reload_name_cell_size(width)
	
	def create_tab_label(self, title, stock):
			box = gtk.HBox()
			
			pixbuf = icon_factory.load_icon(stock, icon_size = 32 ,cache = False)
			icon = gtk.Image()
			icon.set_from_pixbuf(pixbuf)
			del pixbuf

			label = gtk.Label(title)
			
			box.pack_start(icon, False, False)
			box.pack_start(label, True, True)
			box.show_all()
			return box
	
class TagWindow(gtk.Window):
	def __init__(self):
		gtk.Window.__init__(self)	
		self.hide()
		pass
		
	def edit_tags(self,item):
		for tag in item.get_tags():
			pass

expanded_views = {}