# -.- encoding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Seif Lotfy <seif@lotfy.com>
# Copyright © 2009 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
# Copyright © 2009 Natan Yellin <aantny@gmail.com>
# Copyright © 2009 Alex Graveley <alex@beatniksoftware.com>
# Copyright © 2009 Markus Korn <thekorn@gmx.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import sys
import time
import os
from threading import Thread
import gobject
import gettext
import logging

from _zeitgeist.loggers.zeitgeist_setup_service import _Configuration, DefaultConfiguration

NAMES = set()

class DataProvider(gobject.GObject, Thread):
	# Clear cached items after 4 minutes of inactivity
	CACHE_CLEAR_TIMEOUT_MS = 1000 * 60 * 4
	
	__gsignals__ = {
		"reload" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
	}
	
	def __init__(self, name, icon=None, comment=None, uri=None,
					filter_by_date=True, config=None):
		
		# Initialize superclasses
		Thread.__init__(self)
		gobject.GObject.__init__(self)
		
		self.__ctx = gobject.main_context_default()
		
		if name in NAMES:
			raise RuntimeError
		self.name = name
		NAMES.add(name)
		self.icon = icon
		self.comment = comment
		self.uri = uri
		self.mimetype = "zeitgeist/item-source"
		self.timestamp = 0
		
		# Set attributes
		self.filter_by_date = filter_by_date
		self.clear_cache_timeout_id = None
		
		# Clear cached items on reload
		self.connect("reload", lambda x: self.set_items(None))
		self.hasPref = None
		self.counter = 0
		self.needs_view = True
		self.active = True
		if config is None:
			self.config = DefaultConfiguration(self.name)
		else:
			if not isinstance(config, _Configuration):
				raise TypeError
			self.config = config
	
	def run(self):
		self.get_items()
		
	def checkEnabled(self):
		try:
			enabled = self.config.enabled
		except AttributeError:
			return True
		else:
			return enabled
	
	def get_name(self):
		return self.name
	
	def get_icon_string(self):
		return self.icon
	
	def get_items(self, min=0, max=sys.maxint):
		"""
		Return the items for the indicated time periode.
		"""
		if not self.config.isConfigured() or not self.checkEnabled():
			logging.warning("'%s' is not enabled or configured." % \
				self.config.get_internal_name())
			return []
		def _wrapper():
			for n, i in enumerate(self.get_items_uncached()):
				if not self.checkEnabled(): #on each iteration???
					raise StopIteration
				if i["timestamp"] >= min and i["timestamp"] < max:
					yield i
				if not n % 50:
					# check for pending gobject events on long running updates
					# not sure when to check pending events, maybe for each iteration?
					while self.__ctx.pending():
						self.__ctx.iteration()
		return _wrapper()
	
	def get_items_uncached(self):
		"""Subclasses should override this to return/yield Datas. The results
		will be cached."""
		return []

	def set_items(self, items):
		"""Set the cached items. Pass None for items to reset the cache."""
		self.items = items
	
	def set_active(self,bool):
		self.active = bool
	
	def get_active(self):
		return self.active
	
	def items_contains_uri(self, items, uri):
		if uri in (item["uri"] for item in items):
			return True
		return False
