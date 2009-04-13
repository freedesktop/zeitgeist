from zeitgeist_gui.zeitgeist_dbus import iface
from zeitgeist_shared.zeitgeist_shared import *

class Bookmarker:
	
	def __init__(self):
		
		self.bookmarks = []
		self.reload_bookmarks()
	
	def get_bookmark(self,uri):
		return self.bookmarks.count(uri) > 0
	
	def add_bookmark(self,item):
		if self.bookmarks.count(item.uri) == 0:
			self.bookmarks.append(item.uri)
	
	def reload_bookmarks(self):
		self.bookmarks = []
		for item in iface.get_bookmarks():
			self.add_bookmark(objectify_data(item))
		iface.emit_signal_updated()
	
	def get_items_uncached(self):
		for bookmark in iface.get_bookmarks():
			yield objectify_data(bookmark)

bookmarker = Bookmarker()
