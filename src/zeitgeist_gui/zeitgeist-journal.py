#! /usr/bin/env python
# -.- encoding: utf-8 -.-

import sys
import os
import signal
import gtk
import gobject
import gettext

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../"))
gettext.install('gnome-zeitgeist', '/usr/share/locale', unicode=1)

from zeitgeist_journal_widgets import *
from zeitgeist_shared.basics import BASEDIR

class Journal(gtk.Window):
	
	def __init__(self):
		
		gtk.Window.__init__(self)
		
		# Window
		self.set_title("GNOME Zeitgeist")
		self.set_resizable(True)
		#self.set_default_size(800, -1)
		self.set_icon_from_file("%s/data/logo/scalable/apps/gnome-zeitgeist.svg" % BASEDIR)
		
		self.connect("destroy", gtk.main_quit)
		self.connect('check-resize', self.window_state_event_cb)
		signal.signal(signal.SIGUSR1, lambda *discard: self.emit(gtk.main_quit))
		
		# Vertical box (contains self.hBox and a status bar)
		self.vBox = gtk.VBox(False, 5)
		self.vBox.pack_start(bb, False, False)
		self.add(self.vBox)
		
		# Horizontal box (contains the main content and a sidebar)
		self.hBox = gtk.HBox()
		self.vBox.pack_start(self.hBox, True, True,1)
		self.hBox.set_border_width(5)
		
		# Sidebar
		self.sidebar = gtk.VBox()
		
		#self.hBox.pack_start(bookmarks, False, False)
		
		# Filter/options box
		self.sidebar.pack_start(calendar, False, False)
		self.sidebar.pack_start(filtersBox, True, True)
		
		# Event box
		evbox = gtk.EventBox()
		evbox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("darkgrey"))
		evbox.add(timeline)
		
		# Notebook
		notebook = gtk.Notebook()
		notebook.connect("switch-page",self.switch_page)
		notebook.set_homogeneous_tabs(True)
		#notebook.set_property("tab-pos", gtk.POS_LEFT)
		
		journal = "%s/data/calendar.svg" % BASEDIR
		label = self.create_tab_label(_("Journal"), journal)
		notebook.append_page(evbox, label)
		notebook.set_tab_label_packing(evbox, True, True, gtk.PACK_START)
		
		starred = "%s/data/bookmark-new.svg" % BASEDIR
		label = self.create_tab_label(_("Bookmarks"), starred)
		notebook.append_page(bookmarks, label)
		notebook.set_tab_label_packing(bookmarks, True, True, gtk.PACK_START)
		
		box = gtk.VBox()
		notebook.append_page(box, gtk.Label("Most Used Stuff (not yet  implemented)"))
		notebook.set_tab_label_packing(box, True, True, gtk.PACK_START)
		#notebook.set_tab_label_packing(bookmarks, True, True, gtk.PACK_START)
		#notebook.set_tab_label_packing(evbox, True, True, gtk.PACK_START)
		
		self.connect("key-press-event",self.on_window_key_press_event)

		
		# vbox for timeline and tagbar
		vbox = gtk.VBox()
		vbox.pack_start(notebook, True, True)
		#vbox.pack_start(tagbox,False,True,2)
		
		hbox = gtk.HBox()
		self.hBox.pack_start(htb,False,True,2)
		hbox.pack_start(vbox,True,True,1)
		
		self.hBox.pack_start(hbox, True, True,5)
		self.hBox.pack_start(self.sidebar, False, False)
		
		# Status bar
		statusbar = gtk.Statusbar()
		self.vBox.pack_start(statusbar, False, False)
		
		# Show everything
		self.show_all()
		#bookmarks.hide_all()
		htb.hide_all()
		filtersBox.option_box.hide_all()
		calendar.hide_all()
		
		self.set_focus(None)
		
		
		
		#self.window_state_event_cb(None)
	def on_window_key_press_event(self,timelime,event):
		if event.keyval==65360:
			timeline.jump_to_day(str(datetime.datetime.today().strftime("%d %m %Y")).split(" "))
			self.set_focus(None)
		if event.keyval==65361:
			timeline.step_in_time(-1)

			timeline.get_dayboxes()[1][1].grab_focus()
		if event.keyval==65363:
			timeline.step_in_time(+1)
	
	def switch_page(self, notebook, page, page_num):	
		if page_num == 1 or page_num ==2:
			bb.set_time_browsing(False)
		else:
			bb.set_time_browsing(True)
			
	def create_tab_label(self, title, stock):
			box = gtk.HBox()
			
			pixbuf = icon_factory.load_icon(stock, icon_size = 16 ,cache = False)
			icon = gtk.Image()
			icon.set_from_pixbuf(pixbuf)
			del pixbuf

			label = gtk.Label(title)
			
			box.pack_start(icon, False, False)
			box.pack_start(label, True, True)
			box.show_all()
			return box

	def window_state_event_cb(self, window):
		
		width, height = self.get_size()
		
		#bookmarks.bookmarks.view.reload_name_cell_size(width-50)
		
		if width < 800:
			self.set_size_request(800,-1)
			width = 800

		timeline.clean_up_dayboxes(width/3)
		bookmarks.clean_up_dayboxes(width)

if __name__ == "__main__":
	
	journal = Journal()
	# Load data
	timeline.ready()

	try:
		gtk.main()
	except KeyboardInterrupt:
		sys.exit(0)
