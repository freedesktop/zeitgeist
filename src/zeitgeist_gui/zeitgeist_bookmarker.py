# -.- encoding: utf-8 -.-

from zeitgeist_gui.zeitgeist_engine_wrapper import engine

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
		for item in engine.get_bookmarks():
			self.add_bookmark(item)
		engine.emit_signal_updated()
	
	def get_items_uncached(self):
		return engine.get_bookmarks()

bookmarker = Bookmarker()
