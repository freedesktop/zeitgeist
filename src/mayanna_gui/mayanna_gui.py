import datetime
import math
import os
import sys

import gnomeapplet
import gobject
import gtk
import gtk.glade

from mayanna_gui_helpers import DockWindow
from mayanna_panel_widgets import MayannaWidget
from mayanna_engine.mayanna_util import bookmarks, icon_factory, icon_theme, launcher

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
        self.topicWindow.connect("destroy", gtk.main_quit)

        self.mainTable = gtk.HBox()
        self.topicWindow.add(self.mainTable)
        
        ''' 
        HeaderTable
        
        '''
        
        self.mayannapanel = MayannaWidget()
        self.mainTable.pack_start(self.mayannapanel, True, True)
        self.topicWindow.show_all()
        
        
