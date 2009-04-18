import datetime
import gc
import os
import time
import sys
import gtk
import gobject
import pango
from gettext import ngettext, gettext as _ 

from zeitgeist_engine.zeitgeist_util import gconf_bridge
from zeitgeist_gui.zeitgeist_util import launcher
from zeitgeist_engine.xdgdirs import xdg_directory
from zeitgeist_gui.zeitgeist_util import launcher, icon_factory
from zeitgeist_gui.zeitgeist_engine_wrapper import engine
from zeitgeist_gui.zeitgeist_base import Data
from zeitgeist_gui.zeitgeist_bookmarker import bookmarker
from zeitgeist_shared.zeitgeist_shared import *

class TimelineWidget(gtk.ScrolledWindow):
	
	def __init__(self):
		# Initialize superclass
		gtk.ScrolledWindow.__init__(self)
		
		# Add children widgets
		self.view = DataIconView(True)
		self.dayboxes=gtk.HBox(False,False)
		self.days = {}
				
		# Set up default properties
		self.set_border_width(0)
		self.set_size_request(600, 200)
		self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_NEVER)
		self.add_with_viewport(self.dayboxes)
		
		# This contains the range of dates which we've currently loaded into the GUI
		self.begin = None
		self.end = None
		
		# The current tags that we're using to filter displayed results
		self.tags = ''
		
		# Get list of sources to filter
		self.sources = {}
		self.set_filters()
		
		# Connect to the calendar's (displayed in the sidebar) signals
		calendar.connect("month-changed", self.load_month)
		calendar.connect("day-selected", self.jump_to_day)
		calendar.connect("day-selected-double-click", self.jump_to_day, True)
		
		# GConf settings
		self.compress_empty_days = gconf_bridge.get("compress_empty_days")
		gconf_bridge.connect("changed::compress_empty_days", lambda gb: self.load_month())
		
		engine.connect("signal_updated", self.load_month_proxy)
		self.offset=0
		self.items = []
		
		# Load the GUI
		self.load_month()
	
	def set_filters(self):
		for source in engine.get_sources_list():
			self.sources[source[0]]=False
	
	def apply_search(self, tags="", search = True):
		'''
		Adds all items which match tags to the gui.
		'''
		
		self.tags = tags
		tagsplit = [tag.strip() for tag in \
			tags.replace(",", " ").split() if tag.strip()]
		
		print "----------------------------------------------------------"
		print tagsplit
		print "----------------------------------------------------------"
		
		days_range = int((self.end - self.begin ) / 86400) + 1 #get the days range
		
		self.days.clear()
		self.review_days()
		self.build_days(tagsplit, search)
	
	def build_days(self, tagsplit, search):
		for item in self.items:
			if not self.sources[item.type]:
				if len(tagsplit) > 0:
					for tag in tagsplit:
						if search:
							if item.uri.lower().find(tag.lower())>-1:
								if self.days.has_key(item.get_datestring()):
									daybox = self.days[item.get_datestring()]
									daybox.append_item(item)
									self.dayboxes.pack_start(daybox,False,False)
									self.days[item.get_datestring()]=daybox
									break
						
						if item.tags.lower().find(","+tag.lower()+",")> -1 or item.tags.lower().find(","+tag.lower())> -1 or item.tags.lower().find(tag.lower()+",")> -1 or item.tags.lower() == tag.lower()> -1:
							if self.days.has_key(item.get_datestring()):
								daybox = self.days[item.get_datestring()]
								daybox.append_item(item)
								self.dayboxes.pack_start(daybox, False, False)
								self.days[item.get_datestring()]=daybox
								break
				
				else:
					if self.days.has_key(item.get_datestring()):
						daybox = self.days[item.get_datestring()]
						daybox.append_item(item)
						self.dayboxes.pack_start(daybox, False, False)
						self.days[item.get_datestring()] = daybox
						
		
		self.clean_up_dayboxes()
	
	def review_days(self):
		
		days_range = int((self.end - self.begin) / 86400) +1 #get the days range
		
		'''
		Try avoiding rebuiling boxes and use currently available
		'''
		
		if days_range == len(self.dayboxes):
			i = 0
			for daybox in self.dayboxes:
				datestring = datetime.datetime.fromtimestamp(self.begin+(i*86400)).strftime(_("%a %d %b %Y"))
				daybox.clear()
				daybox.label.set_label(datestring)
				self.days[datestring]=daybox
				i = i + 1
		
		else:
			for daybox in self.dayboxes:
				self.dayboxes.remove(daybox)
				daybox.clear()
			#precalculate the number of dayboxes we need and generate the dayboxes
			for i in xrange(days_range):
				datestring = datetime.datetime.fromtimestamp(self.begin+(i*86400)).strftime(_("%a %d %b %Y"))
				self.days[datestring]=DayBox(datestring)
				self.dayboxes.pack_start(self.days[datestring])
	
	def clean_up_dayboxes(self):
		range = (self.end-self.begin) / 86400
		self.compress_empty_days = gconf_bridge.get("compress_empty_days")
		if self.compress_empty_days and range > 7:
			for daybox in self.dayboxes:
				if daybox.item_count == 0:
					daybox.label.set_label(".")
					daybox.view.set_size_request(-1,-1)
		gc.collect()
	
	def load_month_proxy(self,widget=None, begin=None, end=None):
		today = time.time()
		if today >= self.begin and today <= (self.end + 86400):
			self.load_month(begin=begin, end=end)
	
	def load_month(self, widget=None, begin=None, end=None, keep=False):
		'''
		Loads the current month selected on the calendar into the GUI.
		
		This is called when a new date is selected on the calendar
		or when the user types into the search bar. In the second case,
		we need to reload the GUI and only show items that match the tags
		parameter.
		'''
		
		# Begin benchmarking
		t1 = time.time()
		# Get date range
		# Format is (year, month-1, day)
		date = calendar.get_date()
		
		# Get the begin and end of this month
		# each tuple is of format (year, month, day, hours, minutes,
		# seconds, weekday, day_of_year, daylight savings) 
		
		day = date[2]
		if not keep:
			if begin == None and end == None:
				begin = (date[0], date[1]+1, day-1+self.offset, 0,0,0,0,0,0)
				end = (date[0], date[1]+1, day+2+self.offset, 0,0,0,0,0,0)
				self.begin = time.mktime(begin)
				self.end = time.mktime(end) -1
			
			else:
				self.begin = begin 
				self.end = end - 1
		
		t2 = time.time()
		print "Time to set up dates: "+str(t2-t1)
		
		# Note: To get the begin and end of a single day we would use the following
		#begin = (date[0], date[1]+1, date[2], 0,0,0,0,0,0)
		#end = (date[0], date[1]+1, date[2]+1, 0,0,0,0,0,0)
		
		# Get date as unix timestamp
		calendar.clear_marks()
		
		# Get all items in the date range and add them to self.items
		self.items = []
		for item in engine.get_items(self.begin, self.end, ""):
			if item.timestamp < self.end:
				self.items.append(item)
				item.connect("relate", self.set_relation)
		
		t3 = time.time()
		print "Time to get items: %s" % str(t3-t2)
		
		# Update the GUI with the items that match the current search terms/tags
		self.apply_search(self.tags)
		
		t4 = time.time()
		# Benchmarking
		print "Time to apply search on  %s items: %s" % (len(self.items), str(t4 -t3))
		print "Time for operation on %s items: %s \n" % (len(self.items), str(t4 -t1))
		
		gc.enable()		
		gc.set_debug(gc.DEBUG_LEAK)
		print gc.garbage
		gc.collect()
	
	def jump_to_day(self, widget,focus=False):
		'''
		Jump to the currently selected day in the calendar.
		'''
		
		self.offset = 0
		self.load_month()
		date = calendar.get_date()
		ctimestamp = time.mktime([date[0],date[1]+1,date[2],0,0,0,0,0,0])
		datestring = datetime.datetime.fromtimestamp(ctimestamp).strftime(_("%d %b %Y"))
		if focus == False:
			for w in self.dayboxes:
				w.show_all()
				if w.date == datestring:
					w.emit("set-focus-child",w)
		else:
			for w in self.dayboxes:
				w.hide_all()
				if w.date == datestring:
					w.show_all()
		
	def set_relation(self, item):
		related = RelatedWindow()
		related.set_relation(item)

	def focus_in(self, widget, event, adj):
		alloc = widget.get_allocation() 
		if alloc.x < adj.value or alloc.x > adj.value + adj.page_size:
			adj.set_value(min(alloc.x, adj.upper-adj.page_size))
			del widget 

class DayBox(gtk.VBox):
	def __init__(self,date):
		gtk.VBox.__init__(self)
		self.date=date
		self.label=gtk.Label(date)
		vbox = gtk.VBox()
		
		self.ev = gtk.EventBox()
		self.ev.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("#FFFAAA"))
		self.ev.add(vbox)
		self.ev.set_border_width(1)
		vbox.pack_start(self.label,True,True,5)
		
		self.pack_start(self.ev,False,False)
		self.view=DataIconView()
		if date.startswith("Sat") or date.startswith("Sun"):
			color = gtk.gdk.rgb_get_colormap().alloc_color('#EEEEEE')
			self.view.modify_base(gtk.STATE_NORMAL,color)

		self.scroll = gtk.ScrolledWindow()		
		self.scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
		self.scroll.add_with_viewport(self.view)
		self.pack_start(self.scroll)
		self.show_all()
		self.item_count=0
	
	def append_item(self,item):
		self.view.append_item(item)
		self.item_count +=1
		del item 
		
	def clear(self):
		self.view.clear_store()
		self.item_count = 0
	   
	def emit_focus(self):
			self.emit("set-focus-child", self) 
		  	  
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

class HTagBrowser(gtk.HBox):
	def __init__(self):
		# Initialize superclass
		gtk.HBox.__init__(self)
		self.set_size_request(-1,-1)
		self.combobox = gtk.combo_box_new_text()
		self.combobox.append_text('Recently used tags')
		self.combobox.append_text('Most used tags')
		
		hbox=gtk.HBox()
		
		hbox.pack_start(self.combobox, False, False)
				
		self.scroll = gtk.ScrolledWindow()
		self.ev = gtk.EventBox()
		self.ev.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))

		self.view = gtk.HBox()
		self.ev.add(self.view)
		self.scroll.add_with_viewport(self.ev)
		self.scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_NEVER)
		self.scroll.set_shadow_type(gtk.SHADOW_NONE)
		hbox.pack_start(self.scroll,True,True)
		self.show_all()
		self.items = []
		
		self.func = self.get_recent_tags
		
		self.func()
	
		self.combobox.connect('changed', self.changed_cb)
		self.combobox.set_active(0)
		self.pack_start(hbox,True,True)
		engine.connect("signal_updated", lambda *args: self.func)

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
	
	def _tag_toggle_button(self, tag):
		btn = gtk.ToggleButton(tag)
		btn.set_size_request(-1, -1)
		btn.set_relief(gtk.RELIEF_NONE)
		btn.set_focus_on_click(False)
		self.view.pack_start(btn, True, True)
		btn.connect("toggled", self.toggle)
	
	def get_recent_tags(self, x=None):
		
		date = calendar.get_date()
		
		begin = time.mktime((date[0], date[1]+1, 1, 0,0,0,0,0,0))
		end = time.mktime((date[0], date[1]+2, 0, 0,0,0,0,0,0))
		
		for w in self.view:
			self.view.remove(w)
		
		for tag in engine.get_recent_used_tags(10, begin, end):
			self._tag_toggle_button(tag)
			
		self.show_all()
	
	def get_most_tags(self, x=None):
		
		begin = timeline.begin
		end = timeline.end
		
		for w in self.view:
			self.view.remove(w)
		
		for tag in engine.get_most_used_tags(10, begin, end):
			self._tag_toggle_button(tag)
		
		self.show_all()
	
	def toggle(self, x=None):
		
		tags = timeline.tags
		if x.get_active():
			if tags.find(x.get_label()) == -1:
				 tags = tags + "," + x.get_label()
				 begin, end = engine.get_timestamps_for_tag(x.get_label())
				 timeline.load_month(begin=begin, end=end)
		else:
			if tags.find(x.get_label()) > -1:
				 tags = tags.replace("," + x.get_label(), ",")
				 tags = tags.replace(x.get_label() + ",", ",")
				 timeline.load_month()
		
		timeline.apply_search(tags,False)
		
	def untoggle_all(self):
		for btn in self.view:
			btn.set_active(False)
		
class VTagBrowser(gtk.VBox):
	def __init__(self):
		# Initialize superclass
		gtk.VBox.__init__(self)
		self.set_size_request(-1,-1)
		self.combobox = gtk.combo_box_new_text()
		self.reload_tags()
		
		self.combobox.connect('changed', self.changed_cb)
		self.combobox.set_active(0)
		self.pack_start(self.combobox,True,True,5)
		engine.connect("signal_updated", lambda *args: self.func)
		
	def reload_tags(self,x=None):
		self.func = self.get_recent_tags()
		self.func = self.get_most_tags()

	def changed_cb(self, combobox=None):
		label = combobox.get_active_text()
		projectview.view.clear_store()
		for item in engine.get_items_for_tag(label):
			projectview.view.append_item(item)
		
	def get_recent_tags(self, x=None):
		
		date = calendar.get_date()
		
		begin = time.mktime((date[0], date[1]+1, 1, 0,0,0,0,0,0))
		end = time.mktime((date[0], date[1]+2, 0, 0,0,0,0,0,0))
		
		for tag in engine.get_recent_used_tags(10, begin, end):
			print tag
			self.combobox.append_text(tag)
			
	def get_most_tags(self, x=None):
		
		begin = timeline.begin
		end = timeline.end
		
		for tag in engine.get_most_used_tags(10, begin, end):
			print tag
			self.combobox.append_text(tag)
	
		
							   
class FilterAndOptionBox(gtk.VBox):
	
	def __init__(self):
		
		gtk.VBox.__init__(self)
		self.option_box = gtk.VBox(False)
		self.create_doc_btn = gtk.Button("Create New Document")
		self.create_doc_btn.connect("clicked", self._show_new_from_template_dialog)
		self.create_note_btn = gtk.Button("Create New Note")
		self.create_note_btn.connect("clicked", self._make_new_note)
		self.option_box.pack_end(self.create_doc_btn, False, False)
		self.option_box.pack_end(self.create_note_btn, False, False)
		self.timefilter_active=False
		self.filters=[]
		
		'''
		Filter Box
		'''
		
		#self.search = SearchToolItem()
		#self.pack_start( self.search ,False,False,0)
		self.pack_start(calendar, False, False, 0)
		
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
		for source in engine.get_sources_list():
			filter = CheckBox(source)
			filter.set_active(True)
			self.voptionbox.pack_start(filter, False, False, 0)
			self.filters.append(filter)
		
		self.frame2.add(self.voptionbox)
		self.date_dict = None
		
		# GConf settings
		gconf_bridge.connect("changed::show_note_button", lambda gb: self.set_buttons())
		gconf_bridge.connect("changed::show_file_button", lambda gb: self.set_buttons())
		self.show_all()
		self.set_buttons()
		
	def set_buttons(self):
		note = gconf_bridge.get("show_note_button")
		if note:
			self.create_note_btn.show_all()
		else:
			self.create_note_btn.hide_all()
			
		file = gconf_bridge.get("show_file_button")
		if file:
			self.create_doc_btn.show_all()
		else:
			self.create_doc_btn.hide_all()
	
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
		
class CalendarWidget(gtk.Calendar):
	def __init__(self):
		gtk.Calendar.__init__(self)
		self.show_all()

class CheckBox(gtk.CheckButton):
	
	def __init__(self, source):
		
		gtk.CheckButton.__init__(self)
		self.set_border_width(5)
		self.set_focus_on_click(False)
		self.connect("toggled", self.toggle_source)
		
		self.source = source
		self.set_label(source[0])
		self.set_active(self.source[2])
		
		icon = icon_factory.load_icon(source[1], icon_size = 16)
		self.image = gtk.Image()
		self.image.set_from_pixbuf(icon)
		self.set_image(self.image)
		
		self.show_all()
	
	def toggle_source(self, widget=None):
		if self.get_active():
			timeline.sources[self.source[0]]=False
			pass
			#self.source.set_active(True)
			# FIXME - ???
			#search.emit("clear")
		else:
			timeline.sources[self.source[0]]=True
			pass
			#self.source.set_active(False)
		
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
		self.set_current_folder(xdg_directory("desktop", "~/Desktop"))
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
		timeline.load_month()
	
	def do_search(self, text):
		# Get date range
		# Format is (year, month-1, day)
		date = calendar.get_date()
		
		
		# Get the begin and end of this month
		# each tuple is of format (year, month, day, hours, minutes,
		# seconds, weekday, day_of_year, daylight savings) 
		
		day = date[2]
		begin = (date[0], date[1]+1,0, 0,0,0,0,0,0)
		end = (date[0], date[1]+2, 0, 0,0,0,0,0,0)
		begin = time.mktime(begin)
		end = time.mktime(end) -1
		
		timeline.load_month(begin=begin, end=end)
		
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
			self.search_timeout = gobject.timeout_add(500, self._typing_timeout)

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
		self.set_size_request(250,-1)
		self.parentdays = parentdays
		
		self.store = gtk.TreeStore(gtk.gdk.Pixbuf, str, str, gobject.TYPE_BOOLEAN, gobject.TYPE_PYOBJECT)
		
		icon_cell = gtk.CellRendererPixbuf()
		icon_column = gtk.TreeViewColumn("",icon_cell,pixbuf=0)
		icon_column.set_fixed_width(32)
		
		name_cell = gtk.CellRendererText()
		name_cell.set_property("wrap-mode", pango.WRAP_WORD_CHAR)
		name_cell.set_property("wrap-width", 125)
		name_column = gtk.TreeViewColumn("Name", name_cell, markup=1)
		name_column.set_fixed_width(125)
		
		time_cell = gtk.CellRendererText()
		time_column = gtk.TreeViewColumn("Time",time_cell,markup=2)
		time_column.set_fixed_width(32)
		
		bookmark_cell = gtk.CellRendererToggle()
		bookmark_cell.set_property('activatable', True)
		bookmark_cell.connect( 'toggled', self.toggle_bookmark, self.store )
		bookmark_column = gtk.TreeViewColumn("bookmark",bookmark_cell)
		bookmark_column.add_attribute( bookmark_cell, "active", 3)
		bookmark_column.set_fixed_width(32)
				
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
		self.connect("focus-out-event",self.unselect_all)
		
		self.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, [("text/uri-list", 0, 100)], gtk.gdk.ACTION_LINK | gtk.gdk.ACTION_COPY)
		self.last_item=None
		self.day=None
		engine.connect("signal_updated", lambda *args: self._do_refresh_rows())
		
		#self.store.set_sort_column_id(2, gtk.SORT_ASCENDING)
		self.types = {}
		self.days={}
		self.last_item = ""
		self.items_uris=[]
		
	def append_item(self, item,group=True):
		# Add an item to the end of the store
		self._set_item(item, group=group)
		#self.set_model(self.store)
		pass
		
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
		except:
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
		treeselection = self.get_selection()
		model, iter = treeselection.get_selected()
		item = model.get_value(iter, 4)
		return item
	
	def _show_item_popup(self, view, ev):
		if ev.button == 3:
			item = self.get_selected_item()
			if item:
				menu = gtk.Menu()
				menu.attach_to_widget(view, None)
				item.populate_popup(menu)
				menu.popup(None, None, None, ev.button, ev.time)
				return True
	
	def _item_drag_data_get(self, view, drag_context, selection_data, info, timestamp):
		# FIXME: Prefer ACTION_LINK if available
		print("_item_drag_data_get")
		uris = []
		treeselection = self.get_selection()
		model, iter = treeselection.get_selected()
		item = model.get_value(iter, 4)
		if not item:
			print "ERROR"
		uris.append(item.get_uri())
		
		pass #print " *** Dropping URIs:", uris
		selection_data.set_uris(uris)
	
	def toggle_bookmark( self, cell, path, model ):
		"""
		Sets the toggled state on the toggle button to true or false.
		"""
		
		model[path][3] = not model[path][3]
		item = model[path][4]
		item.add_bookmark()

	def _do_refresh_rows(self):
		refresh=False
		if len(bookmarker.bookmarks) > 0:	
			for uri in self.items_uris:
				if bookmarker.get_bookmark(uri):
					refresh = True
					break
				
			if refresh:
				iter = self.store.get_iter_root()
				if iter:
					item = self.store.get_value(iter, 4)
					try:
						self.store.set(iter,3,bookmarker.get_bookmark(item.uri))
					except:
						pass
					while True:
						iter = self.store.iter_next(iter)
						if iter:
							item = self.store.get_value(iter, 4)
							try:
								self.store.set(iter,3,bookmarker.get_bookmark(item.uri))
							except:
								pass
						else:
							break
		else:
			iter = self.store.get_iter_root()
			if iter:
				item = self.store.get_value(iter, 4)
				self.store.set(iter,3,False)
				while True:
					iter = self.store.iter_next(iter)
					if iter:
						item = self.store.get_value(iter, 4)
						self.store.set(iter,3,False)
					else:
						break
	
	def _set_item(self, item, append=True, group=True):
		
		func = self.store.append
		bookmark = bookmarker.get_bookmark(item.uri)
		parent = None
		
		if self.parentdays:
			if not self.types.has_key(item.type):
				parent = func(None,[None,#item.get_icon(24),
										"<span size='x-large' color='blue'>%s</span>" % item.type,
										"",
										False,
										None])
				self.types[item.type]=parent
			else:
				parent = self.types[item.type]
			
		self.items_uris.append(item.uri)
		
		if not item.timestamp == -1.0:
			date="<span size='small' color='blue'>%s</span>" % item.get_time()
		else:
			date=""
		
		func(parent,[item.get_icon(24),
				"<span color='black'>%s</span>" % item.get_name(),
				date,
				bookmark,
				item])
		
		self.expand_all()
		
class BrowserBar(gtk.HBox):
	
	def __init__(self):
		
		gtk.HBox.__init__(self)   
		self.tooltips = gtk.Tooltips()

		self.home = gtk.ToolButton("gtk-home")
		self.home.set_label("Recent")
		self.home.connect("clicked", self.focus_today)
		self.tooltips.set_tip(self.home, "Show recent activities")

		self.back = gtk.ToolButton("gtk-go-back")
		self.back.set_label("Older")
		self.back.connect("clicked", self.add_day)
		self.tooltips.set_tip(self.back, "Go back in time")
		
		self.forward = gtk.ToolButton("gtk-go-forward")
		self.forward.set_label("Newer")
		self.forward.connect("clicked", self.remove_day)
		self.tooltips.set_tip(self.forward, "Go to the future")
		
		self.options = gtk.ToggleToolButton("gtk-select-color")
		self.tooltips.set_tip(self.options, "Filter your current view")
		self.options.set_label("Filters")
		
		self.star = gtk.ToggleToolButton("gtk-about")
		self.star.set_label("Bookmarks")
		self.tooltips.set_tip(self.star, "View bookmarked activities")
		self.star.connect("toggled",self.toggle_bookmarks)
		
		self.tags = gtk.ToggleToolButton("gtk-dialog-warning")
		self.tags.set_label("Tags")
		self.tooltips.set_tip(self.tags, "View tagged activities")
		self.tags.connect("toggled", self.toggle_tags)
		
		toolbar = gtk.Toolbar()
		toolbar.add(self.back)
		toolbar.add(self.home)
		toolbar.add(self.forward)
		toolbar.add(gtk.SeparatorToolItem())
		toolbar.add(self.star)
		toolbar.add(self.tags)
		toolbar.add(self.options)
		self.pack_start(toolbar, True, True, 4)
		
		hbox = gtk.HBox()
		hbox.pack_start(gtk.HBox(), True, True, 5)
		
		# Search Area
		self.search = SearchToolItem()
		hbox.pack_start(self.search, True, True)
		clear_btn = gtk.ToolButton("gtk-clear")
		clear_btn.connect("clicked", lambda x: self.search.do_clear())
		hbox.pack_start(clear_btn, False, False, 4)
		
		self.pack_start(hbox, True, True)
	
	def remove_day(self, x=None):
		htb.untoggle_all()
		timeline.offset +=  1
		timeline.load_month()
	
	def toggle_bookmarks(self, x=None):
		if self.star.get_active():
			bookmarks.show_all()
		else:
			bookmarks.hide_all()
	
	def toggle_tags(self, x=None):
		if self.tags.get_active():
			htb.show_all()
		else:
			htb.hide_all()
		
	def add_day(self, x=None):
		htb.untoggle_all()
		timeline.offset -= 1
		timeline.load_month()

	def focus_today(self, x=None):
		timeline.offset = 0
		today = time.time()
		month = int(datetime.datetime.fromtimestamp(today).strftime(_("%m")))-1
		year = int(datetime.datetime.fromtimestamp(today).strftime(_("%Y")))
		day = int(datetime.datetime.fromtimestamp(today).strftime(_("%d")))
		calendar.select_month(month,year)
		calendar.select_day(day)
		#calendar.do_day_selected_double_click()
		
		
class BookmarksView(gtk.VBox):
	def __init__(self):
		gtk.VBox.__init__(self)
		
		vbox=gtk.VBox()
		
		self.label = gtk.Label("Bookmarks")
		#self.label.set_padding(5,5)
		vbox.pack_start(self.label, False, True, 5)
		self.view = DataIconView()

		ev = gtk.EventBox()
		ev.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("#FFFAAA"))
		evbox = gtk.EventBox()
		evbox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("darkgrey"))
		evbox1 = gtk.EventBox()
		evbox1.set_border_width(1)
		evbox1.add(ev)
		evbox.add(evbox1)
		ev.set_border_width(1)
		ev.add(vbox)
				
		evbox2 = gtk.EventBox()
		evbox2.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("darkgrey"))
		evbox3 = gtk.EventBox()
		evbox3.set_border_width(1)
		evbox3.add(self.view)
		evbox2.add(evbox3)
					
		vbox.pack_start(evbox2,True,True)
		self.pack_start(evbox,True,True)
		self.get_bookmarks()
		engine.connect("signal_updated", self.get_bookmarks)

	def get_bookmarks(self, x=None):
		self.view.clear_store()
		for item in bookmarker.get_items_uncached():
			self.view.append_item(item, group=False)

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

class ProjectView(gtk.ScrolledWindow):
	def __init__(self):
		gtk.ScrolledWindow.__init__(self)
		self.view = DataIconView(True)
		self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self.add_with_viewport(self.view)
		

calendar = CalendarWidget()
timeline = TimelineWidget()
projectview = ProjectView()
htb = HTagBrowser()
vtb = VTagBrowser()
filtersBox = FilterAndOptionBox()
bookmarks = BookmarksView()
bb = BrowserBar()

