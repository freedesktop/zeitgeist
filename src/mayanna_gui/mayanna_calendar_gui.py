import datetime
import math
import os
import sys
import time

sys.path.append("libs/")
from SpiffGtkWidgets import Calendar
import gnomeapplet
import gobject
import gtk
import gtk.glade
    
from mayanna_panel_widgets import MayannaWidget
from mayanna_engine.mayanna_util import icon_factory, icon_theme, launcher


class MayannaGUI:   
    
    '''   Initilization   '''
   
    def __init__(self):
        self.date = time.localtime()
        self.create_gui()
        
    def create_gui(self):
        self.glade = gtk.glade.XML("calendar.glade")
        self.glade.signal_autoconnect(self)
        
        self.calendarModel = Calendar.Model()
        self.calendar = Calendar.Calendar(self.calendarModel)
        self.calendar.set_range(Calendar.Calendar.RANGE_WEEK)
        
        vbox = self.glade.get_widget("mainVBox")
        vbox.add(self.calendar)
        
        calendarWindow = self.glade.get_widget("calendarWindow")
        calendarWindow.connect("destroy", gtk.main_quit)
        calendarWindow.show_all()
    
    def on_mode_button_clicked (self, button):
        '''
        Called when one of the buttons to change
        the calendar's mode has been clicked.
        '''
        if gtk.glade.get_widget_name(button) == "weekButton":
            self.calendar.set_range(Calendar.Calendar.RANGE_WEEK)
        else:
            self.calendar.set_range(Calendar.Calendar.RANGE_MONTH)
