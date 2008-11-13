#!/usr/bin/env python

import sys

import gtk

# uncomment the following line to use the new calendar gui
from mayanna_gui.mayanna_calendar_gui import MayannaGUI

# comment out the following line if you're using the new calendar gui
#from mayanna_gui.mayanna_gui import MayannaGUI

 
if __name__ == "__main__":
    gui=MayannaGUI()
    gtk.main()
