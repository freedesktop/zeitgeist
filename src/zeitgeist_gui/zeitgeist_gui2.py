import datetime
import math
import sys
import os
import gc
import gtk
import gtk.glade
import gobject
import gnomeapplet

from zeitgeist_panel_widgets2 import filtersBox,calendar,timeline,tb,bb,bookmarks,SearchToolItem
from zeitgeist_engine.zeitgeist_util import icon_factory, icon_theme, launcher

class UI:
   
	def __init__(self):
	        self.active_tab=0
		self.create_gui()
	
        
	def create_gui(self):
		
		'''
		Create main window and everything inside it
		'''
		
		# Window
		self.topicWindow = gtk.Window()
		self.topicWindow.set_title("Gnome Zeitgeist")
		self.topicWindow.set_resizable(True)
        	self.topicWindow.set_default_size(-1,-1)
		self.topicWindow.connect("destroy", gtk.main_quit)
		
	        #self.topicWindow.set_icon_from_file("Hourglass.png")
                #gtk.window_set_default_icon_from_file("Hourglass.png")
		# Vertical box (contains self.hBox and a status bar)
		self.vBox = gtk.VBox()
	        tagbox = gtk.HBox()
            
        	#tagbox.pack_start(tb,True,True)
                self.vBox.pack_start(bb,False,False)


		self.topicWindow.add(self.vBox)
		
		# Horizontal box (contains the main content and a sidebar)
		self.hBox = gtk.HBox()
		self.vBox.pack_start(self.hBox, True, True,5)
		
		# Sidebar
		self.sidebar = gtk.VBox()
            
	   	#self.hBox.pack_start(bookmarks, False, False,5)
		
		# Filter/options box
		#self.sidebar.pack_start(filtersBox, True, True)
		
		# Notebook
        
		self.notebook = gtk.Notebook()
	        self.notebook.append_page(bookmarks, gtk.Label("Bookmarks"))
	        self.notebook.append_page(filtersBox,gtk.Label("Filters"))
         	self.notebook.append_page(tb,gtk.Label("Tags"))
        
	        
	        self.sidebar.pack_start(gtk.Label("    "))
        	self.sidebar.pack_start(SearchToolItem())
        	self.sidebar.pack_start(gtk.Label("    "))
	        self.sidebar.pack_start(self.notebook, True, True)
        
	        evbox = gtk.EventBox()
		evbox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("darkgrey"))
		
		evbox.add(timeline)
		
	        #vbox for timeline and tagbar
	        vbox = gtk.VBox()
	        vbox.pack_start(evbox)
	        vbox.pack_start(tagbox,False,False)
        
	        self.hBox.pack_start(self.sidebar, False, False,5)
		self.hBox.pack_start(vbox, True, True,5)
                #self.hBox.pack_start(ctb, True, True,5)
		
		# Timeline view
		#self.notebook.append_page(related, gtk.Label("Related"))
		#self.notebook.append_page(timeline,gtk.Label("Timeline"))
		#self.notebook.set_current_page(-1)
		
        
	        # Status bar
                statusbar = gtk.Statusbar()
                self.vBox.pack_start(statusbar, False, False)
        
		# Show everything
		self.topicWindow.show_all()
                self.sidebar.hide_all()
                #bookmarks.hide_all()
               # tb.hide_all()
        	bb.options.connect("toggled",self.toggle_filters)
        
        def toggle_filters(self,x=None):
     	    if bb.options.get_active():
		self.sidebar.show_all()
                filtersBox.set_buttons()
                self.notebook.set_current_page( self.active_tab)
            else:
                self.active_tab = self.notebook.get_current_page()
                self.sidebar.hide_all()
