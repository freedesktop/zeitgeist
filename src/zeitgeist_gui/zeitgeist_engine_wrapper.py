from zeitgeist_gui.zeitgeist_dbus import iface, dbus_connect
from zeitgeist_shared.zeitgeist_shared import *


class EngineInterface(object):
	
	def get_items(self, *args):
		for item in iface.get_items(*args):
			yield objectify_data(item)
	
	def get_related_items(self, *args):
		for related_item in iface.get_related_items(*args):
			yield objectify_data(related_item)
	
	def get_most_used_tags(self, *args):
		for tag in iface.get_most_used_tags(*args):
			yield tag
	
	def get_recent_used_tags(self, *args):
		for tag in iface.get_recent_used_tags(*args):
			yield tag
	
	def get_timestamps_for_tag(self, *args):
		return iface.get_timestamps_for_tag(*args)
	
	def get_bookmarks(self, *args):
		for item in iface.get_bookmarks(*args):
			yield objectify_data(item)
	
	def get_sources_list(self, *args):
		return iface.get_sources_list()
	
	def emit_signal_updated(self, *args):
		return iface.emit_signal_updated(*args)
	
	def update_item(self, item):
		return iface.update_item(plainify_data(item))
	
	def delete_item(self, *args):
		return iface.delete_item(*args)
	
	def connect(self, *args):
		return dbus_connect(*args)

engine = EngineInterface()
