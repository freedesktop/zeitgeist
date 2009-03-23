import datetime
import gc
import os
import time
import sys
import gtk
import gobject
import pango
from gettext import ngettext, gettext as _
 
from zeitgeist_engine.zeitgeist_datasink import datasink
from zeitgeist_engine.zeitgeist_util import launcher

class TimelineWidget(gtk.ScrolledWindow,gobject.GObject):
	__gsignals__ = {
		"reload" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())
		}

	

	def __init__(self):
		# Initialize superclass
		gtk.ScrolledWindow.__init__(self)
		
		gobject.GObject.__init__(self)
		# Add children widgets
		self.view = DataIconView(True)
		self.dayboxes=gtk.HBox(False,True)
		self.days={}
				
		# Set up default properties
		self.set_border_width(5)
		self.set_size_request(400, 300)
		self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_NEVER)
		self.add_with_viewport(self.dayboxes)
		
		# This contains the range of dates which we've currently loaded into the GUI
		self.begin = None
		self.end = None
		
		# The current tags that we're using to filter displayed results
		self.tags = ''
		
		# Connect to the calendar's (displayed in the sidebar) signals
		calendar.connect("month-changed", self.load_month)
		calendar.connect("day-selected", self.jump_to_day)
		calendar.connect("day-selected-double-click", self.jump_to_day,True)
		
		# Connect to the datasink's signals
		datasink.connect("reload", self.load_month_proxy)
		self.offset=0
		# Load the GUI
		self.load_month()
	
	def apply_search(self, tags, search = True):
		'''
		Adds all items which match tags to the gui.
		'''
		
		self.tags = tags
		items=[]
		if not tags == "":
			if tags.find(",,")>-1:
				tags = self.tags.strip().replace(",,", ",")
			if tags.startswith(","):
				tags.replace(",","",1)
			while tags.find("  ") > -1:
				tags = tags.replace("  "," ")
			tagsplit = tags.strip().split(",")
		else:
			tagsplit = []
				
		ftagsplit=[]
		for tag in tagsplit:
			if not tag=="":
				ftagsplit.append(tag)
		tagsplit = ftagsplit
		
		self.days.clear()
		for day in self.dayboxes:
			self.dayboxes.remove(day)
			day.view.clear_store()
		
		day = None
		for item in self.items:
			if len(tagsplit) >0:
				for tag in tagsplit:
						if search:
							if item.uri.lower().find(tag.lower())>-1:
								
								try:
									if items.index(item)>-1:
										pass
								except:
									items.append(item)
									if day == item.datestring:
										daybox.view.append_item(item)
									else:
										day=item.datestring
										daybox = DayBox(item.datestring)
										daybox.view.append_item(item)
										adj = self.get_hadjustment()
										daybox.connect('set-focus-child', self.focus_in, adj) 
										self.dayboxes.pack_start(daybox)
										self.days[day]=daybox
									
						if item.tags.lower().find(","+tag.lower()+",")> -1 or item.tags.lower().find(","+tag.lower())> -1 or item.tags.lower().find(tag.lower()+",")> -1 or item.tags.lower() == tag.lower()> -1:

							try:
								if items.index(item)>-1:
									pass
							except:
								items.append(item)
								if day == item.datestring:
									daybox.view.append_item(item)
								else:
									day=item.datestring
									daybox = DayBox(item.datestring)
									daybox.view.append_item(item)
									adj = self.get_hadjustment()
									daybox.connect('set-focus-child', self.focus_in, adj) 
									self.dayboxes.pack_start(daybox)
									self.days[day]=daybox		
							 
			else:
				try:
					if items.index(item)>-1:
						pass
				except:
					items.append(item)
					if day == item.datestring:
						daybox.view.append_item(item)
					else:
						day=item.datestring
						daybox = DayBox(item.datestring)
						daybox.view.append_item(item)
						adj = self.get_hadjustment()
						daybox.connect('set-focus-child', self.focus_in, adj) 
						self.dayboxes.pack_start(daybox)
						self.days[day]=daybox
					
	def load_month_proxy(self,widget=None,month=False,force=False):
        	
        	today = time.time()
        	if today  >= self.begin and today<=self.end+86400 :
        	    self.load_month(month=month,force=force)
                    
	def load_month(self, widget=None,month=False,force=False):
		'''
		Loads the current month selected on the calendar into the GUI.
		
		This is called when a new date is selected on the calendar
		or when the user types into the search bar. In the second case,
		we need to reload the GUI and only show items that match the tags
		parameter.
		'''
		
		# Get date range
		# Format is (year, month-1, day)
		date = calendar.get_date()
		
		
		# Get the begin and end of this month
		# each tuple is of format (year, month, day, hours, minutes,
		# seconds, weekday, day_of_year, daylight savings) 
		
		day = date[2]
		if not month:
			begin = (date[0], date[1]+1, day-1+self.offset, 0,0,0,0,0,0)
			end = (date[0], date[1]+1, day+2+self.offset, 0,0,0,0,0,0)
		else:
			begin = (date[0], date[1]+1, 1, 0,0,0,0,0,0)
			end = (date[0], date[1]+2, 1, 0,0,0,0,0,0)
		
                    
		# Note: To get the begin and end of a single day we would use the following
		#begin = (date[0], date[1]+1, date[2], 0,0,0,0,0,0)
		#end = (date[0], date[1]+1, date[2]+1, 0,0,0,0,0,0)
		
		# Get date as unix timestamp
		self.begin = time.mktime(begin)
		self.end = time.mktime(end)
		
		calendar.clear_marks()
		
		
		# Begin benchmarking
		time1 = time.time()
		# Get all items in the date range and add them to self.items
		self.items = []
		for i in datasink.get_items_by_time(self.begin, self.end, '', True):
			self.items.append(i)
			i.connect("relate",self.set_relation)
			i.connect("reload",self.load_month)
			 
		
		# Update the GUI with the items that match the current search terms/tags
		self.apply_search(self.tags)
		
		time2 = time.time()
		# Benchmarking
		print "Time to retrive %s items from database: %s" % (len(self.items), str(time2 -time1))
		
		# Manually force garbage collection
		gc.collect()
		self.emit("reload")
		
	def jump_to_day(self, widget,focus=False):
		'''
		Jump to the currently selected day in the calendar.
		'''
		
		self.offset = 0
		self.load_month()
		date = calendar.get_date()
		ctimestamp = time.mktime([date[0],date[1]+1,date[2],0,0,0,0,0,0])
		datestring = datetime.datetime.fromtimestamp(ctimestamp).strftime(_("%d %b %Y"))
		if focus==False:
			for w in self.dayboxes:
				w.show_all()
				if w.date == datestring:
					w.emit("set-focus-child",w)
		else:
			for w in self.dayboxes:
				w.hide_all()
				if w.date == datestring:
					w.show_all()
		
	
	def set_relation(self,item):
		related = RelatedWindow()
		related.set_relation(item)

	def focus_in(self,widget, event, adj):
		alloc = widget.get_allocation() 
            	if alloc.x < adj.value or alloc.x > adj.value + adj.page_size:
	        	adj.set_value(min(alloc.x, adj.upper-adj.page_size))
        	del widget 

class DayBox(gtk.VBox):
	def __init__(self,date):
		gtk.VBox.__init__(self)
		self.date=date
		self.label=gtk.Label(date)
		self.pack_start(self.label,False,False,5)
		self.view=DataIconView(True)
		self.scroll = gtk.ScrolledWindow()		
		self.scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
		self.scroll.add_with_viewport(self.view)
		self.pack_start(self.scroll)
		self.show_all()
				      
	def emit_focus(self):
	        self.emit("set-focus-child",self) 
		  	  
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
	
	def set_relation(self,item):
		'''
		Find the items that share same tags with the current item
		Later to be done by monitoring the active files
		'''
		self.img.set_from_pixbuf(item.get_icon(64))
		string = item.get_name() +"\n"+"\n"+"Last Usage:			"+item.datestring + " " + item.time +"\n"+"\n"+"tags:				"+str(item.get_tags())+"\n"
		self.itemlabel.set_label(string)
		self.set_title("Gnome Zeitgeist - Files related to "+item.name)
		self.view.clear_store()
		uris = {}
		if not item.tags == "":
			for i in timeline.items:
				for tag in item.get_tags():
					try:
						if i.tags.index(tag) >= 0:
							#print tag
							i.timestamp=-1.0
							uris[i.uri]=i
						else:
							pass
					except:
						pass
		items = []
		for uri in uris.keys():
			if items.count(uri) == 0:
				items.append(uri)
				self.view.append_item(uris[uri])
				
		for i in datasink.get_related_items(item):
			if items.count(i.uri) == 0:
				items.append(i.uri)
				self.view.append_item(i)
		
		items=[]
		uris.clear()
		
class TagBrowser(gtk.HBox):
    def __init__(self):
        # Initialize superclass
        gtk.HBox.__init__(self)
        self.set_size_request(-1,32)
        self.combobox = gtk.combo_box_new_text()
        
        self.combobox = gtk.combo_box_new_text()
        self.combobox.append_text('Recently used tags')
        self.combobox.append_text('Most used tags')
        
        self.pack_start(self.combobox, False, False)
        
        
        
        self.scroll = gtk.ScrolledWindow()
        self.ev = gtk.EventBox()
        self.ev.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))

        self.view = gtk.HBox()
        self.ev.add(self.view)
        self.scroll.add_with_viewport(self.ev)
        self.scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_NEVER)
        self.pack_start(self.scroll,True,True)
        self.show_all()
        self.items = []
        
        self.func = self.get_recent_tags
        
        self.func()
        
        #timeline.connect("reload", self.reload_tags)
    
        self.combobox.connect('changed', self.changed_cb)
        self.combobox.set_active(0)
        
        datasink.connect("reload", lambda x: self.func)
        return

    def reload_tags(self,x=None):
    	model = self.combobox.get_model()
        index = self.combobox.get_active()
        if index == 0:
        	self.func = self.get_recent_tags()
        else:
        	self.func = self.get_most_tags()

    def changed_cb(self, combobox=None):
        model = self.combobox.get_model()
        index = self.combobox.get_active()
        if index == 0:
        	self.func = self.get_recent_tags()
        else:
        	self.func = self.get_most_tags()

    
    
    def get_recent_tags(self,x=None):
        
        date = calendar.get_date()
        
        begin = time.mktime((date[0], date[1]+1, 1, 0,0,0,0,0,0))
        end = time.mktime((date[0], date[1]+2, 0, 0,0,0,0,0,0))
		
        for w in self.view:
            self.view.remove(w)
        
        for tag in datasink.get_recent_used_tags(10,begin,end):
            btn = gtk.ToggleButton(str(tag))
            btn.set_relief(gtk.RELIEF_NONE)
            btn.set_focus_on_click(False)
            #label.set_use_underline(True)
            self.view.pack_start(btn,True,True)
            #btn.set_size_request(-1,-1)
            btn.connect("toggled",self.toggle)
            
        self.show_all()
        
    def get_most_tags(self,x=None):
		
		begin = timeline.begin
		end = timeline.end
        
		for w in self.view:
			self.view.remove(w)
		
		for tag in datasink.get_most_used_tags(10,begin,end):
			btn = gtk.ToggleButton(str(tag))
			btn.set_relief(gtk.RELIEF_NONE)
			btn.set_focus_on_click(False)
			#label.set_use_underline(True)
			self.view.pack_start(btn,True,True)
			#btn.set_size_request(-1,-1)
			btn.connect("toggled",self.toggle)
			
		self.show_all()
        
    def toggle(self,x=None):
        tags = timeline.tags
        if x.get_active():
            if tags.find(x.get_label()) == -1:
                 tags = tags+","+x.get_label()
                 timeline.load_month(month=True)
        else:
            if tags.find(x.get_label()) > -1:
                 tags = tags.replace(","+x.get_label(), ",")
                 tags = tags.replace(x.get_label()+"," ,",")
                 timeline.load_month(month=False)
        
        timeline.apply_search(tags,False)
                       
class FilterAndOptionBox(gtk.VBox):
	def __init__(self):
		gtk.VBox.__init__(self)
		self.option_box = gtk.VBox(False)
		self.create_doc_btn = gtk.Button("Create New Document")
		self.create_doc_btn.connect("clicked",self._show_new_from_template_dialog)
		self.create_note_btn = gtk.Button("Create New Note")
		self.create_note_btn.connect("clicked",self._make_new_note)
		self.option_box.pack_end(self.create_doc_btn,False,False)
		self.option_box.pack_end(self.create_note_btn,False,False)
		self.timefilter_active=False
		self.filters=[]
		'''
		Filter Box
		'''
		
		#self.search = SearchToolItem()
		#self.pack_start( self.search ,False,False,0)
		self.pack_start( calendar ,False,False,0)
		
		self.pack_start(self.option_box)
		
		self.frame2 = gtk.Frame()
		#self.alignment2 = gtk.Alignment(0.5,0.5,1.0,1.0)
		self.label2 = gtk.Label("Filter")
		self.frame2.set_label_align(0.5, 0.5)
		#self.frame2.add(self.alignment2)
		self.frame2.set_label_widget(self.label2)
		
		
		#self.timefilter = gtk.CheckButton()
		#self.timefilter.set_label("Filter over current period")
		#self.timefilter.connect("toggled",self.set_timelinefilter)
		#self.option_box.pack_start(self.timefilter,False,False,5)
		self.option_box.pack_start(self.frame2,False, False)
		
		
		self.voptionbox = gtk.VBox(False)
		
		self.timelinefilter = gtk.CheckButton()
		for source in datasink.sources:
			filter = CheckBox(source)
			filter.set_active(True)
			self.voptionbox.pack_start( filter,False,False,0)
			self.filters.append(filter)
			filter.connect("toggled",self.filter_out)
			
		self.frame2.add(self.voptionbox)
		self.date_dict = None
		
	def set_timelinefilter(self,w=None):
		if self.timefilter.get_active():
			self.timefilter_active=True
			print "timefilter active"
		else:
			self.timefilter_active=False
			print "timefilter inactive"
			
	def _make_new_note(self,x):
		launcher.launch_command("tomboy --new-note")
  
	def _show_new_from_template_dialog(self, x):		
		dlg = NewFromTemplateDialog(".","")
		dlg.show()
		
	def filter_out(self, widget):
		datasink.emit("reload")
		gc.collect()

class CalendarWidget(gtk.Calendar):
	def __init__(self):
		gtk.Calendar.__init__(self)

class CheckBox(gtk.CheckButton):
	
	def __init__(self,source):
		gtk.CheckButton.__init__(self)
		self.set_label(source.name)
		self.set_border_width(5)
		self.img = gtk.Image()
		
		self.source = source
		
		#icon = source.icon
		#self.img.set_from_pixbuf(icon)
		
		self.img.set_from_pixbuf(source.get_icon_static_done(16))
		
		self.set_image(self.img)
		
		self.set_focus_on_click(False)
		self.connect("toggled", self.toggle_source)
		self.show_all()

	def toggle_source(self,widget):
		if self.get_active():
			self.source.set_active(True)
			# FIXME
			#search.emit("clear")
		else:
			self.source.set_active(False)
		
		timeline.load_month()
	
	  
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
		self.set_current_folder(os.path.expanduser("~/Desktop"))
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

class SearchToolItem(gtk.ToolItem):
	__gsignals__ = {
		"clear" : (gobject.SIGNAL_RUN_FIRST,
				   gobject.TYPE_NONE,
				   ()),
		"search" : (gobject.SIGNAL_RUN_FIRST,
					gobject.TYPE_NONE,
					(gobject.TYPE_STRING,))
		}

	def __init__(self, accel_group = None):
		gtk.ToolItem.__init__(self)
		self.search_timeout = None
		self.default_search_text = _("Search")
		box = gtk.HBox(False, 5)
		box.show()

		self.clearbtn = None
		self.iconentry = None
		self.entry = gtk.Entry()
		box.pack_start(self.entry, True, True, 5)

		self.entry.set_width_chars(14)
		self.entry.set_text(self.default_search_text)
		self.entry.show()
		
		# Needs cleanup
		calendar.connect("month-changed", lambda w: self.emit("clear"))
		self.entry.connect("activate", lambda w: self._typing_timeout())
		self.entry.connect("focus-in-event", lambda w, x: self._entry_focus_in())
		self.entry.connect("key-press-event", self._entry_key_press)
		
		# Hold on to this id so we can block emission when initially clearing text
		self.change_handler_id = self.entry.connect("changed", lambda w: self._queue_search())
		
		if accel_group:
			# Focus on Ctrl-L
			self.entry.add_accelerator("grab-focus",
									   accel_group,
									   ord('l'),
									   gtk.gdk.CONTROL_MASK,
									   0)

		self.add(box)
		self.show_all()

	def do_clear(self):
		if self.clearbtn and self.clearbtn.child:
			self.clearbtn.remove(self.clearbtn.child)
		self._entry_clear_no_change_handler()
		self.do_search("")
		timeline.load_month(month=False)
		
	def do_search(self, text):
		timeline.load_month(month=True)
		if self.clearbtn and not self.clearbtn.child:
			img = icon_factory.load_image(gtk.STOCK_CLOSE, 16)
			img.show()
			self.clearbtn.add(img)
		timeline.apply_search(tags=text.lower())

	def _entry_clear_no_change_handler(self):
		'''Avoids sending \'changed\' signal when clearing text.'''
		self.entry.handler_block(self.change_handler_id)
		self.entry.set_text("")
		self.entry.handler_unblock(self.change_handler_id)

	def _entry_focus_in(self):
		'''Clear default search text'''
		if self.entry.get_text() == self.default_search_text:
			self._entry_clear_no_change_handler()

	def _typing_timeout(self):
		if len(self.entry.get_text()) > 0:
			self.emit("search", self.entry.get_text())
		self.search_timeout = None
		return False

	def _queue_search(self):
		if self.search_timeout is not None:
			gobject.source_remove(self.search_timeout)
			self.search_timeout = None

		if len(self.entry.get_text()) == 0:
			self.emit("clear")
		else:
			self.search_timeout = gobject.timeout_add(100, self._typing_timeout)

	def _entry_key_press(self, w, ev):
		if ev.keyval == gtk.gdk.keyval_from_name("Escape") \
			   and len(self.entry.get_text()) > 0:
			self.emit("clear")
			return True

	def get_search_text(self):
		return self.entry.get_text()

	def cancel(self):
		'''Cancel a pending/active search without sending the \'clear\' signal.'''
		if self.entry.get_text() != self.default_search_text:
			self.do_clear()
		
class DataIconView(gtk.TreeView):
	'''
	Icon view which displays Datas in the style of the Nautilus horizontal mode,
	where icons are right aligned and each column is of a uniform width.  Also
	handles opening an item and displaying the item context menu.
	'''
	
	def __init__(self,parentdays=False):
		gtk.TreeView.__init__(self)
		self.parentdays = parentdays
		#self.set_selection_mode(gtk.SELECTION_MULTIPLE)
		self.store = gtk.TreeStore(gtk.gdk.Pixbuf, str, str,gtk.gdk.Pixbuf, gobject.TYPE_PYOBJECT)
		#self.use_cells = isinstance(self, gtk.CellLayout)
		
		icon_cell = gtk.CellRendererPixbuf()
		icon_column = gtk.TreeViewColumn("Icon",icon_cell,pixbuf=0)
		
		name_cell = gtk.CellRendererText()
		name_cell.set_property("wrap-mode", pango.WRAP_WORD_CHAR)
		name_cell.set_property("yalign", 0.0)
		name_cell.set_property("xalign", 0.0)
		name_cell.set_property("wrap-width", 150)
		name_column = gtk.TreeViewColumn("Name", name_cell, markup=1)
		
		time_cell = gtk.CellRendererText()
		time_column = gtk.TreeViewColumn("Time",time_cell,markup=2)
		
		bookmark_cell = gtk.CellRendererPixbuf()
		bookmark_column = gtk.TreeViewColumn("bookmark",bookmark_cell,pixbuf=3,expand=False)
		
		self.append_column(icon_column)
		self.append_column(name_column)
		self.append_column(time_column)
		self.append_column(bookmark_column)
		#self.append_column(count_column)
	 
		self.set_model(self.store)
		self.set_headers_visible(False)
		self.set_enable_tree_lines(True)
		self.set_rubber_banding(True)
		self.set_expander_column(icon_column)
		
		self.connect("row-activated", self._open_item)
		self.connect("button-press-event", self._show_item_popup)
		self.connect("drag-data-get", self._item_drag_data_get)
		self.connect("focus-out-event",self.unselect_all)
		
		self.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, [("text/uri-list", 0, 100)], gtk.gdk.ACTION_LINK | gtk.gdk.ACTION_COPY)
		self.last_item=None
		self.day=None
		
		#self.store.set_sort_column_id(2, gtk.SORT_ASCENDING)
		self.types = {}
		self.days={}
		self.last_item = ""
		self.iter = None
	
	def append_item(self, item,group=True):
		# Add an item to the end of the store
		self._set_item(item,group=group)
		self.set_model(self.store)
	
	def prepend_item(self, item,group=True):
		# Add an item to the end of the store
		self._set_item(item, False,group=group)
		self.set_model(self.store)
		
	def remove_item(self,item):
		#Maybe filtering should be done on a  UI level
		pass
	
	def clear_store(self):
		self.types.clear()
		self.days.clear()
		self.store.clear()
		self.day=None
		gc.collect()
		
	def unselect_all(self,x=None,y=None):
		try:
			treeselection = self.get_selection()
			model, iter = treeselection.get_selected()
			self.last_item = model.get_value(iter, 4)
			treeselection.unselect_all()
		except:
			pass
			
	def _open_item(self, view, path, x=None):		 
		treeselection = self.get_selection()
		model, iter = treeselection.get_selected()
		item = model.get_value(iter, 4)
		item.open()
		del item
		del iter
		del model
		gc.collect()

	def _show_item_popup(self, view, ev):
		if ev.button == 3:
			   treeselection = self.get_selection()
			   model, iter = treeselection.get_selected()
			   if iter:
				   item = model.get_value(iter, 4)
				   if item:
						menu = gtk.Menu()
						menu.attach_to_widget(view, None)
						item.populate_popup(menu)
						menu.popup(None, None, None, ev.button, ev.time)
						return True

	def _item_drag_data_get(self, view, drag_context, selection_data, info, timestamp):
		# FIXME: Prefer ACTION_LINK if available
		if info == 100: # text/uri-list
			
			if self.last_item:
				uris = []
				uris.append(self.last_item.get_uri())
				selection_data.set_uris(uris)
	
	def _set_item(self, item, append=True, group=True):
		
		func = self.store.append
	        
		if not item.timestamp == -1.0:
			date="<span size='small' color='blue'>%s</span>" % item.get_time()
		else:
			date=""
			
	        if self.last_item!=item.type or group==False:
        		self.last_item = item.type
        		self.iter=func(None,[item.get_icon(24),
							"<span color='black'>%s</span>" % item.get_name(),
		        			date,
							item.get_bookmark_icon(),
							item])
        	else:
	        	func(None,[item.get_icon(24),
	        	#func(self.iter,[item.get_icon(24),
							"<span color='black'>%s</span>" % item.get_name(),
		        			date,
							item.get_bookmark_icon(),
							item])
	        	
	def get_icon_pixbuf(self, stock):
		return self.render_icon(stock, size=gtk.ICON_SIZE_MENU,detail=None)

        	
class BrowserBar (gtk.Toolbar):
	def __init__(self):
		gtk.Toolbar.__init__(self)   
		self.tooltips = gtk.Tooltips()

		self.home = gtk.ToolButton("gtk-home")
		self.home.set_label("Recent")
		self.home.connect("clicked",self.focus_today)
		self.tooltips.set_tip(self.home , "Show recent activities")

		self.back = gtk.ToolButton("gtk-go-back")
		self.back.set_label("Older")
		self.back.connect("clicked",self.add_day)
		self.tooltips.set_tip(self.back , "Go back in time")
		
		self.forward = gtk.ToolButton("gtk-go-forward")
		self.forward.set_label("Newer")
		self.forward.connect("clicked",self.remove_day)
		self.tooltips.set_tip(self.forward , "Go to the future")
		
		
		self.options = gtk.ToggleToolButton("gtk-select-color")
		self.tooltips.set_tip(self.options , "Filter your current view")
		self.options.set_label("Filters")
		
		self.star = gtk.ToggleToolButton("gtk-about")
		self.star.set_label("Bookmarks")
		self.tooltips.set_tip(self.star , "View bookmarked activities")
		self.star.connect("toggled",self.toggle_bookmarks)
		
		
		self.tags = gtk.ToggleToolButton("gtk-dialog-warning")
		self.tags.set_label("Tags")
		self.tooltips.set_tip(self.tags , "View tagged activities")
		self.tags.connect("toggled",self.toggle_tags)
		
		self.add(self.back)
		self.add(self.forward)
		self.add(self.home)
		self.add(self.star)
		self.add(self.tags)
		self.add(self.options)
		
		
		self.search = SearchToolItem()
		self.add(self.search)
		
	def remove_day(self, x=None):
		print timeline.offset
		timeline.offset +=  1
		timeline.load_month()
		
	def toggle_bookmarks(self, x=None):
		if self.star.get_active():
			bookmarks.show_all()
		else:
			bookmarks.hide_all()
			
	
	def toggle_tags(self, x=None):
		if self.tags.get_active():
			tb.show_all()
		else:
			tb.hide_all()
		
	def add_day(self, x=None):
		print timeline.offset
		timeline.offset -= 1
		timeline.load_month()

	def focus_today(self, x = None):
		timeline.offset = 0
		today = time.time()
		month =  int(datetime.datetime.fromtimestamp(today).strftime(_("%m")))-1
		year =  int(datetime.datetime.fromtimestamp(today).strftime(_("%Y")))
		day =  int(datetime.datetime.fromtimestamp(today).strftime(_("%d")))
		calendar.select_month(month,year)
		calendar.select_day(day)
		#calendar.do_day_selected_double_click()
		
class BookmarksView(gtk.VBox):
	def __init__(self):
		gtk.VBox.__init__(self)

		vbox=gtk.VBox()
		
		self.label = gtk.Label("Bookmarks")
		self.label.set_padding(5,5)
		vbox.pack_start(self.label,False,True)
		self.view = DataIconView()

		evbox = gtk.EventBox()
		evbox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("darkgrey"))
		evbox1 = gtk.EventBox()
		evbox1.set_border_width(1)
		evbox1.add(vbox)
		evbox.add(evbox1)
		
		
		
        	evbox2 = gtk.EventBox()
		evbox2.set_border_width(5)
		evbox2.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("darkgrey"))
        	evbox3 = gtk.EventBox()
        	evbox3.set_border_width(1)
        	evbox3.add(self.view)
        	evbox2.add(evbox3)
            
		
		
		vbox.pack_start(evbox2,True,True)
		self.pack_start(evbox,True,True)
		self.get_bookmarks()
		datasink.connect("reload",self.get_bookmarks)
		
	def get_bookmarks(self,x=None):
		self.view.clear_store()
		for item in datasink.get_bookmarks():
			self.view.append_item(item,group=False)
			
			
		
calendar = CalendarWidget()
timeline = TimelineWidget()
tb =TagBrowser()
filtersBox = FilterAndOptionBox()
bookmarks = BookmarksView()
bb = BrowserBar()
