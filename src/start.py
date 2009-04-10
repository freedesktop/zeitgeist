#!/usr/bin/env python

import sys
import gtk

if __name__ == "__main__":
	
	if '--old' in sys.argv:
		from zeitgeist_gui.zeitgeist_gui_old import UI
	else:
		from zeitgeist_gui.zeitgeist_gui import UI
	
	gui = UI()
	
	try:
		gtk.main()
	except KeyboardInterrupt:
		sys.exit(0)
