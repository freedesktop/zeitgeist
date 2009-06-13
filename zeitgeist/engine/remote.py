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

from zeitgeist.engine.engine import get_default_engine
from zeitgeist.shared.zeitgeist_shared import *

_engine = get_default_engine()

class RemoteInterface(dbus.service.Object):
	
	# Initialization
	
	def __init__(self, start_dbus=True, mainloop=None):
		bus_name = dbus.service.BusName("org.gnome.Zeitgeist", dbus.SessionBus())
		dbus.service.Object.__init__(self, bus_name, "/org/gnome/Zeitgeist")
		self._mainloop = mainloop
	
	# Reading stuff
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="s", out_signature=sig_plain_data)
	def GetItem(self, uri):
		return _engine.get_item(uri)
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="iiiss", out_signature="a"+sig_plain_data)
	def GetItems(self, min_timestamp, max_timestamp, limit, tags, mimetype):
		return _engine.get_items(min_timestamp, max_timestamp, limit, tags, mimetype)
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="siis", out_signature="a"+sig_plain_data)
	def GetItemsWithMimetype(self, mimetype, min_timestamp, max_timestamp, tags):
		return _engine.get_items_with_mimetype(mimetype, min_timestamp, max_timestamp, tags)
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="sii", out_signature="i")
	def GetCountForItem(self, uri, start, end):
		return _engine.get_count_for_item(self, uri, start, end)
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="i", out_signature="as")
	def GetURIsForTimestamp(self, timestamp):
		return _engine.get_uris_for_timestamp(timestamp)
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="i", out_signature="i")
	def GetLastTimestamp(self, uri):
		return _engine.get_last_timestamp(uri)
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="", out_signature="a"+sig_plain_data)
	def GetBookmarks(self):
		return _engine.get_bookmarks()
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="", out_signature="as")
	def GetAllTags(self):
		return _engine.get_all_tags()
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="iii", out_signature="as")
	def GetMostUsedTags(self, amount, min_timestamp, max_timestamp):
		return _engine.get_recently_used_tags(amount, min_timestamp, max_timestamp)
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="iii", out_signature="as")
	def GetRecentUsedTags(self, amount, min_timestamp, max_timestamp):
		return _engine.get_recently_used_tags(amount, min_timestamp, max_timestamp)
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="s", out_signature="a"+sig_plain_data)
	def GetRelatedItems(self, item_uri):
		return _engine.get_related_items(item_uri)
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="s", out_signature="(uu)")
	def GetTimestampsForTag(self, tag):
		return _engine.get_timestamps_for_tag(tag)
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="s", out_signature="i")
	def GetLastInsertionDate(self, application):
		return _engine.get_last_insertion_date(application)
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="", out_signature="a(ss)")
	def GetTypes(self):
		return _engine.get_types()
	
	# Writing stuff
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature=sig_plain_data, out_signature="b")
	def InsertItem(self, item_list):
		result = _engine.insert_item(dictify_data(item_list))
		if result:
			self.EmitSignalUpdated()
		return result
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="a"+sig_plain_data, out_signature="")
	def InsertItems(self, items_list):
		if _engine.insert_items([dictify_data(x) for x in items_list]):
			self.EmitSignalUpdated()
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature=sig_plain_data, out_signature="")
	def UpdateItem(self, item_list):
		_engine.update_item(dictify_data(item_list))
	
	@dbus.service.method("org.gnome.Zeitgeist",
						in_signature="s", out_signature="")
	def DeleteItem(self, item_uri):
		_engine.delete_item(item_uri)
	
	# Signals and signal emitters
	
	@dbus.service.signal("org.gnome.Zeitgeist")
	def SignalUpdated(self):
		pass
	
	@dbus.service.signal("org.gnome.Zeitgeist")
	def SignalExit(self):
		pass
	
	@dbus.service.method("org.gnome.Zeitgeist")
	def EmitSignalUpdated(self):
		self.SignalUpdated()
	
	# Commands
	
	@dbus.service.method("org.gnome.Zeitgeist")
	def Quit(self):
		if self._mainloop:
			self._mainloop.quit()
