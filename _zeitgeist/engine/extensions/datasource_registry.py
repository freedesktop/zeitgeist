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
import cPickle as pickle
import dbus
import dbus.service
import logging

from _zeitgeist.engine.datamodel import Event, DataSource as OrigDataSource
from _zeitgeist.engine.extension import Extension
from _zeitgeist.engine import constants

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("zeitgeist.datasource_registry")

DATA_FILE = os.path.join(constants.DATA_PATH, "datasources.pickle")
REGISTRY_DBUS_OBJECT_PATH = "/org/gnome/zeitgeist/data_source_registry"
REGISTRY_DBUS_INTERFACE = "org.gnome.zeitgeist.DataSourceRegistry"
SIG_FULL_DATASOURCE = "(ssa("+constants.SIG_EVENT+")bxb)"

class DataSource(OrigDataSource):
	@classmethod
	def from_list(cls, l):
	    """
	    Parse a list into a DataSource, overriding the value of Running
	    to always be False.
	    """
	    s = cls(l[cls.Name], l[cls.Description], l[cls.EventTemplates], False,
	        l[cls.LastSeen], l[cls.Enabled])
	    return s
	
	def update_from_data_source(self, source):
		for prop in (self.Description, self.EventTemplates, self.Running,
		    self.LastSeen):
			self[prop] = source[prop]

class DataSourceRegistry(Extension, dbus.service.Object):
	"""
	The Zeitgeist engine maintains a publicly available list of recognized
	data-sources (components inserting information into Zeitgeist). An
	option to disable such data-providers is also provided.
	
	The data-source registry of the Zeitgeist engine has DBus object path
	:const:`/org/gnome/zeitgeist/data_source_registry` under the bus name
	:const:`org.gnome.zeitgeist.DataSourceRegistry`.
	"""
	PUBLIC_METHODS = ["register_data_source", "get_data_sources",
		"set_data_source_enabled"]
	
	def __init__ (self, engine):
	
		Extension.__init__(self, engine)
		dbus.service.Object.__init__(self, dbus.SessionBus(),
			REGISTRY_DBUS_OBJECT_PATH)
		
		if os.path.exists(DATA_FILE):
			try:
				self._registry = [DataSource.from_list(
					datasource) for datasource in pickle.load(open(DATA_FILE))]
				log.debug("Loaded data-source data from %s" % DATA_FILE)
			except Exception, e:
				log.warn("Failed to load data file %s: %s" % (DATA_FILE, e))
				self._registry = []
		else:
			log.debug("No existing data-source data found.")
			self._registry = []
		self._running = {}
		
		# Connect to client disconnection signals
		dbus.SessionBus().add_signal_receiver(self._name_owner_changed,
		    signal_name="NameOwnerChanged",
		    dbus_interface=dbus.BUS_DAEMON_IFACE,
		    arg2="", # only match services with no new owner
	    )
	
	def _write_to_disk(self):
		data = [DataSource.get_plain(datasource) for datasource in self._registry]
		with open(DATA_FILE, "w") as data_file:
			pickle.dump(data, data_file)
		log.debug("Data-source registry updated.")
	
	def _get_data_source(self, name):
		for datasource in self._registry:
			if datasource[DataSource.Name] == name:
				return datasource
	
	def insert_event_hook(self, event, sender):
		for (name, bus_names) in self._running.iteritems():
			if sender in bus_names and not \
				self._get_data_source(name)[DataSource.Enabled]:
				return None
		return event
	
	# PUBLIC
	def register_data_source(self, name, description, templates):
		source = DataSource(unicode(name), unicode(description),
			map(Event.new_for_struct, templates))
		for datasource in self._registry:
			if datasource == source:
				datasource.update_from_data_source(source)
				self.DataSourceRegistered(datasource)
				return datasource[DataSource.Enabled]
		self._registry.append(source)
		self._write_to_disk()
		self.DataSourceRegistered(source)
		return True
	
	# PUBLIC
	def get_data_sources(self):
		return self._registry
	
	# PUBLIC
	def set_data_source_enabled(self, name, enabled):
		datasource = self._get_data_source(name)
		if not datasource:
			return False
		if datasource[DataSource.Enabled] != enabled:
			datasource[DataSource.Enabled] = enabled
			self.DataSourceEnabled(datasource[DataSource.Name], enabled)
		return True
	
	@dbus.service.method(REGISTRY_DBUS_INTERFACE,
						 in_signature="ssa("+constants.SIG_EVENT+")",
						 out_signature="b",
						 sender_keyword="sender")
	def RegisterDataSource(self, name, description, actors, sender):
		"""
		Register a data-source as currently running. If the data-source was
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
		return self.register_data_source(name, description, actors)
	
	@dbus.service.method(REGISTRY_DBUS_INTERFACE,
						 in_signature="",
						 out_signature="a"+SIG_FULL_DATASOURCE)
	def GetDataSources(self):
		"""
		Get a list of data-sources.
		
		:returns: A list of
			:class:`DataSource <zeitgeist.datamodel.DataSource>`
		"""
		return self.get_data_sources()

	@dbus.service.method(REGISTRY_DBUS_INTERFACE,
						 in_signature="sb",)
	def SetDataSourceEnabled(self, name, enabled):
		"""
		Get a list of data-sources.
		
		:param name: unique string identifying a data-source
		
		:returns: True on success, False if there is no known data-source
			matching the given name.
		:rtype: Bool
		"""
		return self.set_data_source_enabled(name, enabled)

	@dbus.service.signal(REGISTRY_DBUS_INTERFACE,
						signature="sb")
	def DataSourceEnabled(self, value, enabled):
		"""This signal is emitted whenever a data-source is enabled or
		disabled.
		
		:returns: data-source name and bool which is True if it was enabled
			False if it was disabled.
		:rtype: struct containing a string and a bool
		"""
		return (value, enabled)

	@dbus.service.signal(REGISTRY_DBUS_INTERFACE,
						signature=SIG_FULL_DATASOURCE)
	def DataSourceRegistered(self, datasource):
		"""This signal is emitted whenever a data-source registers itself.
		
		:returns: the registered data-source
		:rtype: :class:`DataSource <zeitgeist.datamodel.DataSource>`
		"""
		return datasource

	def _name_owner_changed(self, owner, old, new):
		"""
		Cleanup disconnected clients and mark data-sources as not running
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
			self._get_data_source(name)[DataSource.Running] = False
		else:
			del self._running[name][owner]
