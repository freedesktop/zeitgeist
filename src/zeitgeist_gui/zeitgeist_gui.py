import datetime
import math
import sys
import os

import gtk
import gtk.glade
import gobject
import gnomeapplet

from zeitgeist_panel_widgets import timeline,StarredWidget,FilterAndOptionBox,calendar
from zeitgeist_engine.zeitgeist_util import icon_factory, icon_theme, launcher

class zeitgeistGUI:
   
	def __init__(self):
		self.create_gui()
		
	def create_gui(self):
		
		'''
		Main Window holding everything inside it
		'''
		
		self.topicWindow = gtk.Window()
		self.topicWindow.set_title("Gnome Zeitgeist")
		self.topicWindow.set_resizable(True)
		self.topicWindow.set_border_width(5)
		self.topicWindow.connect("destroy", gtk.main_quit)

		self.mainbox = gtk.VBox()
		self.mainTable = gtk.HBox()    
		self.sidebar = gtk.VBox()
		
		''' 
		HeaderTable
		'''
		
		self.starredbox = StarredWidget()
		self.notebook = gtk.Notebook()
		self.faobox = FilterAndOptionBox()
		
		
		self.sidebar.pack_start(calendar, False, False)
		self.sidebar.pack_start(self.faobox, True, True)
		
		
		self.notebook.append_page(self.starredbox, gtk.Label("Starred"))
		self.notebook.append_page(timeline, gtk.Label("Timeline"))
		
		self.mainTable.pack_start(self.sidebar, False, False,5)
		self.mainTable.pack_start(self.notebook, True, True,5)
	
		self.mainbox.pack_start(self.mainTable, True, True,5)
		
		statusbar = gtk.Statusbar()
		self.mainbox.pack_start(statusbar, False, False)
		
		
		self.topicWindow.add(self.mainbox)
		self.topicWindow.show_all()