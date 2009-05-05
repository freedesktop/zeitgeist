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
		self.set_default_size(800, -1)
		self.set_icon_from_file("%s/data/gnome-zeitgeist.png" % BASEDIR)
		
		self.connect("destroy", gtk.main_quit)
		self.connect('check-resize', self.window_state_event_cb)
		signal.signal(signal.SIGUSR1, lambda *discard: self.emit(gtk.main_quit))
		
		# Vertical box (contains self.hBox and a status bar)
		self.vBox = gtk.VBox(False, 5)
		tagbox = gtk.HBox()
		tagbox.pack_start(htb, True, True)
		self.vBox.pack_start(bb, False, False)
		self.add(self.vBox)
		
		# Horizontal box (contains the main content and a sidebar)
		self.hBox = gtk.HBox()
		self.vBox.pack_start(self.hBox, True, True,1)
		
		# Sidebar
		self.sidebar = gtk.VBox()
		
		self.hBox.pack_start(bookmarks, False, False)
		
		# Filter/options box
		self.sidebar.pack_start(filtersBox, True, True)
		
		# Event box
		evbox = gtk.EventBox()
		evbox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("darkgrey"))
		evbox.add(timeline)
		
		# vbox for timeline and tagbar
		vbox = gtk.VBox()
		vbox.pack_start(evbox)
		vbox.pack_start(tagbox,False,True,2)
		
		hbox = gtk.HBox()
		hbox.pack_start(vbox,True,True,1)
		
		self.hBox.pack_start(hbox, True, True,5)
		self.hBox.pack_start(self.sidebar, False, False)
		
		# Status bar
		statusbar = gtk.Statusbar()
		self.vBox.pack_start(statusbar, False, False)
		
		# Show everything
		self.show_all()
		bookmarks.hide_all()
		htb.hide_all()
		filtersBox.option_box.hide_all()
		calendar.hide_all()
	
	def window_state_event_cb(self, window):
		width, height = self.get_size()
		
		if bookmarks.get_property("visible"):
			width = width / 5
		else:
			width = width / 4
		
		bookmarks.bookmarks.view.reload_name_cell_size(width)


if __name__ == "__main__":
	
	journal = Journal()
	# Load data
	timeline.ready()

	try:
		gtk.main()
	except KeyboardInterrupt:
		sys.exit(0)
