import sys
import os
import gtk
import gobject
from gettext import ngettext, gettext as _ 

# Transitional until we got ride of imports from the backend
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), "../")))

from zeitgeist_panel_widgets import vtb, bb, bookmarks, projectview

class ProjectViewer(gtk.Window):
	
	def __init__(self):
		gtk.Window.__init__(self)
		# Window
		self.set_title("GNOME Zeitgeist Project Viewer")
		self.set_resizable(True)
		self.set_default_size(300, 600)
		self.connect("destroy", gtk.main_quit)
		self.set_icon_from_file("data/gnome-zeitgeist.png")
		#gtk.window_set_default_icon_from_file("Hourglass.png")
		# Vertical box (contains self.hBox and a status bar)
		self.vbox = gtk.VBox()
		self.vbox.pack_start(vtb,False,False,5)
		self.vbox.pack_start(projectview,True,True,5)
		self.set_border_width(5)
		self.add(self.vbox)
		self.show_all()
		


if __name__ == "__main__":
	
	pv = ProjectViewer()

	try:
		gtk.main()
	except KeyboardInterrupt:
		sys.exit(0)
