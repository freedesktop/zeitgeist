# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Seif Lotfy <seif@lotfy.com>
# Copyright © 2009-2010 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
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

from threading import Thread
import gobject
import logging

from zeitgeist.datamodel import DataSource
from _zeitgeist.loggers.zeitgeist_setup_service import _Configuration, DefaultConfiguration

class DataProvider(gobject.GObject, Thread):
	
	__gsignals__ = {
		"reload" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
	}
	
	def __init__(self, unique_id, name, description="", event_templates=[],
		client=None, config=None):
		
		# Initialize superclasses
		Thread.__init__(self)
		gobject.GObject.__init__(self)
		
		self._name = name
		self._client = client
		self._ctx = gobject.main_context_default()
		
		if client:
			self._registry = self._client.get_extension("DataSourceRegistry",
				"data_source_registry")
			try:
				self._last_seen = [ds[DataSource.LastSeen] for ds in \
					self._registry.GetDataSources() if \
					ds[DataSource.UniqueId] == unique_id][0] - 3600000
				# We substract 1 hour to ensure no events got missed (because
				# of LastSeen being updated on disconnect).
				# TODO: Maybe it should be changed to (or we should add)
				# LastInsertion, though?
			except IndexError:
				self._last_seen = 0
			self._enabled = self._registry.RegisterDataSource(unique_id, name,
				description, event_templates)
		
		if not config:
			self.config = DefaultConfiguration(self._name)
		else:
			if not isinstance(config, _Configuration):
				raise TypeError
			self.config = config
	
	def get_name(self):
		return self._name
	
	def get_items(self):
		if not self._enabled:
			return []
		# FIXME: We need to figure out what to do with this configuration stuff
		# Maybe merge it into the DataSource registry so that everyone
		# can benefit from it, or just throw it out.
		if not self.config.isConfigured() or not self.config.enabled:
			logging.warning("'%s' isn't enabled or configured." % \
				self.config.get_internal_name())
			return []
		return self._get_items()
	
	def _get_items(self):
		""" Subclasses should override this to return data. """
		raise NotImplementedError
	
	def _process_gobject_events(self):
		""" Check for pending gobject events. This should be called in some
		meaningful place in _get_items on long running updates. """
		while self._ctx.pending():
			self._ctx.iteration()
