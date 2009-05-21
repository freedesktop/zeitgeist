# -.- encoding: utf-8 -.-

import dbus
import dbus.service

from zeitgeist.engine.engine import engine
from zeitgeist.shared.zeitgeist_shared import *

class RemoteInterface(dbus.service.Object):
	
	# Initialization
	
	def __init__(self, start_dbus=True, mainloop=None):
		bus_name = dbus.service.BusName("org.gnome.Zeitgeist", dbus.SessionBus())
		dbus.service.Object.__init__(self, bus_name, "/org/gnome/zeitgeist")
		self._mainloop = mainloop
	
	# Reading stuff
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="iis", out_signature="a"+sig_plain_data)
	def get_items(self, min_timestamp, max_timestamp, tags):
		return engine.get_items(min_timestamp, max_timestamp, tags)
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="s", out_signature="a"+sig_plain_data)
	def get_items_for_tag(self, tag):
		return engine.get_items_for_tag(tag)
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="siis", out_signature="a"+sig_plain_data)
	def get_items_with_mimetype(self, mimetype, min_timestamp, max_timestamp, tags):
		return engine.get_items_with_mimetype(mimetype, min_timestamp, max_timestamp, tags)
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="", out_signature="a"+sig_plain_data)
	def get_bookmarks(self):
		return engine.get_bookmarks()
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="", out_signature="as")
	def get_all_tags(self):
		return engine.get_all_tags()
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="iii", out_signature="as")
	def get_most_used_tags(self, amount, min_timestamp, max_timestamp):
		return engine.get_recently_used_tags(amount, min_timestamp, max_timestamp)
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="iii", out_signature="as")
	def get_recent_used_tags(self, amount, min_timestamp, max_timestamp):
		return engine.get_recently_used_tags(amount, min_timestamp, max_timestamp)
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="s", out_signature="a"+sig_plain_data)
	def get_related_items(self, item_uri):
		return engine.get_related_items(item_uri)
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="s", out_signature="a"+sig_plain_data)
	def get_items_related_by_tags(self, item_uri):
		items = []
		for item in engine.get_items_related_by_tags(item_uri):
			items.append(item)
		return items
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="s", out_signature="(uu)")
	def get_timestamps_for_tag(self, tag):
		return engine.get_timestamps_for_tag(tag)
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="", out_signature="a(ss)")
	def get_types(self):
		return engine.get_types()
	
	# Writing stuff
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature=sig_plain_data, out_signature="b")
	def insert_item(self, item_list):
		result = engine.insert_item(dictify_data(item_list))
		if result:
			self.emit_signal_updated()
		return result
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="a"+sig_plain_data, out_signature="")
	def insert_items(self, items_list):
		if engine.insert_items([dictify_data(x) for x in items_list]):
			self.emit_signal_updated()
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature=sig_plain_data, out_signature="")
	def update_item(self, item_list):
		engine.update_item(dictify_data(item_list))
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="s", out_signature="")
	def delete_item(self, item_uri):
		engine.delete_item(item_uri)
	
	# Signals and signal emitters
	
	@dbus.service.signal("org.gnome.Zeitgeist")
	def signal_updated(self):
		pass
	
	@dbus.service.signal("org.gnome.Zeitgeist")
	def signal_exit(self):
		pass
	
	@dbus.service.method("org.gnome.Zeitgeist")
	def emit_signal_updated(self):
		self.signal_updated()
	
	# Commands
	
	@dbus.service.method("org.gnome.Zeitgeist")
	def quit(self):
		if self._mainloop:
			self._mainloop.quit()
