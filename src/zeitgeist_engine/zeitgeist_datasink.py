import sys
import time
import urllib

from gettext import gettext as _

from zeitgeist_engine.zeitgeist_base import ItemSource
from zeitgeist_engine.zeitgeist_firefox import FirefoxSource
from zeitgeist_engine.zeitgeist_tomboy import TomboySource
from zeitgeist_engine.zeitgeist_recent import *
from zeitgeist_engine.zeitgeist_dbcon import DBConnector

class DataSinkSource(ItemSource):
	def __init__(self, note_path=None):
		ItemSource.__init__(self,
							name=_("Sink"),
							icon=None,
							uri="source:///Datasink")
		self.sources=[]
		
		'''
		Recently Used
		'''
		
		self.videos=RecentlyUsedVideoSource()
		self.videos.run()
		self.music=RecentlyUsedMusicSource()
		self.music.run()
		self.images=RecentlyUsedImagesSource()
		self.images.run()
		self.docs=RecentlyUsedDocumentsSource()
		self.docs.run()
		self.others = RecentlyUsedOthersSource()
		self.others.run()
		recent_model.connect("reload", self.log)
		
		#self.firefox = FirefoxSource()
		#self.firefox.run()
		
		#self.chats = RecentContacts()
		
		self.tomboy = TomboySource()
		self.tomboy.run()
		self.tomboy.connect("reload", self.log)
		
		self.lasttimestamp = 0
		self.init_sources()
		self.desktop_items=[]
		
		self.zdb = DBConnector()
		self.log()
	
	def init_sources(self):
	   self.sources=[
					 self.docs,
					 #self.firefox,
					 self.images,
					 self.music,
					 self.others,
					 #self.chats,
					 self.tomboy,
					 self.videos
					]
	
	def log(self,x=None):
	   
		print("logging")
		for source in self.sources:
			for item in source.get_items():
				self.zdb.insert_item(item)
		self.emit("reload")
			
	   
	def get_items(self,min=0,max=sys.maxint):
		
		items =[]
		
		for item in self.zdb.get_items(min,max):
			items.append(item)
		print " got all items"
		return items
		
		
	def get_items_by_time(self,min=0,max=sys.maxint):
		"Datasink getting all items from DaraProviders"
		items = self.get_items(min,max)
		items.sort(self.comparetime)
		return items
	
	def get_freq_items(self,min=0,max=sys.maxint):
		items =[]
		for source in self.sources:
			if source.get_active():
				sourcelist= source.get_freq_items(min,max)
				items += sourcelist
			del source
		items.sort(self.comparecount)
		for item in items:
			yield item
			del item
		del items
		gc.collect()
			   
	def get_desktop_items(self):
		DirectoryList = []	
		path = "~/Desktop"
		path = os.path.expanduser(path)
		os.path.walk(path, self.walker, DirectoryList)
		return self.desktop_items
		
	def walker(self, arg, dirname, filenames):
		self.desktop_items=[]
		# Create A List Of Files with full pathname
		for files in filenames:
			file = os.path.join(dirname, files)
			item = Item(uri=file)
			self.desktop_items.append(item)

datasink= DataSinkSource()
