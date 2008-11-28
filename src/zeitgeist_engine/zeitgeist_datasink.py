import sys
import time
import urllib

from gettext import gettext as _

from zeitgeist_engine.zeitgeist_base import ItemSource
from zeitgeist_engine.zeitgeist_firefox import *
from zeitgeist_engine.zeitgeist_tomboy import *
from zeitgeist_engine.zeitgeist_recent import *
from zeitgeist_engine.zeitgeist_dbcon import db

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
		
		self.firefox = FirefoxSource()
		self.firefox.run()
		
		#self.chats = RecentContacts()
		
		self.tomboy = TomboySource()
		self.tomboy.run()
		self.tomboy.connect("reload", self.log)
		
		self.init_sources()
		
		self.log()
	
	def init_sources(self):
	   self.sources=[
					 self.docs,
					 self.firefox,
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
				db.insert_item(item)
		self.emit("reload")
			
	   
	def get_items(self,min=0,max=sys.maxint):
		filters = []
		for source in self.sources:
			if source.get_active():
				filters.append(source.get_name())
			del source
		
		# Used for benchmarking
		time1 = time.time()
		
		for item in db.get_items(min,max):
			try:
				if filters.index(item.type)>=0:
					if item.type =="Firefox History":
						yield FirefoxItem(item.uri,item.name,item.timestamp,item.count)
					elif item.type =="Notes":
						yield NoteItem(item.uri,item.timestamp)
					else:
						yield item	
			except:
				pass
			del item
		del filters
		
		time2 = time.time()
		print("Got all items: " + str(time2 -time1))
		gc.collect()
		
	def get_items_by_time(self,min=0,max=sys.maxint):
		"Datasink getting all items from DaraProviders"
		for item in self.get_items(min,max):
			yield item
			
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
