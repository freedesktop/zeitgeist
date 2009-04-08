#!/usr/bin/env python

import sys
import gtk

if __name__ == "__main__":
	
	if '--light' in sys.argv:
		from zeitgeist_gui.zeitgeist_gui2 import UI
	else:
		from zeitgeist_gui.zeitgeist_gui import UI
	
	gui = UI()
	gtk.main()
