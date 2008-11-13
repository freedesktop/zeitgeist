#!/usr/bin/env python
from mayanna_panel_widgets import TimelineWidget,StarredWidget,FilterAndOptionBox
from mayanna_engine.mayanna_util import icon_factory, icon_theme, launcher
import sys
import os
import gnomeapplet

import datetime
import math
try:
     import pygtk
     pygtk.require("2.0")
except:
      pass
try:
    import gtk
    import gtk.glade
except:
    sys.exit(1)
import gobject

class MayannaGUI:   
    
    '''   Initilization   '''
   
    def __init__(self):
        
        #self.main_btn =  gtk.Button("Start")
        self.create_gui()
        
    def create_gui(self):
        
        '''
        Main Window holding everything inside it
        '''
        
        self.topicWindow = gtk.Window()
        self.topicWindow.set_title("Timeline")
        self.topicWindow.set_resizable(True)
        self.topicWindow.set_border_width(5)
        self.topicWindow.show_all()
        if (self.topicWindow):
            self.topicWindow.connect("destroy", gtk.main_quit)

        self.mainbox=gtk.VBox()
        self.mainTable = gtk.HBox()    
        
        ''' 
        HeaderTable
        
        '''
        
        self.timeline = TimelineWidget()
        self.starredbox=StarredWidget()
        self.notebook = gtk.Notebook()
        self.faobox= FilterAndOptionBox()
        
        self.notebook.append_page(self.starredbox,gtk.Label("Starred"))
        self.notebook.append_page(self.timeline,gtk.Label("Timeline"))
        
        self.mainTable.pack_start(self.notebook,True,True,5)
        self.mainTable.pack_start(self.faobox,False,False,5)
    
        self.mainbox.pack_start(self.mainTable,True,True,5)
        
        statusbar = gtk.Statusbar()
        self.mainbox.pack_start(statusbar,False,False)
        
        
        self.topicWindow.add(self.mainbox)
        
        self.topicWindow.show_all()
        
    