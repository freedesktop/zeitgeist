# -.- encoding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import dbus
import dbus.service
import logging

from zeitgeist.engine.engine import get_default_engine
from zeitgeist.dbusutils import dictify_data, sig_plain_data
from zeitgeist.singleton import SingletonApplication

_engine = get_default_engine()

class RemoteInterface(SingletonApplication):
	
	# Initialization
	
	def __init__(self, start_dbus=True, mainloop=None):
		SingletonApplication.__init__(self, bus_name = "org.gnome.zeitgeist",
											path_name = "/org/gnome/zeitgeist")
		self._mainloop = mainloop
	
	# Reading stuff
	
	@dbus.service.method("org.gnome.zeitgeist",
						in_signature="as", out_signature="a"+sig_plain_data)
	def GetItems(self, uris):
		return map(_engine.get_item, uris)
	
	@dbus.service.method("org.gnome.zeitgeist",
						in_signature="iiibsaa{sv}", out_signature="a"+sig_plain_data)
	def FindEvents(self, min_timestamp, max_timestamp, limit,
			sorting_asc, mode, filters):
		# filters is a list of dicts, where each dict can have the following items:
		#   text_name: <str>
		#   text_uri: <str>
		#   tags: <list> of <str>
		#   mimetypes: <list> or <str>
		#   source: <str>
		#   content: <str>
		#   bookmarked: <bool> (True means bookmarked items, and vice versa
		return _engine.find_events(min_timestamp, max_timestamp, limit,
			sorting_asc, mode, filters, False)
	
	@dbus.service.method("org.gnome.zeitgeist",
						in_signature="iisaa{sv}", out_signature="a"+sig_plain_data)
	def CountEvents(self, min_timestamp, max_timestamp, mode, filters):
		# The parameteres are the same as for FindEvents, except for sorting
		# which wouldn't make a difference, and limit.
		return _engine.find_events(min_timestamp, max_timestamp, 0, True,
			mode, filters, True)
	
	@dbus.service.method("org.gnome.zeitgeist",
						in_signature="s", out_signature="i")
	def GetLastTimestamp(self, uri):
		return _engine.get_last_timestamp(uri)
	
	@dbus.service.method("org.gnome.zeitgeist",
						in_signature="siii", out_signature="a(si)")
	def GetTags(self, name_filter, amount, min_timestamp, max_timestamp):
		return _engine.get_tags(name_filter, amount, min_timestamp, max_timestamp)
	
	@dbus.service.method("org.gnome.zeitgeist",
						in_signature="s", out_signature="a"+sig_plain_data)
	def GetRelatedItems(self, item_uri):
		# FIXME: Merge this into FindEvents so that matches can be
		# filtered?
		return _engine.get_related_items(item_uri)
	
	@dbus.service.method("org.gnome.zeitgeist",
						in_signature="s", out_signature="i")
	def GetLastInsertionDate(self, application):
		return _engine.get_last_insertion_date(application)
	
	@dbus.service.method("org.gnome.zeitgeist",
						in_signature="", out_signature="as")
	def GetTypes(self):
		return _engine.get_types()
	
	# Writing stuff
	
	@dbus.service.method("org.gnome.zeitgeist",
						in_signature="a"+sig_plain_data, out_signature="i")
	def InsertItems(self, items_list):
		result = _engine.insert_items([dictify_data(x) for x in items_list])
		return result if (result and self.EventsChanged()) else 0
	
	@dbus.service.method("org.gnome.zeitgeist",
						in_signature="a"+sig_plain_data, out_signature="")
	def UpdateItems(self, item_list):
		_engine.update_items([dictify_data(x) for x in item_list])
		self.EventsChanged()
	
	@dbus.service.method("org.gnome.zeitgeist",
						in_signature="as", out_signature="")
	def DeleteItems(self, uris):
		_engine.delete_items(uris)
		self.EventsChanged()
	
	# Signals and signal emitters
	
	@dbus.service.signal("org.gnome.zeitgeist")
	def EventsChanged(self):
		return True
	
	@dbus.service.signal("org.gnome.zeitgeist")
	def EngineStart(self):
		return True
	
	@dbus.service.signal("org.gnome.zeitgeist")
	def EngineExit(self):
		return True
	
	# Commands
	
	@dbus.service.method("org.gnome.zeitgeist")
	def Quit(self):
		if self._mainloop:
			self._mainloop.quit()
