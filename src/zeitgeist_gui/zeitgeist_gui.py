import datetime
import math
import sys
import os
import gc
import gtk
import gtk.glade
import gobject
import gnomeapplet

from zeitgeist_panel_widgets import filtersBox,calendar,timeline,related
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
		self.topicWindow.add(self.vBox)
		
		# Horizontal box (contains the main content and a sidebar)
		self.hBox = gtk.HBox()
		self.vBox.pack_start(self.hBox, True, True,5)
		
		# Sidebar
		self.sidebar = gtk.VBox()
		self.sidebar.pack_start(calendar, False, False)
		self.hBox.pack_start(self.sidebar, False, False,5)
		
		# Filter/options box
		self.sidebar.pack_start(filtersBox, True, True)
		
		# Notebook
		self.notebook = gtk.Notebook()
		self.hBox.pack_start(self.notebook, True, True, 5)
	        self.hBox.pack_start(related,True,True,5)
		
		# Timeline view
		self.notebook.append_page(timeline, gtk.Label("Timeline"))
		
		
		# Status bar
		statusbar = gtk.Statusbar()
		self.vBox.pack_start(statusbar, False, False)
		
		# Show everything
		self.topicWindow.show_all()
