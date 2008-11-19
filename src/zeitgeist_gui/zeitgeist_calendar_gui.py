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
from zeitgeist_engine.zeitgeist_util import icon_factory, icon_theme, launcher
from zeitgeist_engine.zeitgeist_datasink import DataSinkSource

class zeitgeistGUI:   
    
    '''   Initilization   '''
    
    month_mapping = ["January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July"
        "August",
        "September",
        "October",
        "November",
        "December"]
        
    def __init__(self):
        self.date = time.localtime()
        self.create_gui()
        
    def create_gui(self):
        self.glade = gtk.glade.XML("calendar.glade")
        self.glade.signal_autoconnect(self)
        
        self.monthLabel = self.glade.get_widget("monthLabel")
        self.monthLabel.set_markup("<b>%s %s</b>" % 
            (self.month_mapping[self.date[1]-1], self.date[0]))
        
        self.miniCalendar = self.glade.get_widget("miniCalendar")
        self.miniCalendar.select_month(self.date[1], self.date[0])
        
        self.calendarModel = Calendar.Model()
        self.calendar = Calendar.Calendar(self.calendarModel)
        self.calendar.set_range(Calendar.Calendar.RANGE_WEEK)
        
        vbox = self.glade.get_widget("mainVBox")
        vbox.add(self.calendar)
        calendarWindow = self.glade.get_widget("calendarWindow")
        calendarWindow.connect("destroy", gtk.main_quit)
        calendarWindow.show_all()
        
        datasink = DataSinkSource()
        for data in datasink.get_items():
            start = datetime.datetime.fromtimestamp(data.timestamp)
            end = datetime.datetime.fromtimestamp(data.timestamp+1000)
            ev = Calendar.Event(data.get_name(),start,end)
            self.calendarModel.add_event(ev)
            
        #self.zeitgeistpanel = zeitgeistWidget()
        #self.zeitgeistpanel.show_all()
        #self.mainTable.pack_start(self.zeitgeistpanel,True,True)
        #self.topicWindow.show_all()
    
    def on_mode_button_clicked (self, button):
        '''
        Called when one of the buttons to change
        the calendar's mode has been clicked.
        '''
        if gtk.glade.get_widget_name(button) == "weekButton":
            self.calendar.set_range(Calendar.Calendar.RANGE_WEEK)
        else:
            self.calendar.set_range(Calendar.Calendar.RANGE_MONTH)
