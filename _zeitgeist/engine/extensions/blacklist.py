# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
#           © 2011 Manish Sinha <manishsinha@ubuntu.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 2.1 of the License, or
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
import json
import dbus
import dbus.service
from xdg import BaseDirectory
import logging

from _zeitgeist.engine.datamodel import Event
from _zeitgeist.engine.extension import Extension
from _zeitgeist.engine import constants

log = logging.getLogger("zeitgeist.blacklist")

CONFIG_FILE = os.path.join(constants.DATA_PATH, "blacklist.json")
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
	PUBLIC_METHODS = ["add_blacklist", "remove_blacklist", "get_blacklist"]
	
	def __init__ (self, engine):		
		Extension.__init__(self, engine)
		dbus.service.Object.__init__(self, dbus.SessionBus(),
		                             BLACKLIST_DBUS_OBJECT_PATH)
		if os.path.exists(CONFIG_FILE):
			try:
				pcl_file = open(CONFIG_FILE, "r")
				self._blacklist = json.load(pcl_file)
				log.debug("Loaded blacklist config from %s"
				          % CONFIG_FILE)
			except Exception, e:
				log.warn("Failed to load blacklist config file %s: %s"\
				         % (CONFIG_FILE, e))
				self._blacklist = {}
		else:
			log.debug("No existing blacklist config found")
			self._blacklist = {}
	
	def pre_insert_event(self, event, sender):
		for tmpl in self._blacklist.itervalues():
			if event.matches_template(Event(tmpl)): return None
		return event
	
	# PUBLIC
	def add_blacklist(self, blacklist_id, event_template):
		Event._make_dbus_sendable(event_template)
		self._blacklist[blacklist_id] = event_template
		
		out = file(CONFIG_FILE, "w")
		json.dump(self._blacklist, out)		
		out.close()
		log.debug("Blacklist added: %s" % self._blacklist)
	
	# PUBLIC
	def remove_blacklist(self, blacklist_id):
		event_template = self._blacklist[blacklist_id]
		del self._blacklist[blacklist_id]
		
		out = file(CONFIG_FILE, "w")
		json.dump(self._blacklist, out)		
		out.close()
		log.debug("Blacklist deleted: %s" % self._blacklist)
		
		return event_template
	
	# PUBLIC
	def get_blacklist(self):
		return self._blacklist
	
	@dbus.service.method(BLACKLIST_DBUS_INTERFACE,
	                     in_signature="s("+constants.SIG_EVENT+")")
	def AddTemplate(self, blacklist_id, event_template):
		"""
		Set the blacklist to :const:`event_template`. Events
		matching any these templates will be blocked from insertion
		into the log. It is still possible to find and look up events
		matching the blacklist which was inserted before the blacklist
		banned them.
		
		:param blacklist_id: A string identifier for a blacklist template
		
		:param event_template: An object of
		    :class:`Events <zeitgeist.datamodel.Event>`
		"""
		tmp = Event(event_template)
		self.add_blacklist(blacklist_id, tmp)
		self.TemplateAdded(blacklist_id, event_template)
		
	@dbus.service.method(BLACKLIST_DBUS_INTERFACE,
	                     in_signature="",
	                     out_signature="a{s("+constants.SIG_EVENT+")}")
	def GetTemplates(self):
		"""
		Get the current list of blacklist templates.
		
		:returns: An dictionary of { string ,
		    :class:`Events <zeitgeist.datamodel.Event>` }
		"""
		return self.get_blacklist()
	
	@dbus.service.method(BLACKLIST_DBUS_INTERFACE,
	                     in_signature="s",
	                     out_signature="")
	def RemoveTemplate(self, blacklist_id):
		"""
		Remove a blacklist template which is identified by the 
		        blacklist_id provided
		
		:param blacklist_id: A string identifier for a blacklist template
		
		"""
		try:
			event_template = self.remove_blacklist(blacklist_id)
			self.TemplateRemoved(blacklist_id, event_template)
		except KeyError:
			log.debug("Blacklist %s not found " % blacklist_id)
	
	@dbus.service.signal(BLACKLIST_DBUS_INTERFACE,
	                      signature="s("+constants.SIG_EVENT+")")
	def TemplateAdded(self, blacklist_id, event_template):
	    """
	    Raised when a template is added
	    
	    :param blacklist_id: The Id of the Blacklist template used for
	        setting the Blacklist
	    :param event_template: The blacklist template which was set
	    """
		pass

	@dbus.service.signal(BLACKLIST_DBUS_INTERFACE,
	                      signature="s("+constants.SIG_EVENT+")")
	def TemplateRemoved(self, blacklist_id, event_template):
	    """
	    Raised when a template is deleted
	    
	    :param blacklist_id: The Id of the Blacklist template which was deleted
	    :param event_template: The blacklist template which was deleted 
	    """
		pass
