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

from zeitgeist_gui.zeitgeist_util import launcher, icon_factory
from zeitgeist_shared.xdgdirs import xdg_directory
from zeitgeist_gui.zeitgeist_util import launcher, color_palette
from zeitgeist_gui.zeitgeist_engine_wrapper import engine
from zeitgeist_gui.zeitgeist_bookmarker import bookmarker
from zeitgeist_shared.zeitgeist_shared import *
from zeitgeist_shared.basics import BASEDIR


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
		
		TARGET_TYPE_TEXT = 80
		TARGET_TYPE_PIXMAP = 81

		self.fromImage = [ ( "text/plain", 0, TARGET_TYPE_TEXT ), ( "image/x-xpixmap", 0, TARGET_TYPE_PIXMAP ) ]

		
		self.active_image = gtk.gdk.pixbuf_new_from_file_at_size(
			"%s/data/bookmark-new.png" % BASEDIR, 24, 24) 
		
		self.inactive_image = icon_factory.greyscale(self.active_image)
		self.inactive_image = icon_factory.transparentize(self.inactive_image,50)

		#self.connect('window-state-event', self.window_state_event_cb)
		self.store = gtk.TreeStore(gtk.gdk.Pixbuf, str, str, gobject.TYPE_BOOLEAN, gobject.TYPE_PYOBJECT, str,  gtk.gdk.Pixbuf)
		
		self.set_tooltip_column(5)
		
		icon_cell = gtk.CellRendererPixbuf()
		icon_column = gtk.TreeViewColumn("",icon_cell,pixbuf=0)
		#icon_column.set_fixed_width(32)
		icon_column.set_expand(False)
		
		name_cell = gtk.CellRendererText()
		name_cell.set_property("wrap-mode", pango.WRAP_WORD_CHAR)
		name_cell.set_property("wrap-width", 125)
		name_column = gtk.TreeViewColumn(_("Name"), name_cell, markup=1)
		name_column.set_expand(True)
		self.name_cell = name_cell
		
		time_cell = gtk.CellRendererText()
		time_column = gtk.TreeViewColumn(_("Time"), time_cell, markup=2)
		#time_column.set_fixed_width(32)
		time_column.set_expand(False)
		
		bookmark_cell = CellRendererPixbuf()
		bookmark_cell.connect("toggled", self.toggle_bookmark, self.store )
		bookmark_column = gtk.TreeViewColumn("bookmark", bookmark_cell, pixbuf =6)
		bookmark_column.set_expand(False)
				
		self.append_column(icon_column)
		self.append_column(name_column)
		self.append_column(time_column)
		self.append_column(bookmark_column)
	 
		self.set_model(self.store)
		self.set_headers_visible(False)
			
		self.set_enable_tree_lines(True)
		self.set_expander_column(icon_column)
		
		self.connect("row-activated", self._open_item)
		self.connect("button-press-event", self._show_item_popup)
		self.connect("drag-data-get", self._item_drag_data_get)
		self.connect("drag_data_received", self.drag_data_received_data)
		self.connect("focus-out-event",self.unselect_all)
		
		self.set_double_buffered(True)
		#self.get_selection().set_mode(gtk.SELECTION_MULTIPLE)		
		
		self.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, [("text/uri-list", 0, 100)], gtk.gdk.ACTION_LINK | gtk.gdk.ACTION_COPY)
		self.enable_model_drag_dest(self.fromImage, gtk.gdk.ACTION_MOVE) 
		
		self.last_item=None
		self.last_iter = None
		self.day=None
		#engine.connect("signal_updated", lambda *args: self._do_refresh_rows())
		
		#self.store.set_sort_column_id(2, gtk.SORT_ASCENDING)
		self.types = {}
		self.days={}
		self.items_uris=[]
			
		
		
	def button_press_handler(self, treeview, event):
		if event.button == 3:
	      		# Figure out which item they right clicked on
			path = treeview.get_path_at_pos(int(event.x),int(event.y))
          		# Get the selection
           		selection = treeview.get_selection()
	
		    	# Get the selected path(s)
		    	rows = selection.get_rows()
			# If they didnt right click on a currently selected row, change the selection
			if path[0] not in rows[1]:
				selection.unselect_all()
				selection.select_path(path[0])
			
		     	return True
	
	def reload_name_cell_size(self,width):
		self.name_cell.set_property("wrap-width",width - 150)
		
	def append_item(self, item, group=True):
		self._set_item(item, group=group)
	
	def prepend_item(self, item,group=True):
		self._set_item(item, False, group=group)
		
	def remove_item(self,item):
		# Maybe filtering should be done on a UI level
		pass
	
	def clear_store(self):
		self.types.clear()
		self.days.clear()
		self.day=None
		self.items_uris=[]
		
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
		try:
			if ev.button == 3:
				item = self.get_selected_item()
				if item:
					menu = gtk.Menu()
					menu.attach_to_widget(view, None)
					item.populate_popup(menu)
					menu.popup(None, None, None, ev.button, ev.time)
					return True
		except Exception:
			pass
	
	def _item_drag_data_get(self, view, drag_context, selection_data, info, timestamp):
		# FIXME: Prefer ACTION_LINK if available
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
				
	def _set_item(self, item, append=True, group=False):
		
		bookmark = bookmarker.get_bookmark(item.uri)
		self.items_uris.append(item.uri)
			
		
		date = ""
		if not item.timestamp == -1.0:
			date = "<span size='small' color='darkgrey'>%s</span>" % item.get_time()
		
		name = "<span color='%s'>%s</span>" % \
			("black" if item.exists else "grey", item.get_name())
		
		icon = self.inactive_image
		if bookmark == True:
			icon = self.active_image
		
		
		if not self.types.has_key(item.type):
			if group:
				iter = self.store.append(None, [icon_factory.load_icon(item.icon, 24),
									item.type,
									date,
									bookmark,
									item,
									"Bookmarked "+item.type,
									None,
									])
			else:
				iter = None
			self.types[item.type] = iter
		
		self.last_iter = self.store.append(self.types[item.type], 
			[item.get_icon(24),
			name,
			date,
			bookmark,
			item,
			self.get_tooltip(item),
			icon,
			])
		
		self.collapse_all()
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
		self.set_current_folder(xdg_directory("", "~/"))
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
		string = item.get_name() +"\n"+"\n"+"Last Usage:			"+item.get_datestring() + " " + item.get_time()+"\n"+"\n"+"tags:				"+str(item.get_tags())+"\n"
		self.itemlabel.set_label(string)
		self.set_title("GNOME Zeitgeist -" + _("Files related to %s") % item.name)
		self.view.clear_store()
		uris = {}
		from zeitgeist_gui.zeitgeist_journal_widgets import timeline
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
	
	def __init__(self,date):
		
		gtk.VBox.__init__(self)
		self.date=date
		self.label=gtk.Label(date)
		vbox = gtk.VBox()
		
		self.ev = gtk.EventBox()
			
		'''
		FIXME: export the code somehwere else
		This makes the headers of the days fit the tooltip color
		'''
		
		#self.ev.modify_bg(gtk.STATE_NORMAL, color_palette.get_tooltip_color())
		
		self.ev.add(vbox)
		self.ev.set_border_width(1)
		vbox.pack_start(self.label,True,True,5)
		
		self.pack_start(self.ev,False,False)
		self.view = DataIconView()
		if date.startswith("Sat") or date.startswith("Sun"):
			color = gtk.gdk.rgb_get_colormap().alloc_color('#EEEEEE')
			self.view.modify_base(gtk.STATE_NORMAL,color)

		self.scroll = gtk.ScrolledWindow()		
		self.scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
		self.scroll.add_with_viewport(self.view)
		self.pack_start(self.scroll)
		self.show_all()
		self.item_count = 0
	
	def format_color_string(self, color):
		""" Convert 48-bit gdk.Color to 24-bit "RRR GGG BBB" triple. """
		return (color.red, color.green,  color.blue)	
	
	def append_item(self, item, group=False):
		self.view.append_item(item, group)
		self.item_count += 1
	
	def clear(self):
		self.view.clear_store()
		self.item_count = 0
	  
	def emit_focus(self):
		self.emit("set-focus-child", self)
			
class BookmarksBox(DayBox):
	def __init__(self):
		DayBox.__init__(self, _("Bookmark"))
		self.get_bookmarks()
		engine.connect("signal_updated", self.get_bookmarks)

	def get_bookmarks(self, x=None , text=""):
		self.view.clear_store()
		self.types = {}
		for item in bookmarker.get_items_uncached():
			if item.has_search(text):
				if self.types.has_key(item.type):
					self.types[item.type].append(item)
				else:
					self.types[item.type]=[item]
		
		items = self.types.items()
		items.sort()
		list =  [value for key, value in items]

		for type in list:
			for item in type:
				self.append_item(item)
				
	def append_item(self, item):
		self.view.append_item(item, group = True)
		self.item_count += 1
		
class BookmarksView(gtk.ScrolledWindow):
	def __init__(self):
		gtk.ScrolledWindow.__init__(self)
		self.bookmarks = BookmarksBox()
		self.add_with_viewport(self.bookmarks)		
		self.set_policy(gtk.POLICY_NEVER, gtk.POLICY_NEVER)


class TagWindow(gtk.Window):
	def __init__(self):
		gtk.Window.__init__(self)	
		self.hide()
		pass
		
	def edit_tags(self,item):
		for tag in item.get_tags():
			pass

		
		
		
			
