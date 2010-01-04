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

from zeitgeist.datamodel import Event
from _zeitgeist.engine.extension import Extension
from _zeitgeist.engine import constants

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("zeitgeist.blacklist")

CONFIG_FILE = os.path.join(constants.DATA_PATH, "blacklist.pickle")
DBUS_OBJECT_PATH = "/org/gnome/zeitgeist/blacklist"

def _event2popo(ev):
	"""
	Ensure that an Event instance is a Plain Old Python Object (popo)
	without DBus wrappings etc.
	"""
	popo = list()
	popo.append(map(unicode, ev[0]))
	popo.append([map(unicode, subj) for subj in ev[1]])
	popo.append(str(ev[2]))
	return popo

class Blacklist(Extension, dbus.service.Object):
	PUBLIC_METHODS = ["set_blacklist", "get_blacklist"]
	
	def __init__ (self, engine):
		Extension.__init__(self, engine)
		dbus.service.Object.__init__(self, dbus.SessionBus(),
		                             DBUS_OBJECT_PATH)
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
	
	def insert_event_hook(self, event):
		for tmpl in self._blacklist:
			if event.matches_template(tmpl): return None
		return event
	
	# PUBLIC
	def set_blacklist(self, event_templates):
		self._blacklist = event_templates
		map(Event._make_dbus_sendable, self._blacklist)
		
		out = file(CONFIG_FILE, "w")
		pickle.dump(map(_event2popo, self._blacklist), out)		
		out.close()
		log.debug("Blacklist updated: %s" % self._blacklist)
	
	# PUBLIC
	def get_blacklist(self):
		return self._blacklist
	
	@dbus.service.method(constants.DBUS_INTERFACE,
	                     in_signature="a("+constants.SIG_EVENT+")")
	def SetBlacklist(self, event_templates):
		tmp = map(Event, event_templates)
		self.set_blacklist(tmp)
		
	@dbus.service.method(constants.DBUS_INTERFACE,
	                     in_signature="",
	                     out_signature="a("+constants.SIG_EVENT+")")
	def GetBlacklist(self):
		return self.get_blacklist()
