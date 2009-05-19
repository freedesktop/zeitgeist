# -.- encoding: utf-8 -.-

import sys
import os
import gettext
import gobject

from zeitgeist_dbcon import db
from zeitgeist.shared.zeitgeist_shared import *


class ZeitgeistEngine(gobject.GObject):
	
	def __init__(self):
		gobject.GObject.__init__(self)
		self.reload_callback = None
	
	def get_items(self, min=0, max=sys.maxint, tags=""):
		# Emulate optional argument for the D-Bus interface
		if not max: max = sys.maxint
		# Get a list of all tags/search terms
		# (Here, there's no reason to use sets, because we're not using python's "in"
		#  keyword for membership testing.)
		if not tags == "":
			tags = tags.replace(",", " ")
			tagsplit = [tag.lower() for tag in tags.split(" ")]
		else:
			tagsplit = []
		
		# Loop over all of the items from the database
		for item in db.get_items(min, max):
			# Check if the document type matches; If it doesn't then don't bother checking anything else
				matches = True
				# Loop over every tag/search term
				for tag in tagsplit:
					# If the document name or uri does NOT match the tag/search terms then skip this item
					if not tag in item[3].lower().split(',') and not item[0].lower().find(tag) > -1:
						matches = False
						break
				if matches:
					yield item
	
	def get_items_for_tag(self, tag):
		return (item for item in db.get_items_for_tag(tag))
	
	def get_bookmarks(self):
		return db.get_bookmarked_items()
	
	def get_types(self):
		return db.get_types()
	
	def update_item(self, item):
		print _("Updating item: %s") % item
		db.update_item(item)		 
	
	def delete_item(self, item):
		print _("Deleting item: %s") % item
		db.delete_item(item)
	
	def get_items_by_time(self, min=0, max=sys.maxint, tags=""):
		"Datasink getting all items from DataProviders"
		return self.get_items(min, max, tags)
	
	def get_items_with_mimetype(self, mimetype, min=0, max=sys.maxint, tags=""):
		items = []
		for item in self.get_items_by_time(min, max, tags):
			if item[4] in mimetype.split(','):
				items.append(item)
		return items
	
	def get_all_tags(self):
		return db.get_all_tags()
	
	def get_most_used_tags(self, count=20, min=0, max=sys.maxint):
		if not count: count = 20
		if not min: min = 0
		if not max: max = sys.maxint
		return db.get_most_tags(count, min, max)
	
	def get_recent_used_tags(self, count=20, min=0, max=sys.maxint):
		if not count: count = 20
		if not min: min = 0
		if not max: max = sys.maxint
		return db.get_recent_tags(count, min, max)
	
	def get_timestamps_for_tag(self, tag):
		begin = db.get_min_timestamp_for_tag(tag)
		end = db.get_max_timestamp_for_tag(tag)
		
		if begin and end:
			if end - begin > 86400:
				end = end + 86400
		else:
			begin =0
			end = 0
		return (begin, end)
	
	def get_related_items(self, item):
		return db.get_related_items(item)
	
	def get_items_related_by_tags(self, item):
		return db.get_items_related_by_tags(item)
	
	def insert_item(self, item):
		if db.insert_item(item):
			self.reload_callback()
	
	def insert_items(self, items):
		if db.insert_items(items):
			self.reload_callback()

datasink = ZeitgeistEngine()
