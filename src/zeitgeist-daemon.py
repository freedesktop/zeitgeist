import dbus
import dbus.service
import dbus.mainloop.glib
import gobject
from gettext import ngettext, gettext as _

from zeitgeist_engine.zeitgeist_datasink import datasink

class RemoteInterface(dbus.service.Object):
	
	@dbus.service.method("org.gnome.zeitgeist",
						in_signature='', out_signature='a(ss)')
	def get_bookmarks(self):
		items = []
		for item in datasink.get_bookmarks():
			items.append((item.get_name(), item.get_uri()))
		return items
	
	@dbus.service.method("org.gnome.zeitgeist",
						in_signature='iii', out_signature='as')
	def get_most_used_tags(self, amount, min_timestamp, max_timestamp):
		return list(datasink.get_most_used_tags(amount,
			min_timestamp, max_timestamp))

	@dbus.service.method("org.gnome.zeitgeist",
						in_signature='iii', out_signature='as')
	def get_recent_used_tags(self, amount, min_timestamp, max_timestamp):
		return list(datasink.get_recent_used_tags(amount,
			min_timestamp, max_timestamp))


if __name__ == "__main__":
	
	dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
	session_bus = dbus.SessionBus()
	name = dbus.service.BusName("org.gnome.zeitgeist", session_bus)
	object = RemoteInterface(session_bus, '/RemoteInterface')
	
	mainloop = gobject.MainLoop()
	print _("Running Zeitgeist service.")
	mainloop.run()
