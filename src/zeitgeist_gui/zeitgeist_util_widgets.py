# -.- encoding: utf-8 -.-

import datetime
import gc
import os
import time
import sys
import gtk
import gobject
import pango
from gettext import ngettext, gettext as _ 

from zeitgeist_gui.zeitgeist_util import launcher
from zeitgeist_shared.xdgdirs import xdg_directory
from zeitgeist_gui.zeitgeist_util import launcher, color_palette
from zeitgeist_gui.zeitgeist_engine_wrapper import engine
from zeitgeist_gui.zeitgeist_bookmarker import bookmarker
from zeitgeist_shared.zeitgeist_shared import *


class ButtonCellRenderer(gtk.GenericCellRenderer):
	
	__gsignals__ = {
		'toggled': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE,
			(gobject.TYPE_STRING,))
	}
	
	def __init__(self):
		gtk.GenericCellRenderer.__init__(self)
		self.__gobject_init__()
		self.set_property('mode', gtk.CELL_RENDERER_MODE_ACTIVATABLE)

		self.xpad = 1; self.ypad = 0
		self.xalign = 0.5; self.yalign = 0.5
		self.active_area = None
		self.toggled = False
		self.pango_l  = None
		self.text = ""
		self.active_bookmark = icon_factory.load_icon(gtk.STOCK_ABOUT, 24)
		
		self.inactive_bookmark = icon_factory.greyscale(icon_factory.load_icon(gtk.STOCK_ABOUT, 24))

	def do_set_property(self, pspec, value):
		print "set prop ", pspec.name
		setattr(self, pspec.name, value)
	
	def do_get_property(self, pspec):
		print "get prop ", pspec.name
		return getattr(self, pspec.name)
	
	def on_render(self, window, widget, background_area, cell_area, expose_area, flags):
	
		pix_rect = gtk.gdk.Rectangle()
		pix_rect.x, pix_rect.y, pix_rect.width, pix_rect.height = \
		self.on_get_size(widget, cell_area)
		
		pix_rect.x += cell_area.x
		pix_rect.y += cell_area.y
		pix_rect.width -= 2 * self.get_property("xpad")
		pix_rect.height -= 2 * self.get_property("ypad")
		
		draw_rect = cell_area.intersect(pix_rect)
		draw_rect = expose_area.intersect(draw_rect)

		if self.toggled:
			window.draw_pixbuf(widget.style.black_gc, self.active_bookmark, \
				draw_rect.x-pix_rect.x, draw_rect.y-pix_rect.y, draw_rect.x, \
				draw_rect.y+2, draw_rect.width, draw_rect.height, \
				gtk.gdk.RGB_DITHER_NONE, 0, 0)
		else:
			window.draw_pixbuf(widget.style.black_gc, self.inactive_bookmark, \
				draw_rect.x-pix_rect.x, draw_rect.y-pix_rect.y, draw_rect.x, \
				draw_rect.y+2, draw_rect.width, draw_rect.height, \
				gtk.gdk.RGB_DITHER_NONE, 0, 0)
	
	def on_get_size(self, widget, cell_area):
		if cell_area:
			calc_width = cell_area.width - 2 * self.pad
			calc_height = cell_area.height - 2 * self.ypad
			if calc_width < calc_height:
				calc_height = calc_width
			else:
				calc_width = calc_height
			x_offset = int(self.xalign * (cell_area.width - calc_width))
			x_offset = max(x_offset, 0)
			y_offset = int(self.yalign * (cell_area.height - calc_height))
			y_offset = max(y_offset, 0)
		else:
			x_offset = 0
			y_offset = 0
			calc_width = 20
			calc_height = 16
		return x_offset, y_offset, calc_width, calc_height

	def on_activate(self, event, widget, path, background_area, cell_area, flags):
		self.sig_deac = widget.connect('button-release-event', self.on_deactivate, cell_area, path)
		self.active_area = cell_area
		self.toggled = not self.toggled

	def on_deactivate(self, w, e, cell_area, path):
		w.disconnect(self.sig_deac)
		if (cell_area.x <= int(e.x) <= cell_area.x + cell_area.width) and (cell_area.y <= int(e.y) <= cell_area.y + cell_area.height):
			self.emit('toggled', path)
		self.active_area = None
		self.on_render(w.get_bin_window(), w, None, cell_area, None, 0)


class DataIconView(gtk.TreeView):
	'''
	Icon view which displays Datas in the style of the Nautilus horizontal mode,
	where icons are right aligned and each column is of a uniform width.  Also
	handles opening an item and displaying the item context menu.
	'''
	
	def __init__(self,parentdays=False):
		gtk.TreeView.__init__(self)
		self.set_size_request(250,-1)
		self.parentdays = parentdays
		
		TARGET_TYPE_TEXT = 80
		TARGET_TYPE_PIXMAP = 81

		self.fromImage = [ ( "text/plain", 0, TARGET_TYPE_TEXT ), ( "image/x-xpixmap", 0, TARGET_TYPE_PIXMAP ) ]

		#self.connect('window-state-event', self.window_state_event_cb)
		self.store = gtk.TreeStore(gtk.gdk.Pixbuf, str, str, gobject.TYPE_BOOLEAN, gobject.TYPE_PYOBJECT, str)
		
		self.set_tooltip_column(5)
		
		icon_cell = gtk.CellRendererPixbuf()
		icon_column = gtk.TreeViewColumn("",icon_cell,pixbuf=0)
		#icon_column.set_fixed_width(32)
		icon_column.set_expand(False)
		
		name_cell = gtk.CellRendererText()
		name_cell.set_property("wrap-mode", pango.WRAP_WORD_CHAR)
		name_cell.set_property("wrap-width", 125)
		name_column = gtk.TreeViewColumn("Name", name_cell, markup=1)
		name_column.set_expand(True)
		self.name_cell = name_cell
		
		time_cell = gtk.CellRendererText()
		time_column = gtk.TreeViewColumn("Time", time_cell, markup=2)
		#time_column.set_fixed_width(32)
		time_column.set_expand(False)
		
		bookmark_cell = gtk.CellRendererToggle()
		bookmark_cell.set_property("activatable", True)
		bookmark_cell.connect("toggled", self.toggle_bookmark, self.store )
		bookmark_column = gtk.TreeViewColumn("bookmark",bookmark_cell)
		bookmark_column.add_attribute( bookmark_cell, "active", 3)
		bookmark_column.set_fixed_width(128)
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
		
		self.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, [("text/uri-list", 0, 100)], gtk.gdk.ACTION_LINK | gtk.gdk.ACTION_COPY)
		self.enable_model_drag_dest(self.fromImage, gtk.gdk.ACTION_MOVE) 
		
		self.last_item=None
		self.last_iter = None
		self.day=None
		engine.connect("signal_updated", lambda *args: self._do_refresh_rows())
		
		#self.store.set_sort_column_id(2, gtk.SORT_ASCENDING)
		self.types = {}
		self.days={}
		self.items_uris=[]
		
		self.reload_name_cell_size(250)
		
	def reload_name_cell_size(self,width):
		if width < 300:
			width = 250
			wrap = 125
		else:
			wrap = width - 50
			
		self.name_cell.set_property("wrap-width",wrap)
		self.set_size_request(width,-1)
		
	def append_item(self, item, group=True):
		# Add an item to the end of the store
		self._set_item(item, group=group)
		#self.set_model(self.store)
	
	def prepend_item(self, item,group=True):
		# Add an item to the end of the store
		self._set_item(item, False,group=group)
		#self.set_model(self.store)
		
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
		item.add_bookmark()
	
	def _do_refresh_rows(self):
		
		iter = self.store.get_iter_root()
		if iter:
			item = self.store.get_value(iter, 4)
			try:
				self.store.set(iter,3,bookmarker.get_bookmark(item.uri))
			except Exception:
				pass
			while True:
				iter = self.store.iter_next(iter)
				if iter:
					item = self.store.get_value(iter, 4)
					try:
						self.store.set(iter,3,bookmarker.get_bookmark(item.uri))
					except Exception:
						pass
				else:
					break
				
						
	def _set_item(self, item, append=True, group=True):
		
		bookmark = bookmarker.get_bookmark(item.uri)
		
		self.items_uris.append(item.uri)
		
		if not item.timestamp == -1.0:
			# TODO: item.get_time() should give 24-hour time
			date="<span size='small' color='grey'>%s</span>" % item.get_time()
		else:
			date=""
		
		tooltip = self.get_tooltip(item)
		
		if item.exists:
			name = "<span color='black'>%s</span>" % item.get_name()
		else:
			name = "<span color='grey'>%s</span>" % item.get_name()
		
		self.last_iter = self.store.append(None, [item.get_icon(24),
					name,
					date,
					bookmark,
					item,
					tooltip])
		
		self.collapse_all()
		self.last_item = item
	
	def get_tooltip(self,item):
		tooltip = item.uri + "\n\n" + item.comment
		if not len(item.tags) == 0:
			tooltip = tooltip +"\n\n" +  "Tagged with:\n"+item.tags
		if not item.exists:	
			tooltip = "The file has been removed from\n"+tooltip
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
		self.label = gtk.Label("Related files")
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
		self.set_title("GNOME Zeitgeist - Files related to "+item.name)
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
	
	def append_item(self, item, group=True):
		self.view.append_item(item, group)
		self.item_count += 1
	
	def clear(self):
		self.view.clear_store()
		self.item_count = 0
	  
	def emit_focus(self):
			self.emit("set-focus-child", self)
			
class BookmarksBox(DayBox):
	def __init__(self):
		DayBox.__init__(self,"Bookmark")
		self.get_bookmarks()
		engine.connect("signal_updated", self.get_bookmarks)

	def get_bookmarks(self, x=None):
		self.view.clear_store()
		for item in bookmarker.get_items_uncached():
			self.view.append_item(item, group=False)
		
class BookmarksView(gtk.ScrolledWindow):
	def __init__(self):
		gtk.ScrolledWindow.__init__(self)
		self.bookmarks = BookmarksBox()
		self.add_with_viewport(self.bookmarks)		
		self.set_policy(gtk.POLICY_NEVER, gtk.POLICY_NEVER)
		
