# -.- encoding: utf-8 -.-

import dbus
import dbus.service

from zeitgeist_engine.zeitgeist_datasink import datasink
from zeitgeist_shared.zeitgeist_shared import *

class RemoteInterface(dbus.service.Object):
	
	# Initialization
	
	def __init__(self, start_dbus=True, mainloop=None):
		if start_dbus:
			bus_name = dbus.service.BusName("org.gnome.Zeitgeist", dbus.SessionBus())
			dbus.service.Object.__init__(self, bus_name, "/org/gnome/zeitgeist")
		self._mainloop = mainloop
	
	# Reading stuff
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="iis", out_signature="a"+sig_plain_data)
	def get_items(self, min_timestamp, max_timestamp, tags):
		return datasink.get_items(min_timestamp, max_timestamp, tags)
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="s", out_signature="a"+sig_plain_data)
	def get_items_for_tag(self, tag):
		return datasink.get_items_for_tag(tag)
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="siis", out_signature="a"+sig_plain_data)
	def get_items_with_mimetype(self, mimetype, min_timestamp, max_timestamp, tags):
		return datasink.get_items_with_mimetype(mimetype, min_timestamp, max_timestamp, tags)
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="", out_signature="a"+sig_plain_data)
	def get_bookmarks(self):
		return datasink.get_bookmarks()
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="iii", out_signature="as")
	def get_most_used_tags(self, amount, min_timestamp, max_timestamp):
		return [str(x) for x in datasink.get_recent_used_tags(amount, min_timestamp, max_timestamp)]
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="iii", out_signature="as")
	def get_recent_used_tags(self, amount, min_timestamp, max_timestamp):
		return [str(x) for x in datasink.get_recent_used_tags(amount, min_timestamp, max_timestamp)]
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="s", out_signature="a"+sig_plain_data)
	def get_related_items(self, item_uri):
		return datasink.get_related_items(item_uri)
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="s", out_signature="a"+sig_plain_data)
	def get_items_related_by_tags(self, item_uri):
		items = []
		for item in datasink.get_items_related_by_tags(item_uri):
			items.append(item)
		return items
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="", out_signature="a"+sig_plain_dataprovider)
	def get_sources_list(self):
		return datasink.get_sources_list()
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="s", out_signature="(uu)")
	def get_timestamps_for_tag(self, tag):
		return datasink.get_timestamps_for_tag(tag)
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="", out_signature="a"+sig_plain_data)
	def get_bookmarks(self):
		return datasink.get_bookmarks()
	
	# Writing stuff
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature=sig_plain_data, out_signature="")
	def insert_item(self, item_list):
		datasink.insert_item(dictify_data(item_list))
		self.emit_signal_updated()
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature=sig_plain_data, out_signature="")
	def update_item(self, item_list):
		datasink.update_item(dictify_data(item_list))
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="s", out_signature="")
	def delete_item(self, item_uri):
		datasink.delete_item(item_uri)
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="ss", out_signature="")
	def register_source(self, name, icon_string):
		datasink.register_source(name, icon_string)
	
	# Signals and signal emitters
	
	@dbus.service.signal("org.gnome.Zeitgeist")
	def signal_updated(self):
		# We forward the "reload" signal, but only if something changed.
		print "Emitted \"updated\" signal." # pass
	
	@dbus.service.method("org.gnome.Zeitgeist")
	def emit_signal_updated(self):
		self.signal_updated()
	
	# Commands
	@dbus.service.method("org.gnome.Zeitgeist")
	def quit(self):
		if self._mainloop:
			self._mainloop.quit()
