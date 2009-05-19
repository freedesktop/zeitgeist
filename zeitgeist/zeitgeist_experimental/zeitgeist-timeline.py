#! /usr/bin/env python
# -.- encoding: utf-8 -.-

import sys
import os
import signal
import gtk
import gobject
import gettext

from zeitgeist import config

gettext.install('gnome-zeitgeist', config.localedir, unicode=1)

from zeitgeist_timeline_widgets import CairoTimeline

class App(gtk.Window):
	
	def __init__(self):
		
		gtk.Window.__init__(self)
		
		# Window
		self.set_title(_("GNOME Zeitgeist Timeline"))
		self.set_resizable(True)
		self.resize(700, 300)
		self.connect("destroy", gtk.main_quit)
		signal.signal(signal.SIGUSR1, lambda *discard: self.emit(gtk.main_quit))
		self.set_icon_from_file("%s/gnome-zeitgeist.png" % zeitgeist.pkgdatadir)
		
		self.timeline = CairoTimeline()
		self.add(self.timeline)
		self.show_all()


if __name__ == "__main__":
	
	app = App()

	try:
		gtk.main()
	except KeyboardInterrupt:
		sys.exit(0)
