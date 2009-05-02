#! /usr/bin/env python
# -.- encoding: utf-8 -.-

import sys
import os
import signal
import gtk
import gobject
import gettext

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../"))
gettext.install('gnome-zeitgeist', '/usr/share/locale', unicode=1)

from zeitgeist_journal_widgets import projectview, VTagBrowser
from zeitgeist_shared.basics import BASEDIR

class ProjectViewer(gtk.Window):
	
	def __init__(self):
		
		gtk.Window.__init__(self)
		
		# Window
		self.set_title(_("GNOME Zeitgeist Project Viewer"))
		self.set_resizable(True)
		self.set_default_size(300, 600)
		self.connect("destroy", gtk.main_quit)
		signal.signal(signal.SIGUSR1, lambda *discard: self.emit(gtk.main_quit))
		self.set_icon_from_file("%s/data/gnome-zeitgeist.png" % BASEDIR)
		
		vtb = VTagBrowser()
		
		# Vertical box (contains self.hBox and a status bar)
		self.vbox = gtk.VBox()
		self.vbox.pack_start(vtb, False, False, 5)
		self.vbox.pack_start(projectview, True, True, 5)
		self.set_border_width(5)
		self.add(self.vbox)
		self.show_all()


if __name__ == "__main__":
	
	pv = ProjectViewer()

	try:
		gtk.main()
	except KeyboardInterrupt:
		sys.exit(0)
