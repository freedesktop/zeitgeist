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
from zeitgeist_twitter import TwitterSource

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
		
		self.firefox = FirefoxSource()
		self.firefox.start()
		
		self.tomboy = TomboySource()
		self.tomboy.start()
		self.tomboy.connect("reload", self.log)
		
		self.twitter=TwitterSource()
		self.twitter.start()
		
		self.init_sources()
		
		self.log()
	
	def init_sources(self):
	   self.sources=[
					 self.docs,
					 self.firefox,
					 self.images,
					 self.music,
					 self.others,
					 self.twitter,
					 self.tomboy,
					 self.videos
					]
	   
	
	def log(self,x=None):
		for source in self.sources:
			db.insert_items(source.get_items())
			
		gc.collect()
		self.emit("reload")
			
	   
	def get_items(self, min=0, max=sys.maxint, tags=""):
		# Get a list of all document types that we're interested in
		types = []
		for source in self.sources:
			if source.get_active():
				types.append(source.get_name())
		# For efficiency, we convert the list to an immutable set
		# Immutable sets (and regular sets) allow us to perform membership testing in O(1)
		#  time. Lists, on the other hand, perform membership testing in O(n) time.
		types = frozenset(types)
		
		# Get a list of all tags/search terms
		# (Here, there's no reason to use sets, because we're not using python's 'in' 
		#  keyword for membership testing.)
		if not tags == "":
			tags = tags.replace(",", "")
			tagsplit = tags.split(" ")
		else:
			tagsplit = []
		
		# Used for benchmarking
		#time1 = time.time()
		#print "TAGS COUNT " + str(len(tagsplit))
		
		# Loop over all of the items from the database
		for item in db.get_items(min, max):
			# Check if the document type matches; If it doesn't then don't bother checking anything else
			if item.type in types:
				matches = True
				# Loop over every tag/search term
				for tag in tagsplit:
					# If the document name or uri does NOT match the tag/search terms then skip this item
					if not item.tags.lower().find(tag)> -1 and not item.uri.lower().find(tag)>-1:
						matches = False
						break
				if matches:
					yield item
        
        
		#time2 = time.time()
		#print("Got all items: " + str(time2 -time1))
		gc.collect()
	
	def update_item(self,item):
		db.update_item(item)
		self.emit("reload")
	
	def get_items_by_time(self,min=0,max=sys.maxint,tags=""):
		"Datasink getting all items from DaraProviders"
		for item in self.get_items(min,max,tags):
			yield item

datasink= DataSinkSource()
