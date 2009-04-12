#!/bin/sh

if [ "$1" != "--new" ]; then
	python -c """
import sys, gtk, os
sys.path.append('src/')
from zeitgeist_gui.zeitgeist_gui_old import UI
gui = UI()
try:
	gtk.main()
except KeyboardInterrupt:
	sys.exit(0)
		"""
else
	python src/zeitgeist_gui/zeitgeist_gui.py $@
fi
