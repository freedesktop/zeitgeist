import datetime
import math
import os
import sys
import time

sys.path.append("libs/")
from SpiffGtkWidgets import Calendar
#from SpiffGtkWidgets import Event
import gnomeapplet
import gobject
import gtk
import gtk.glade
import datetime
from mayanna_panel_widgets import MayannaWidget
from mayanna_engine.mayanna_util import icon_factory, icon_theme, launcher
from mayanna_engine.mayanna_datasink import DataSinkSource

class MayannaGUI:   
    
    '''   Initilization   '''
   
    def __init__(self):
        self.date = time.localtime()
        self.create_gui()
        
    def create_gui(self):
        '''
        Main Window holding everything inside it
        '''
        self.topicWindow = gtk.Window()
        self.topicWindow.set_title("Timeline")
        self.topicWindow.resize(700, 500)
        self.topicWindow.set_resizable(True)
        self.topicWindow.set_border_width(1)
        self.topicWindow.show_all()
        if (self.topicWindow):
            self.topicWindow.connect("destroy", gtk.main_quit)
        
        '''
        Paned view containing a sidebar and the calendar
        '''
        paned = gtk.HPaned()
        self.topicWindow.add(paned)
        
        '''
        Sidebar
        '''
        vbox = gtk.VBox()
        paned.add1(vbox)
        
        self.miniCalendar = gtk.Calendar()
        self.miniCalendar.select_month(self.date[1], self.date[0])
        self.miniCalendar.set_display_options(gtk.CALENDAR_SHOW_HEADING)
        vbox.add(self.miniCalendar)
        
        '''Main View'''
        vbox = gtk.VBox(False)
        paned.add2(vbox)
        
        buttonBox = gtk.HButtonBox()
        vbox.pack_start(buttonBox, False)
        
        for buttonText in ["Week", "Month"]:
            button = gtk.Button(buttonText)
            button.connect("clicked",
                self.on_mode_button_clicked, buttonText)
            buttonBox.add(button)
            
        self.calendarModel = Calendar.Model()
        self.calendar = Calendar.Calendar(self.calendarModel)
        self.calendar.set_range(Calendar.Calendar.RANGE_WEEK)
        vbox.add(self.calendar)
        
        datasink = DataSinkSource()
        for data in datasink.get_items():
            start = datetime.datetime.fromtimestamp(data.timestamp)
            end = datetime.datetime.fromtimestamp(data.timestamp+1000)
            ev = Calendar.Event(data.get_name(),start,end)
            self.calendarModel.add_event(ev)
            
        #self.mayannapanel = MayannaWidget()
        #self.mayannapanel.show_all()
        #self.mainTable.pack_start(self.mayannapanel,True,True)
        self.topicWindow.show_all()
    
    def on_mode_button_clicked (self, button, buttonLabel):
        '''
        Called when one of the buttons to change
        the calendar's mode has been clicked.
        '''
        if buttonLabel == "Week":
            self.calendar.set_range(Calendar.Calendar.RANGE_WEEK)
        else:
            self.calendar.set_range(Calendar.Calendar.RANGE_MONTH)
