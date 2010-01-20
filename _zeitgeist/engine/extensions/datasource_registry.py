# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2010 Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
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

from __future__ import with_statement
import os
import time
import cPickle as pickle
import dbus
import dbus.service
import logging

from zeitgeist.datamodel import Datasource as OrigDatasource
from _zeitgeist.engine.extension import Extension
from _zeitgeist.engine import constants

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("zeitgeist.datasource_registry")

DATA_FILE = os.path.join(constants.DATA_PATH, "datasources.pickle")
REGISTRY_DBUS_OBJECT_PATH = "/org/gnome/zeitgeist/datasource_registry"
REGISTRY_DBUS_INTERFACE = "org.gnome.zeitgeist.DatasourceRegistry"

class Datasource(OrigDatasource):
	@classmethod
	def from_list(cls, l):
	    """
	    Parse a list into a datasource, overriding the value of Running
	    to always be False.
	    """
	    s = cls(l[cls.Name], l[cls.Description], l[cls.Actors], False,
	        l[cls.LastSeen], l[cls.Enabled])
	    return s
	
	def update_from_datasource(self, source):
		for prop in (self.Description, self.Actors, self.Running, self.LastSeen):
			self[prop] = source[prop]

class DatasourceRegistry(Extension, dbus.service.Object):
	"""
	The Zeitgeist engine maintains a list of ......................
	
	The datasource registry of the Zeitgeist engine has DBus object path
	:const:`/org/gnome/zeitgeist/datasource_registry` under the bus name
	:const:`org.gnome.zeitgeist.DatasourceRegistry`.
	"""
	PUBLIC_METHODS = ["register_datasource", "get_datasources"]
	
	def __init__ (self, engine):
	
		Extension.__init__(self, engine)
		dbus.service.Object.__init__(self, dbus.SessionBus(),
			REGISTRY_DBUS_OBJECT_PATH)
		
		if os.path.exists(DATA_FILE):
			try:
				self._registry = [Datasource.from_list(
					datasource) for datasource in pickle.load(open(DATA_FILE))]
				log.debug("Loaded datasource data from %s" % DATA_FILE)
			except Exception, e:
				log.warn("Failed to load data file %s: %s" % (DATA_FILE, e))
				self._registry = []
		else:
			log.debug("No existing datasource data found.")
			self._registry = []
		self._running = {}
		
		# Connect to client disconnection signals
		dbus.SessionBus().add_signal_receiver(self._name_owner_changed,
		    signal_name="NameOwnerChanged",
		    dbus_interface=dbus.BUS_DAEMON_IFACE,
		    arg2="", # only match services with no new owner
	    )

	# TODO: Block events from disabled data sources
	#def insert_event_hook(self, event):
	#	for tmpl in self._blacklist:
	#		if ........: return None
	#	return event
	
	def _write_to_disk(self):
		data = [list(datasource) for datasource in self._registry]
		with open(DATA_FILE, "w") as data_file:
			pickle.dump(data, data_file)
		log.debug("Datasource registry updated.")
	
	def _get_datasource(self, name):
		for datasource in self._registry:
			if datasource[Datasource.Name] == name:
				return datasource
	
	# PUBLIC
	def register_datasource(self, name, description, actors):
		source = Datasource(name, description, actors)
		for datasource in self._registry:
			if datasource == source:
				datasource.update_from_datasource(source)
				return datasource[Datasource.Enabled]
		self._registry.append(source)
		self._write_to_disk()
		return True
	
	# PUBLIC
	def get_datasources(self):
		return self._registry
	
	@dbus.service.method(REGISTRY_DBUS_INTERFACE,
						 in_signature="ssas",
						 out_signature="b",
						 sender_keyword="sender")
	def RegisterDatasource(self, name, description, actors, sender):
		"""
		Register a datasource as currently running. If the datasource was
		already in the database, its metadata (description and actors) are
		updated.
		
		:param name: unique string
		:param description: string
		:param actors: list of strings representing event actors
		"""
		if not name in self._running:
		    self._running[name] = [sender]
		elif sender not in self._running[name]:
		    self._running[name].append(sender)
		return self.register_datasource(name, description, actors)
	
	@dbus.service.method(REGISTRY_DBUS_INTERFACE,
						 in_signature="",
						 out_signature="a(ssasbxb)")
	def GetDatasources(self):
		"""
		Get a list of datasources.
		
		:returns: A list of
			:class:`Datasource <zeitgeist.datamodel.Datasource>`
		"""
		return self.get_datasources()

	def _name_owner_changed(self, owner, old, new):
		"""
		Cleanup disconnected clients and mark datasources as not running
		when no client remains.
		"""
		name = [name for name, ids in self._running.iteritems() if owner in ids]
		if not name:
			return
		name = name[0]
		
		log.debug("Client disconnected: %s" % name)
		if len(self._running[name]) == 1:
			log.debug("No remaining client running: %s" % name)
			del self._running[name]
			self._get_datasource(name)[Datasource.Running] = False
		else:
			del self._running[name][owner]
