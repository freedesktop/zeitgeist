#!/usr/bin/env python

import sys

import gtk

# uncomment the following line to use the new calendar gui
#from zeitgeist_gui.zeitgeist_calendar_gui import zeitgeistGUI

# comment out the following line if you're using the new calendar gui
from zeitgeist_gui.zeitgeist_gui import zeitgeistGUI

 
if __name__ == "__main__":
    gui=zeitgeistGUI()
    gtk.main()
