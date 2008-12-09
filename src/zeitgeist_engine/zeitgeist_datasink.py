import sys
import time
import urllib
from gettext import gettext as _

from zeitgeist_engine.zeitgeist_base import DataProvider
from zeitgeist_engine.zeitgeist_firefox import *
from zeitgeist_engine.zeitgeist_tomboy import *
from zeitgeist_engine.zeitgeist_recent import *
from zeitgeist_engine.zeitgeist_dbcon import db
from zeitgeist_util import difffactory

class DataSinkSource(DataProvider):
	def __init__(self, note_path=None):
		DataProvider.__init__(self,
							name=_("Sink"),
							icon=None,
							uri="source:///Datasink")
		self.sources=[]
		
		'''
		Recently Used
		'''
		
		self.videos=RecentlyUsedVideoSource()
		self.videos.start()
		self.music=RecentlyUsedMusicSource()
		self.music.start()
		self.images=RecentlyUsedImagesSource()
		self.images.start()
		self.docs=RecentlyUsedDocumentsSource()
		self.docs.start()
		self.others = RecentlyUsedOthersSource()
		self.others.start()
		recent_model.connect("reload", self.log)
		
		#self.firefox = FirefoxSource()
		#self.firefox.start()
		
		self.tomboy = TomboySource()
		self.tomboy.start()
		self.tomboy.connect("reload", self.log)
		
		self.init_sources()
		
		self.log()
	
	def init_sources(self):
	   self.sources=[
					 self.docs,
					 #self.firefox,
					 self.images,
					 self.music,
					 self.others,
					 self.tomboy,
					 self.videos
					]
	   
	
	def log(self,x=None):
		for source in self.sources:
			if source.name=="Documents" or source.name=="Other":
				items=[]
				for item in source.get_items():
					tempitem = db.get_last_timestmap_for_item(item)
					'''
					if not tempitem or tempitem[3]=="":
						file = item.uri
						file = file.replace("%20"," ")
						f = open(file.replace("file://","",1))
						diff = f.read()
						item.diff=diff
						items.append(item)
						del diff, f, file
					
					else:
						baseinput=db.get_first_timestmap_for_item(item, True)
						diff = difffactory.create_diff(item.uri,baseinput[3])	
						if diff=="":
							#baseinput = db.get_last_timestmap_for_item(item,True)
							#item.diff = baseinput[3]
							pass
						else:
								item.diff="" 
					'''
					items.append(item)
						
					#del diff,baseinput,tempitem,item
				source.set_items(items)
		
			db.insert_items(source.get_items())
			del source
			
		gc.collect()
		self.emit("reload")
			
	   
	def get_items(self,min=0,max=sys.maxint,tags=""):
		tags = tags.replace(",","")
		filters = []
		for source in self.sources:
			if source.get_active():
				filters.append(source.get_name())
			del source
		
		# Used for benchmarking
		time1 = time.time()
		tagsplit = tags.split(" ")
		#print "TAGS COUNT " + str(len(tagsplit))
		for item in db.get_items(min,max):
				counter = 0	
				for tag in tagsplit:
					try:
						if filters.index(item.type)>=0 and (item.tags.lower().find(tag)> -1 or item.uri.lower().find(tag)>-1):
							if item.type=="Documents" or item.type=="Other":
								#orgsrc= db.get_first_timestmap_for_item(item, True)
								item.original_source=""
							counter = counter +1
						if counter == len(tagsplit):
							yield item
					except:
						pass
		del filters
		
		time2 = time.time()
		print("Got all items: " + str(time2 -time1))
		gc.collect()
	
	def update_item(self,item):
		db.update_item(item)
		self.emit("reload")
	
	def get_items_by_time(self,min=0,max=sys.maxint,tags=""):
		"Datasink getting all items from DaraProviders"
		for item in self.get_items(min,max,tags):
			yield item

	'''			
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
			item = Data(uri=file)
			self.desktop_items.append(item)
'''

datasink= DataSinkSource()
