import datetime
import math
import sys
import os
import gc
import gtk
import gtk.glade
import gobject
import gnomeapplet

from zeitgeist_panel_widgets import filtersBox,calendar,timeline,ctb
from zeitgeist_engine.zeitgeist_util import icon_factory, icon_theme, launcher

class zeitgeistGUI:
   
	def __init__(self):
		self.create_gui()
		
	def create_gui(self):
		
		'''
		Create main window and everything inside it
		'''
		
		# Window
		self.topicWindow = gtk.Window()
		self.topicWindow.set_title("Gnome Zeitgeist")
		self.topicWindow.set_resizable(True)
		self.topicWindow.connect("destroy", gtk.main_quit)
		
		# Vertical box (contains self.hBox and a status bar)
		self.vBox = gtk.VBox()
		self.vBox.pack_start(ctb,False,False)

		self.topicWindow.add(self.vBox)
		
		# Horizontal box (contains the main content and a sidebar)
		self.hBox = gtk.HBox()
		self.vBox.pack_start(self.hBox, True, True,5)
		
		# Sidebar
		self.sidebar = gtk.VBox()
		#self.sidebar.pack_start(calendar, False, False)
		self.hBox.pack_start(self.sidebar, False, False,5)
		
		# Filter/options box
		self.sidebar.pack_start(filtersBox, True, True)
		
		# Notebook
		#self.notebook = gtk.Notebook()
		evbox = gtk.EventBox()
		evbox.modify_bg(gtk.STATE_NORMAL, 
		gtk.gdk.color_parse("darkgrey"))
		evbox1 = gtk.EventBox()
		evbox1.set_border_width(1)
		evbox1.add(timeline)
		evbox.add(evbox1)
		
		self.hBox.pack_start(evbox, True, True)
		advancedbar = gtk.VBox()
		#advancedbar.pack_start(related,True,True,5)
		#advancedbar.pack_start(ctb,True,True,5)
		self.hBox.pack_start(advancedbar,False,False,5)
		
		# Timeline view
		#self.notebook.append_page(related, gtk.Label("Related"))
		#self.notebook.append_page(timeline,gtk.Label("Timeline"))
		#self.notebook.set_current_page(-1)
		
		# Status bar
		statusbar = gtk.Statusbar()
		self.vBox.pack_start(statusbar, False, False)
		
		# Show everything
		self.topicWindow.show_all()
