import dbus
import dbus.service
import dbus.mainloop.glib
import gobject
from gettext import ngettext, gettext as _
import gtk
import subprocess

from zeitgeist_engine.zeitgeist_datasink import datasink
from zeitgeist_shared.zeitgeist_shared import *
from zeitgeist_engine.zeitgeist_util import ZeitgeistTrayIcon

class RemoteInterface(dbus.service.Object):
	
	# Initialization
	
	def __init__(self):
		bus_name = dbus.service.BusName("org.gnome.Zeitgeist", dbus.SessionBus())
		dbus.service.Object.__init__(self, bus_name, "/org/gnome/zeitgeist")
	
	# Reading stuff
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="iis", out_signature="a"+sig_plain_data)
	def get_items(self, min_timestamp, max_timestamp, tags):
		items = []
		for item in datasink.get_items(min_timestamp, max_timestamp, tags):
			items.append(plainify_data(item))
		return items
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="siis", out_signature="a"+sig_plain_data)
	def get_items_with_mimetype(self, mimetype, min_timestamp, max_timestamp, tags):
		items = []
		for item in datasink.get_items_with_mimetype(mimetype, min_timestamp, max_timestamp, tags):
			items.append(plainify_data(item))
		return items
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="", out_signature="a"+sig_plain_data)
	def get_bookmarks(self):
		items = []
		for item in datasink.get_bookmarks():
			items.append(plainify_data(item))
		return items
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="iii", out_signature="as")
	def get_most_used_tags(self, amount, min_timestamp, max_timestamp):
		return list(datasink.get_most_used_tags(amount,
			min_timestamp, max_timestamp))

	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="iii", out_signature="as")
	def get_recent_used_tags(self, amount, min_timestamp, max_timestamp):
		return list(datasink.get_recent_used_tags(amount,
			min_timestamp, max_timestamp))
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="s", out_signature="a"+sig_plain_data)
	def get_related_items(self, item_uri):
		items = []
		for item in datasink.get_related_items(item_uri):
			items.append(plainify_data(item))
		return items
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="s", out_signature="a"+sig_plain_data)
	def get_items_related_by_tags(self, item_uri):
		items = []
		for item in datasink.get_items_related_by_tags(item_uri):
			items.append(plainify_data(item))
		return items
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="", out_signature="a"+sig_plain_dataprovider)
	def get_sources_list(self):
		sources = []
		for source in datasink.get_sources():
			sources.append(plainify_dataprovider(source))
		return sources
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="s", out_signature="(uu)")
	def get_timestamps_for_tag(self, tag):
		return datasink.get_timestamps_for_tag(tag)
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="", out_signature="a"+sig_plain_data)
	def get_bookmarks(self):
		bookmarks = []
		for bookmark in datasink.get_bookmarks():
			bookmarks.append(plainify_data(bookmark))
		return bookmarks
	
	# Writing stuff
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature=sig_plain_data, out_signature="")
	def insert_item(self, item_list):
		datasink.insert_item(dictify_data(item_list))
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature=sig_plain_data, out_signature="")
	def update_item(self, item_list):
		datasink.update_item(dictify_data(item_list))
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="s", out_signature="")
	def delete_item(self, item_uri):
		datasink.delete_item(item_uri)
	
	# Signals and signal emitters
	
	@dbus.service.signal("org.gnome.Zeitgeist")
	def signal_updated(self):
		# We forward the "reload" signal, but only if something changed.
		print "Emitted \"updated\" signal." # pass
	
	@dbus.service.method("org.gnome.Zeitgeist")
	def emit_signal_updated(self):
		self.signal_updated()

class ZeitgeistTrayIcon(gtk.StatusIcon):
	
	def __init__(self):
		gtk.StatusIcon.__init__(self)
		self.set_from_file("data/gnome-zeitgeist.png")
		self.set_visible(True)
		
		menu = gtk.Menu()
		
		self.journal_proc = None
		
		menuItem = gtk.ImageMenuItem(gtk.STOCK_HOME)
		menuItem.set_name("Open Journal")
		menu.append(menuItem)
		menuItem.connect('activate', self.open_journal)
		
		menuItem = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
		menu.append(menuItem)
		menuItem.connect('activate', self.open_about)
		
		menuItem = gtk.ImageMenuItem(gtk.STOCK_QUIT)
		menu.append(menuItem)
		 
		self.set_tooltip("Zeitgeist")
		self.connect('popup-menu', self.popup_menu_cb, menu)

	def open_journal(self,widget):
		if self.journal_proc == None or not self.journal_proc.poll() == None:
			self.journal_proc = subprocess.Popen("sh zeitgeist.sh",shell=True)
			
	def open_about(self,widget):
		about.visible = False
		about._toggle_()
				
 	def popup_menu_cb(self,widget, button, time, data = None):
 		if button == 3:
 			if data:
 				data.show_all()
                data.popup(None, None, None, 3, time)


class AboutWindow(gtk.Window):
	def __init__(self):
		gtk.Window.__init__(self)
		# Window
		self.set_title("About Gnome Zeitgeist")
		self.set_resizable(False)
		self.set_size_request(400,320)
		self.connect("destroy", self._toggle_)
		self.set_icon_name(gtk.STOCK_ABOUT)
		self.hide_all()
		self.visible = True
		self.label = gtk.Label()
		self.label.set_markup(self._get_about())
		self.add(self.label)
		
	def _toggle_(self,widget=None):
		if self.visible:
			self.hide_all()
			self.visible = False
		else:
			self.show_all()
			self.visible = True
			
	def _get_about(self):
		title = "<span size='large' color='blue'>%s</span>" %"GNOME Zeitgeist"
		comment = "Gnome Zeitgeist is a tool for easily browsing and finding files on your computer"
		copyright = "<span size='small' color='blue'>%s</span>"%"Copyright  2009 GNOME Zeitgeist Developers"
		page="http://zeitgeist.geekyogre.com"
		
		about = title +"\n"+"\n"+comment+"\n"+"\n"+copyright+"\n"+"\n"+page
		return about

if __name__ == "__main__":
	
	dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
	object = RemoteInterface()
	datasink.reload_callbacks.append(object.signal_updated)

	trayicon = ZeitgeistTrayIcon()
	
	mainloop = gobject.MainLoop()
	print _("Running Zeitgeist service.")
	mainloop.run()
