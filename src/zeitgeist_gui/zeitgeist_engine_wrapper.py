import sys
import time

from zeitgeist_gui.zeitgeist_base import Data
from zeitgeist_shared.zeitgeist_shared import plainify_data, dictify_data
from zeitgeist_gui.zeitgeist_base import objectify_data

class BaseEngineInterface:
	
	def __init__(self, interface):
		self._interface = interface
	
	def _data_to_engine(self, data):
		return plainify_data(data)
	
	def _data_from_engine(self, data):
		return objectify_data(data)
	
	def get_items(self, *args):
		func = self._data_from_engine
		for item in self._interface.get_items(*args):
				yield func(item)
	
	def get_items_for_tag(self, *args):
		func = self._data_from_engine
		for item in self._interface.get_items_for_tag(*args):
			yield func(item)
	
	def get_related_items(self, *args):
		for related_item in self._interface.get_related_items(*args):
			yield self._data_from_engine(related_item)
	
	def get_most_used_tags(self, *args):
		return self._interface.get_most_used_tags(*args)
	
	def get_recent_used_tags(self, *args):
		return self._interface.get_recent_used_tags(*args)
	
	def get_timestamps_for_tag(self, *args):
		return self._interface.get_timestamps_for_tag(*args)
	
	def get_bookmarks(self, *args):
		items = []
		for item in self._interface.get_bookmarks(*args):
			items.append(self._data_from_engine(item))
		return items
	
	def get_sources_list(self, *args):
		return self._interface.get_sources_list()
	
	def update_item(self, item):
		return self._interface.update_item(self._data_to_engine(item))
	
	def delete_item(self, *args):
		return self._interface.delete_item(*args)


if "--no-dbus" in sys.argv:
	
	import gobject
	from zeitgeist_engine.zeitgeist_dbus import RemoteInterface
	from zeitgeist_engine.zeitgeist_datasink import datasink
	
	class SignalHandling(gobject.GObject):
		
		__gsignals__ = {
			"signal_updated" : (gobject.SIGNAL_RUN_FIRST,
				gobject.TYPE_NONE,
				()),
		}
	
	class EngineInterface(BaseEngineInterface, gobject.GObject):
		
		def connect(self, signal, callback, arg0=None):
			signals.connect(signal, callback, arg0)
		
		def emit_signal_updated(self, *args):
			signals.emit("signal_updated")
	
	signals = SignalHandling()
	remoteinterface = RemoteInterface(start_dbus = False)
	engine = EngineInterface(remoteinterface)
	datasink.reload_callbacks.append(engine.emit_signal_updated)

else:
	
	from zeitgeist_gui.zeitgeist_dbus import iface, dbus_connect
	
	class EngineInterface(BaseEngineInterface):
		
		def connect(self, *args):
			return dbus_connect(*args)
		
		def emit_signal_updated(self, *args):
			return self._interface.emit_signal_updated(*args)
	
	engine = EngineInterface(iface)
