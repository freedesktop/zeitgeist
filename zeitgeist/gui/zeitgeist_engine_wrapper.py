# -.- encoding: utf-8 -.-

import time

from zeitgeist.gui.zeitgeist_base import Data
from zeitgeist.shared.zeitgeist_shared import plainify_data, dictify_data
from zeitgeist.gui.zeitgeist_base import objectify_data
from zeitgeist.shared.zeitgeist_dbus import iface, dbus_connect

class EngineInterface:
	
	def __init__(self, interface):
		self._interface = interface
	
	def _data_to_engine(self, data):
		return plainify_data(data)
	
	def _data_from_engine(self, data):
		return objectify_data(data)
	
	def connect(self, *args):
		return dbus_connect(*args)
	
	def get_items(self, *args):
		func = self._data_from_engine
		return (func(item) for item in self._interface.get_items(*args))
	
	def get_items_for_tag(self, *args):
		func = self._data_from_engine		
		return (func(item) for item in self._interface.get_items_for_tag(*args))

	def get_related_items(self, *args):
		for related_item in self._interface.get_related_items(*args):
			yield self._data_from_engine(related_item)
	
	def get_all_tags(self, *args):
		return self._interface.get_all_tags(*args)
	
	def get_most_used_tags(self, *args):
		return self._interface.get_most_used_tags(*args)
	
	def get_recent_used_tags(self, *args):
		return self._interface.get_recent_used_tags(*args)
	
	def get_timestamps_for_tag(self, *args):
		return self._interface.get_timestamps_for_tag(*args)
	
	def get_types(self, *args):
		return self._interface.get_types(*args)
	
	def get_bookmarks(self, *args):
		items = []
		for item in self._interface.get_bookmarks(*args):
			items.append(self._data_from_engine(item))
		return items
	
	def update_item(self, item):
		return self._interface.update_item(self._data_to_engine(item))
	
	def delete_item(self, *args):
		return self._interface.delete_item(*args)
	
	def emit_signal_updated(self, *args):
		return self._interface.emit_signal_updated(*args)
	
	def quit(self):
		'''
		Stops the daemon. Use carefully!
		'''
		return self._interface.quit()

engine = EngineInterface(iface)
