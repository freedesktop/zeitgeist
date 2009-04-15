import sys

class BaseEngineInterface():
	
	def __init__(self, interface):
		self._interface = interface
	
	def get_items(self, *args):
		for item in self._interface.get_items(*args):
			yield self._data_from_engine(item)
	
	def get_related_items(self, *args):
		for related_item in self._interface.get_related_items(*args):
			yield self._data_from_engine(related_item)
	
	def get_most_used_tags(self, *args):
		for tag in self._interface.get_most_used_tags(*args):
			yield tag
	
	def get_recent_used_tags(self, *args):
		for tag in self._interface.get_recent_used_tags(*args):
			yield tag
	
	def get_timestamps_for_tag(self, *args):
		return self._interface.get_timestamps_for_tag(*args)
	
	def get_bookmarks(self, *args):
		for item in self._interface.get_bookmarks(*args):
			yield self._data_from_engine(item)
	
	def get_sources_list(self, *args):
		return self._interface.get_sources_list()
	
	def update_item(self, item):
		return self._interface.update_item(self._data_to_engine(item))
	
	def delete_item(self, *args):
		return self._interface.delete_item(*args)


if "--no-dbus" in sys.argv:
	
	from zeitgeist_engine.zeitgeist_datasink import datasink
	
	class EngineInterface(BaseEngineInterface):
		
		def _data_to_engine(self, data):
			return dictify_data(plainify_data(data))
		
		def _data_from_engine(self, data):
			return objectify_data(plainify_data(data))
		
		def connect(self, *args):
			pass
			#return getattr()
	
	engine = EngineInterface(datasink)

else:
	
	from zeitgeist_gui.zeitgeist_dbus import iface, dbus_connect
	from zeitgeist_shared.zeitgeist_shared import plainify_data
	from zeitgeist_gui.zeitgeist_base import objectify_data
	
	class EngineInterface(BaseEngineInterface):
		
		def _data_to_engine(self, data):
			return plainify_data(data)
		
		def _data_from_engine(self, data):
			return objectify_data(data)
		
		def connect(self, *args):
			return dbus_connect(*args)
		
		def emit_signal_updated(self, *args):
			return self._interface.emit_signal_updated(*args)
	
	engine = EngineInterface(iface)
