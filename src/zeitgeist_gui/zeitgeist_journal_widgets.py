# -.- encoding: utf-8 -.-

import datetime
import time
import math
import gc
import os
import time
import sys
import gtk
import gobject
import pango
import gettext

from zeitgeist_gui.zeitgeist_util import launcher, gconf_bridge
from zeitgeist_gui.zeitgeist_util_widgets import *
from zeitgeist_shared.xdgdirs import xdg_directory
from zeitgeist_gui.zeitgeist_util import launcher, icon_factory
from zeitgeist_gui.zeitgeist_engine_wrapper import engine
from zeitgeist_shared.zeitgeist_shared import *
from zeitgeist_shared.basics import BASEDIR

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
		self.tags = ""
		
		# Get list of sources to filter
		self.sources = {}
		self.sources_icons = {}
		
		# Connect to the calendar's (displayed in the sidebar) signals
		calendar.connect("month-changed", self.load_month)
		calendar.connect("day-selected", self.jump_to_day)
		calendar.connect("day-selected-double-click", self.jump_to_day, True)
		
		# GConf settings
		self.compress_empty_days = gconf_bridge.get("compress_empty_days")
		gconf_bridge.connect("changed::compress_empty_days", lambda gb: self.load_month())
		
		self.offset = 0
		self.items = []
		self._ready = False
	
	def ready(self):
		'''
		Only call this one time, once the GUI has loaded and we can
		start listening to events.
		'''
		
		assert self._ready == False
		self._ready = True
		
		engine.connect("signal_updated", self.load_month_proxy)
		
		# Load the GUI
		self.load_month()
		self.load_month()
	
	def apply_search(self, tags="", search = True):
		'''
		Adds all items which match tags to the gui.
		'''
		
		print "apply search"
		
		self.tags = tags
		tagsplit = [tag.strip() for tag in \
			tags.split(",") if tag.strip()]
		
		self.days.clear()
		self.review_days()
		self.build_days(tagsplit, search)
	
	def build_days(self, tagsplit, search):
		
		print "building days"
		
		for item in self.items:
			if self.sources[item.type]:
				continue
			if tagsplit:
				for tag in tagsplit:
					if search and tag.lower() in item.uri.lower():
						self._append_to_day(item)
					elif tag.lower() in item.tags.lower().split(","):
						self._append_to_day(item)
			else:
				self._append_to_day(item)
	
		self.clean_up_dayboxes(-1)
	
	def _append_to_day(self, item):
		daybox = self.days[item.get_datestring()]
		daybox.append_item(item)
		self.dayboxes.pack_start(daybox, False, False)
		self.days[item.get_datestring()] = daybox
		
	def review_days(self):
		
		days_range = int((self.end - self.begin) / 86400) + 1 # get the days range
		
		'''
		Try avoiding rebuiling boxes and use currently available
		'''
		
		if days_range == len(self.dayboxes):
			for i, daybox in enumerate(self.dayboxes):
				datestring = datetime.datetime.fromtimestamp(self.begin+(i*86400)).strftime("%a %d %b %Y")
				daybox.clear()
				daybox.label.set_label(datestring)
				self.days[datestring] = daybox
		else:
			for daybox in self.dayboxes:
				self.dayboxes.remove(daybox)
				daybox.clear()
			# precalculate the number of dayboxes we need and generate the dayboxes
			for i in xrange(days_range):
				datestring = datetime.datetime.fromtimestamp(self.begin+(i*86400)).strftime("%a %d %b %Y")
				self.days[datestring]=DayBox(datestring)
				self.dayboxes.pack_start(self.days[datestring])
	
	def clean_up_dayboxes(self, width):
		
		print "cleaning up"
		
		self.compress_empty_days = gconf_bridge.get("compress_empty_days")
		if self.compress_empty_days:
			i = len(self.dayboxes) -1
			for daybox in self.dayboxes:
				if daybox.item_count == 0 and self.tags:
					if i == len(self.dayboxes) -1 or i == 0:
						daybox.hide()
					else:
						daybox.label.set_label(".")
						daybox.view.set_size_request(-1,-1)
						daybox.show()
				else:
					daybox.view.reload_name_cell_size(width)
					daybox.show()
				i = i - 1
		gc.collect()
	
	def load_month_proxy(self,widget=None, begin=None, end=None):
		today = time.time()
		if today >= self.begin and today <= (self.end + 86400):
			self.load_month(begin=begin, end=end)
	
	def load_month(self, widget=None, begin=None, end=None, cached=False):
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
		
		# Begin benchmarking
		t1 = time.time()
				
		if not cached:	
			print "Getting uncached items"
			if begin == None and end == None:
				begin = (date[0], date[1]+1, day-1+self.offset,0,0,0,0,0,-1)
				end = (date[0], date[1]+1, day+2+self.offset, 0,0,0,0,0,-1)
				self.begin = time.mktime(begin) 
				self.end = time.mktime(end) -1
			
			else:
				self.begin = begin 
				self.end = end - 1
		
			# Note: To get the begin and end of a single day we would use the following
			#begin = (date[0], date[1]+1, date[2], 0,0,0,0,0,0)
			#end = (date[0], date[1]+1, date[2]+1, 0,0,0,0,0,0)
			
			# Get date as unix timestamp
			calendar.clear_marks()
			
			# Get all items in the date range and add them to self.items
			self.items = []
			
			for item in engine.get_items(self.begin, self.end, ""):
						
				if item.timestamp <= self.end:
					
					if not self.sources.has_key(item.type):
						self.sources[item.type]=False
						self.sources_icons[item.type] = item.icon
					
					self.items.append(item)
					item.connect("relate", self.set_relation)
			
			try:
				filtersBox.reload()
			except:
				pass
			
		# Update the GUI with the items that match the current search terms/tags
		t3 = time.time()
		print "Time to get items: %s" % str(t3-t1)
		
		self.apply_search(self.tags)
		
		t4 = time.time()
		# Benchmarking
		print "Time to apply search on %s items: %s" % (len(self.items), str(t4 -t3))
		print "Time for operation on %s items: %s \n" % (len(self.items), str(t4 -t1))
		
	def jump_to_day(self, widget,focus=False):
		'''
		Jump to the currently selected day in the calendar.
		'''
		
		self.offset = 0
		self.load_month()
		date = calendar.get_date()
		ctimestamp = time.mktime([date[0],date[1]+1,date[2],0,0,0,0,0,0])
		datestring = datetime.datetime.fromtimestamp(ctimestamp).strftime("%d %b %Y")
		if focus == False:
			for w in self.dayboxes:
				w.show_all()
				if w.date == datestring:
					w.emit("set-focus-child", w)
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

class HTagBrowser(gtk.HBox):
	
	def __init__(self):
		
		# Initialize superclass
		gtk.HBox.__init__(self)
		self.set_size_request(-1,48)
		
		TARGET_TYPE_TEXT = 80
		TARGET_TYPE_PIXMAP = 81
		
		self.fromImage = [ ( "text/plain", 0, TARGET_TYPE_TEXT )]

		self.combobox = gtk.combo_box_new_text()
		self.combobox.append_text(_("Recently used tags"))
		self.combobox.append_text(_("Most used tags"))
		
		self.pack_start(self.combobox, False, False)
		
		self.scroll = gtk.ScrolledWindow()
		self.view = gtk.HBox()
		self.scroll.add_with_viewport(self.view)
		self.scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_NEVER)
		self.scroll.set_shadow_type(gtk.SHADOW_NONE)
		self.pack_start(self.scroll,True,True)
		self.show_all()
		self.items = []
		
		self.func = self.get_recent_tags
		self.func()
	
		self.combobox.connect("changed", self.changed_cb)
		self.combobox.set_active(0)
		
		engine.connect("signal_updated", lambda *args: self.func)

	def reload_tags(self, x=None):
		index = self.combobox.get_active()
		if index == 0:
			self.func = self.get_recent_tags
		else:
			self.func = self.get_most_tags

	def changed_cb(self, combobox=None):
		index = self.combobox.get_active()
		if index == 0:
			self.func = self.get_recent_tags()
		else:
			self.func = self.get_most_tags()
	
	def _tag_toggle_button(self, tag):
		
		btn = gtk.ToggleButton(tag)
		image = gtk.image_new_from_file("%s/data/tag.png" % BASEDIR)
		btn.connect("drag_data_get", self.sendCallback)
		btn.drag_source_set(gtk.gdk.BUTTON1_MASK, self.fromImage,gtk.gdk.ACTION_COPY)

		btn.set_image(image)
		btn.set_size_request(-1, 28)
		btn.set_relief(gtk.RELIEF_NONE)
		btn.set_focus_on_click(False)
		self.view.pack_start(btn, True, True)
		btn.connect("toggled", self.toggle)
	
	def sendCallback(self, widget, context, selection, targetType, eventTime):
		selection.set(selection.target, 8, "tag://"+widget.get_label())

	
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
		
		timeline.apply_search(tags, False)
	
	def is_any_toggled(self):
		for w in self.view:
			if w.get_active():
				return True
		return False
	
	def untoggle_all(self):
		for btn in self.view:
			btn.set_active(False)
		timeline.tags = ""

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
	
	def reload_tags(self, x=None):
		index = self.combobox.get_active()
		if index == 0:
			self.func = self.get_recent_tags
		else:
			self.func = self.get_most_tags
	
	def changed_cb(self, combobox=None):
		label = combobox.get_active_text()
		if label:
			projectview.view.clear_store()
			for item in engine.get_items_for_tag(label):
				projectview.view.append_item(item)
	
	def get_recent_tags(self, x=None):
		
		date = calendar.get_date()
		
		begin = time.mktime((date[0], date[1]+1, 1, 0,0,0,0,0,0))
		end = time.mktime((date[0], date[1]+2, 0, 0,0,0,0,0,0))
		
		for tag in engine.get_recent_used_tags(10, begin, end):
			self.combobox.append_text(tag)
			
	def get_most_tags(self, x=None):
		
		begin = timeline.begin
		end = timeline.end
		
		for tag in engine.get_most_used_tags(10, begin, end):
			self.combobox.append_text(tag)

class FilterAndOptionBox(gtk.VBox):
	
	def __init__(self):
		
		gtk.VBox.__init__(self)
		self.option_box = gtk.VBox(False)
		self.create_doc_btn = gtk.Button(_("Create New Document..."))
		self.create_doc_btn.connect("clicked", self._show_new_from_template_dialog)
		self.create_note_btn = gtk.Button(_("Create New Note"))
		self.create_note_btn.connect("clicked", self._make_new_note)
		self.option_box.pack_end(self.create_doc_btn, False, False)
		self.option_box.pack_end(self.create_note_btn, False, False)
		self.timefilter_active=False
		self.filters = {}
		
		'''
		Filter Box
		'''
		
		self.option_box.set_size_request(178,-1)
		
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
		self.reload()
		
		self.frame2.add(self.voptionbox)
		self.date_dict = None
		
		# GConf settings
		gconf_bridge.connect("changed::show_note_button", lambda gb: self.set_buttons())
		gconf_bridge.connect("changed::show_file_button", lambda gb: self.set_buttons())
		self.show_all()
		self.set_buttons()
	
	def reload(self):		 
		for source in timeline.sources.keys():
			if not self.filters.has_key(source):
				filter = CheckBox(source)
				filter.set_active(True)
				self.voptionbox.pack_start(filter, False, False, 0)
				self.filters[source] = filter
	
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
	
	def set_timelinefilter(self, *discard):
		self.timefilter_active = self.timefilter.get_active()
		
	def _make_new_note(self, *discard):
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
		
		self.source = source
		self.set_label(source)
		self.set_active(timeline.sources[source])
		
		icon = icon_factory.load_icon(timeline.sources_icons[source], icon_size = 24)
		self.image = gtk.Image()
		self.image.set_from_pixbuf(icon)
		self.set_image(self.image)
		
		# Leave this at the end, as else the callback will reload
		# the GUI several times.
		self.connect("toggled", self.toggle_source)
		
		self.show_all()
	
	def toggle_source(self, widget=None):
		timeline.sources[self.source] = not self.get_active()
		print timeline.sources[self.source]
		timeline.load_month(cached=True)

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

		self.entry.set_width_chars(30)
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
		timeline.tags=""
		#timeline.load_month()
	
	def do_search(self, text):
		# Get date range
		# Format is (year, month-1, day)
		date = calendar.get_date()
		
		# Get the begin and end of this month
		# each tuple is of format (year, month, day, hours, minutes,
		# seconds, weekday, day_of_year, daylight savings) 
		
		begin = (date[0], date[1]+1,0, 0,0,0,0,0,0)
		end = (date[0], date[1]+2, 0, 0,0,0,0,0,0)
		begin = time.mktime(begin)
		end = time.mktime(end) -1
		
		#timeline.load_month(begin=begin, end=end)
		
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

class BrowserBar(gtk.HBox):
	
	def __init__(self, htb):
		
		self.htb = htb
		gtk.HBox.__init__(self)   
		self.tooltips = gtk.Tooltips()

		self.home = gtk.ToolButton("gtk-home")
		self.home.set_label("Recent")
		self.home.connect("clicked", self.focus_today)
		self.tooltips.set_tip(self.home, _("Show recent activities"))

		self.back = gtk.ToolButton("gtk-go-back")
		self.back.set_label("Older")
		self.back.connect("clicked", self.add_day)
		self.tooltips.set_tip(self.back, _("Go back in time"))
		
		self.forward = gtk.ToolButton("gtk-go-forward")
		self.forward.set_label("Newer")
		self.forward.connect("clicked", self.remove_day)
		self.tooltips.set_tip(self.forward, _("Go to the future"))
		
		self.options = gtk.ToggleToolButton("gtk-select-color")
		self.tooltips.set_tip(self.options, _("Filter your current view"))
		self.options.set_label("Filters")
		self.options.connect("toggled",self.toggle_options)
		
		self.calendar = gtk.ToggleToolButton()
		icon = gtk.image_new_from_file("%s/data/calendar.png" % BASEDIR)
		icon.set_pixel_size(16)
		self.calendar.set_icon_widget(icon)
		self.tooltips.set_tip(self.calendar, _("View journal for a specific date"))
		self.calendar.set_label("Calendar")
		self.calendar.connect("toggled",self.toggle_calendar)
		
		'''
		self.star = gtk.ToggleToolButton()
		icon = gtk.image_new_from_file("%s/data/bookmark-new.png" % BASEDIR)
		self.star.set_icon_widget(icon)
		self.star.set_label("Bookmarks")
		self.tooltips.set_tip(self.star, _("View bookmarked activities"))
		self.star.connect("toggled",self.toggle_bookmarks)
		'''
		
		self.tags = gtk.ToggleToolButton()
		icon = gtk.image_new_from_file("%s/data/tag.png" % BASEDIR)
		icon.set_pixel_size(24)
		self.tags.set_icon_widget(icon)
		self.tags.set_label("Tags")
		self.tooltips.set_tip(self.tags, _("View tagged activities"))
		self.tags.connect("toggled", self.toggle_tags)
		
		toolbar = gtk.Toolbar()
		toolbar.insert(self.back, -1)
		toolbar.insert(self.home, -1)
		toolbar.insert(self.forward, -1)
		
		self.sep = gtk.SeparatorToolItem()
		
		toolbar.insert(self.sep,-1)
		#toolbar.insert(self.star, -1)
		toolbar.insert(self.tags, -1)
		toolbar.insert(self.options, -1)
		toolbar.insert(self.calendar, -1)
		toolbar.set_style(gtk.TOOLBAR_ICONS)
		
		hbox = gtk.HBox()
		hbox.pack_start(toolbar,True,True)
		
		toolbar2 = gtk.Toolbar()
		searchbox = gtk.HBox()
		# Search Area
		self.search = SearchToolItem()
		searchbox.pack_start(self.search, True, True)
		clear_btn = gtk.ToolButton("gtk-clear")
		clear_btn.connect("clicked", lambda x: self.search.do_clear())
		searchbox.pack_start(clear_btn, False, False)
		toolbar2.add(searchbox)
		
		hbox2 = gtk.HBox(True)
		hbox2.pack_start(toolbar2)
		
		self.pack_start(hbox, True, True)
		self.pack_start(hbox2, False, False)
	
	def set_time_browsing(self, bool):
		if bool:
				self.back.show()
				self.home.show()
				self.sep.show()
				self.forward.show()
				self.calendar.show()
		else:
				self.back.hide()
				self.home.hide()
				self.sep.hide()
				self.forward.hide()
				self.calendar.hide()
	
	def remove_day(self, x=None):
		self.htb.untoggle_all()
		timeline.offset +=  1
		timeline.load_month()
	
	def toggle_options(self, x=None):
		if self.options.get_active():
			filtersBox.option_box.show_all()
		else:
			filtersBox.option_box.hide_all()
	
	def toggle_bookmarks(self, x=None):
		if self.star.get_active():
			bookmarks.show_all()
		else:
			bookmarks.hide_all()
			
	def toggle_calendar(self, x=None):
		if self.calendar.get_active():
			calendar.show_all()
		else:
			calendar.hide_all()
	
	def toggle_tags(self, x=None):
		if self.tags.get_active():
			self.htb.show_all()
		else:
			self.htb.hide_all()
		
	def add_day(self, x=None):
		self.htb.untoggle_all()
		timeline.offset -= 1
		timeline.load_month()

	def focus_today(self, x=None):
		today = str(datetime.datetime.today().strftime("%d %m %Y")).split(" ")
		date = calendar.get_date()
		calendar.select_day(int(today[0]))
		if not int(today[1])-1 == int(date[1]):
			calendar.select_month(int(today[1])-1, int(today[2]))
		
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
bb = BrowserBar(htb)
