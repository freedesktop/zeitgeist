#!/usr/bin/env python
from mayanna_panel_widgets import MayannaWidget
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
        self.topicWindow.set_border_width(1)
        self.topicWindow.show_all()
        if (self.topicWindow):
            self.topicWindow.connect("destroy", gtk.main_quit)

        self.mainTable = gtk.HBox()    
        
        ''' 
        HeaderTable
        
        '''
        ev_box = gtk.EventBox()
        ev_box.modify_bg(gtk.STATE_NORMAL,None)
        #ev_box.set_border_width(2)
        ev_box.add(self.mainTable)
        self.topicWindow.add(ev_box)
        
        self.mayannapanel = MayannaWidget()
        self.mayannapanel.show_all()
        self.mainTable.pack_start(self.mayannapanel,True,True)
        self.topicWindow.show_all()
        
        
