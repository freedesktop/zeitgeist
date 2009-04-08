import dbus
import dbus.service
import dbus.mainloop.glib
import gobject
from gettext import ngettext, gettext as _

from zeitgeist_engine.zeitgeist_datasink import datasink

class DBusInterface(dbus.service.Object):
	
	@dbus.service.method("org.gnome.zeitgeist",
						in_signature='', out_signature='a(ss)')
	def get_bookmarks(self):
		items = []
		for item in datasink.get_bookmarks():
			items.append((item.get_name(), item.get_uri()))
		return items

if __name__ == "__main__":
	
	dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
	session_bus = dbus.SessionBus()
	name = dbus.service.BusName("org.gnome.zeitgeist", session_bus)
	object = DBusInterface(session_bus, '/DBusInterface')
	
	mainloop = gobject.MainLoop()
	print _("Running Zeitgeist service.")
	mainloop.run()
