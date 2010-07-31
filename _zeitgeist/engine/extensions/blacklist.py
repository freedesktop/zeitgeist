# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
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

import os
import pickle
import dbus
import dbus.service
from xdg import BaseDirectory
import logging

from _zeitgeist.engine.datamodel import Event
from _zeitgeist.engine.extension import Extension
from _zeitgeist.engine import constants

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("zeitgeist.blacklist")

CONFIG_FILE = os.path.join(constants.DATA_PATH, "blacklist.pickle")
BLACKLIST_DBUS_OBJECT_PATH = "/org/gnome/zeitgeist/blacklist"
BLACKLIST_DBUS_INTERFACE = "org.gnome.zeitgeist.Blacklist"

class Blacklist(Extension, dbus.service.Object):
	"""
	The Zeitgeist engine maintains a list of event templates that is known
	as the blacklist. When inserting events via
	:meth:`org.gnome.zeitgeist.Log.InsertEvents <_zeitgeist.engine.remote.RemoteInterface.InsertEvents>`
	they will be checked against the blacklist templates and if they match
	they will not be inserted in the log, and any matching monitors will not
	be signalled.
	
	The blacklist of the Zeitgeist engine has DBus object path
	:const:`/org/gnome/zeitgeist/blacklist` under the bus name
	:const:`org.gnome.zeitgeist.Engine`.
	"""
	PUBLIC_METHODS = ["set_blacklist", "get_blacklist"]
	
	def __init__ (self, engine):		
		Extension.__init__(self, engine)
		dbus.service.Object.__init__(self, dbus.SessionBus(),
		                             BLACKLIST_DBUS_OBJECT_PATH)
		if os.path.exists(CONFIG_FILE):
			try:
				raw_blacklist = pickle.load(file(CONFIG_FILE))
				self._blacklist = map(Event, raw_blacklist)
				log.debug("Loaded blacklist config from %s"
				          % CONFIG_FILE)
			except Exception, e:
				log.warn("Failed to load blacklist config file %s: %s"\
				         % (CONFIG_FILE, e))
				self._blacklist = []
		else:
			log.debug("No existing blacklist config found")
			self._blacklist = []
	
	def pre_insert_event(self, event, sender):
		for tmpl in self._blacklist:
			if event.matches_template(tmpl): return None
		return event
	
	# PUBLIC
	def set_blacklist(self, event_templates):
		self._blacklist = event_templates
		map(Event._make_dbus_sendable, self._blacklist)
		
		out = file(CONFIG_FILE, "w")
		pickle.dump(map(Event.get_plain, self._blacklist), out)		
		out.close()
		log.debug("Blacklist updated: %s" % self._blacklist)
	
	# PUBLIC
	def get_blacklist(self):
		return self._blacklist
	
	@dbus.service.method(BLACKLIST_DBUS_INTERFACE,
	                     in_signature="a("+constants.SIG_EVENT+")")
	def SetBlacklist(self, event_templates):
		"""
		Set the blacklist to :const:`event_templates`. Events
		matching any these templates will be blocked from insertion
		into the log. It is still possible to find and look up events
		matching the blacklist which was inserted before the blacklist
		banned them.
		
		:param event_templates: A list of
		    :class:`Events <zeitgeist.datamodel.Event>`
		"""
		tmp = map(Event, event_templates)
		self.set_blacklist(tmp)
		
	@dbus.service.method(BLACKLIST_DBUS_INTERFACE,
	                     in_signature="",
	                     out_signature="a("+constants.SIG_EVENT+")")
	def GetBlacklist(self):
		"""
		Get the current blacklist templates.
		
		:returns: A list of
		    :class:`Events <zeitgeist.datamodel.Event>`
		"""
		return self.get_blacklist()
