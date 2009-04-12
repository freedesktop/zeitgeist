import dbus
import dbus.service
import dbus.mainloop.glib
import gobject
from gettext import ngettext, gettext as _

from zeitgeist_engine.zeitgeist_datasink import datasink


class RemoteInterface(dbus.service.Object):
	
	def __init__(self):
		bus_name = dbus.service.BusName("org.gnome.zeitgeist", dbus.SessionBus())
		dbus.service.Object.__init__(self, bus_name, "/org/gnome/zeitgeist")
	
	_sig_plaindata = "a(sssssss)"
	def _plainify(self, obj):
		''' Takes a Data object and converts it into an object
			suitable for transmission through D-Bus. '''
		return (str(obj.get_timestamp()), obj.get_uri(),
			obj.get_name(), obj.get_type(), obj.get_mimetype(), 
			obj.get_icon_string() or '', ','.join(obj.get_tags()))
	
	@dbus.service.method("org.gnome.zeitgeist",
						in_signature="iis", out_signature=_sig_plaindata)
	def get_items(self, min_timestamp, max_timestamp, tags):
		items = []
		for item in datasink.get_items(min_timestamp, max_timestamp, tags):
			items.append(self._plainify(item))
		return items
	
	@dbus.service.method("org.gnome.zeitgeist",
						in_signature="siis", out_signature=_sig_plaindata)
	def get_items_with_mimetype(self, mimetype, min_timestamp, max_timestamp, tags):
		items = []
		for item in datasink.get_items_with_mimetype(mimetype, min_timestamp, max_timestamp, tags):
			items.append(self._plainify(item))
		return items
	
	@dbus.service.method("org.gnome.zeitgeist",
						in_signature="", out_signature=_sig_plaindata)
	def get_bookmarks(self):
		items = []
		for item in datasink.get_bookmarks():
			items.append(self._plainify(item))
		return items
	
	@dbus.service.method("org.gnome.zeitgeist",
						in_signature="iii", out_signature="as")
	def get_most_used_tags(self, amount, min_timestamp, max_timestamp):
		return list(datasink.get_most_used_tags(amount,
			min_timestamp, max_timestamp))

	@dbus.service.method("org.gnome.zeitgeist",
						in_signature="iii", out_signature="as")
	def get_recent_used_tags(self, amount, min_timestamp, max_timestamp):
		return list(datasink.get_recent_used_tags(amount,
			min_timestamp, max_timestamp))
	
	@dbus.service.method("org.gnome.zeitgeist",
						in_signature="s", out_signature=_sig_plaindata)
	def get_related_items(self, item_uri):
		items = []
		for item in datasink.get_related_items(item_uri):
			items.append(self._plainify(item))
		return items
	
	@dbus.service.method("org.gnome.zeitgeist",
						in_signature="s", out_signature=_sig_plaindata)
	def get_items_related_by_tags(self, item_uri):
		items = []
		for item in datasink.get_items_related_by_tags(item_uri):
			items.append(self._plainify(item))
		return items
	
	@dbus.service.method("org.gnome.zeitgeist",
						in_signature="s", out_signature="")
	def delete_item(self, item_uri):
		datasink.delete_item(item_uri)
	
	@dbus.service.signal("org.gnome.zeitgeist")
	def signal_updated(self):
		# We forward the "reload" signal, but only if something changed.
		print "Emitted \"updated\" signal." # pass
	
	@dbus.service.method("org.gnome.zeitgeist")
	def emit_signal_updated(self):
		self.signal_updated()


if __name__ == "__main__":
	
	dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
	object = RemoteInterface()
	datasink.reload_callbacks.append(object.signal_updated)
	
	mainloop = gobject.MainLoop()
	print _("Running Zeitgeist service.")
	mainloop.run()
