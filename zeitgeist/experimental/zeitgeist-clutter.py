#!/usr/bin/env python

import clutter
import time
import datetime
import math
import sys
import os
import gtk
from gtk_clutter import *
 
class Item():
    
    def __init__(self):
        pass

class UI():
    
    def __init__(self):
        
        '''
        Setting up the stage
        '''
        self.stage = clutter.stage_get_default() 
        self.stage.set_size(800,480)
        self.stage.set_color(clutter.color_parse("#00000000"))
        self.stage.show()    
        
        '''
        Setting up stage timeline widgets
        '''
        
        self.timeline = clutter.Rectangle ()
        self.timeline.set_opacity(100)
        self.timeline.set_size(800,1)
        self.timeline.set_position(0,240)
        self.stage.add(self.timeline)
        
        '''
        Setting up stage background widgets
        '''
        self.daylines = []
        self.set_days()
        
        clutter.main()
    
    def get_days(self):
        days = []
        today = time.time()
        for i in xrange(7):
            days.append(today-i*86400)
        return days
    
    def set_days(self, start=0, days=7):
        
        space = 115
        days = self.get_days()
        for day in days:
            dayline = Dayline(day)
            dayline.set_position(50 + space * days.index(day), 0)
            self.daylines.append(dayline)
            self.stage.add(dayline)

if __name__ == "__main__":

    gui = UI()
    gtk.main()
