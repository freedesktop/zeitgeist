import sys
import os
import gtk
import gobject
from gettext import ngettext, gettext as _ 

# Transitional until we got ride of imports from the backend
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), "../")))

from zeitgeist_panel_widgets import filtersBox, calendar, timeline, tb, bb, bookmarks
from zeitgeist_engine.zeitgeist_util import icon_factory, icon_theme, launcher

class Journal(gtk.Window):
	
	def __init__(self):
		gtk.Window.__init__(self)
		# Window
		self.set_title("Gnome Zeitgeist")
		self.set_resizable(True)
		self.set_default_size(800, -1)
		self.connect("destroy", gtk.main_quit)
		self.set_icon_from_file("data/gnome-zeitgeist.png")
		#gtk.window_set_default_icon_from_file("Hourglass.png")
		# Vertical box (contains self.hBox and a status bar)
		self.vBox = gtk.VBox()
		tagbox = gtk.HBox()
			
		tagbox.pack_start(tb,True,True)
		self.vBox.pack_start(bb,False,False)

		self.add(self.vBox)
		
		# Horizontal box (contains the main content and a sidebar)
		self.hBox = gtk.HBox()
		self.vBox.pack_start(self.hBox, True, True,5)
		
		# Sidebar
		self.sidebar = gtk.VBox()
			
		self.hBox.pack_start(bookmarks, False, False,5)
		
		# Filter/options box
		self.sidebar.pack_start(filtersBox, True, True)
		
		# Notebook
		#self.notebook = gtk.Notebook()
		evbox = gtk.EventBox()
		evbox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("darkgrey"))
		
		evbox.add(timeline)
		
		#vbox for timeline and tagbar
		vbox = gtk.VBox()
		vbox.pack_start(evbox)
		vbox.pack_start(tagbox,False,False)
		
		self.hBox.pack_start(vbox, True, True,5)
		self.hBox.pack_start(self.sidebar, False, False,5)
		#self.hBox.pack_start(ctb, True, True,5)
		
		# Timeline view
		#self.notebook.append_page(related, gtk.Label("Related"))
		#self.notebook.append_page(timeline,gtk.Label("Timeline"))
		#self.notebook.set_current_page(-1)
		
		# Status bar
		statusbar = gtk.Statusbar()
		self.vBox.pack_start(statusbar, False, False)
		
		# Show everything
		self.show_all()
		self.sidebar.hide_all()
		bookmarks.hide_all()
		tb.hide_all()
		bb.options.connect("toggled",self.toggle_filters)
	
	def toggle_filters(self, x=None):
		if bb.options.get_active():
			self.sidebar.show_all()
			filtersBox.set_buttons()
		else:
			self.sidebar.hide_all()


if __name__ == "__main__":
	
	journal = Journal()

	try:
		gtk.main()
	except KeyboardInterrupt:
		sys.exit(0)
