# -.- coding: utf-8 -.-

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

from threading import Thread
import gobject
import logging

from _zeitgeist.loggers.zeitgeist_setup_service import _Configuration, DefaultConfiguration

class DataProvider(gobject.GObject, Thread):
	
	__gsignals__ = {
		"reload" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
	}
	
	def __init__(self, name, config=None):
		
		# Initialize superclasses
		Thread.__init__(self)
		gobject.GObject.__init__(self)
		
		self._name = name
		self._ctx = gobject.main_context_default()
		
		if not config:
			self.config = DefaultConfiguration(self.name)
		else:
			if not isinstance(config, _Configuration):
				raise TypeError
			self.config = config
	
	def get_name(self):
		return self._name
	
	def get_items(self):
		if not self.config.isConfigured() or not self.config.enabled:
			logging.warning("'%s' isn't enabled or configured." % \
				self.config.get_internal_name())
			return []
		return self._get_items()):
	
	def _get_items(self):
		""" Subclasses should override this to return data. """
		raise NotImplementedError
	
	def _process_gobject_events():
		""" Check for pending gobject events. This should be called in some
		meaningful place in _get_items on long running updates. """
		while self.__ctx.pending():
			self.__ctx.iteration()
