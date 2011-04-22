# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2010 Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
# Copyright © 2009 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
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

from __future__ import with_statement
import os
import cPickle as pickle
import dbus
import dbus.service
import gobject
import logging

from zeitgeist.datamodel import get_timestamp_for_now
from _zeitgeist.engine.datamodel import Event, DataSource as OrigDataSource
from _zeitgeist.engine.extension import Extension
from _zeitgeist.engine import constants

log = logging.getLogger("zeitgeist.datasource_registry")

DATA_FILE = os.path.join(constants.DATA_PATH, "datasources.pickle")
REGISTRY_DBUS_OBJECT_PATH = "/org/gnome/zeitgeist/data_source_registry"
REGISTRY_DBUS_INTERFACE = "org.gnome.zeitgeist.DataSourceRegistry"
SIG_FULL_DATASOURCE = "(sssa("+constants.SIG_EVENT+")bxb)"
DISK_WRITE_TIMEOUT = 5*60*1000 # 5 Minutes

class DataSource(OrigDataSource):
	@classmethod
	def from_list(cls, l):
		"""
		Parse a list into a DataSource, overriding the value of Running
		to always be False.
		"""
		s = cls(l[cls.UniqueId], l[cls.Name], l[cls.Description],
			l[cls.EventTemplates], False, l[cls.LastSeen], l[cls.Enabled])
		return s
	
	def update_from_data_source(self, source):
		for prop in (self.Name, self.Description, self.EventTemplates,
			self.LastSeen, self.Running):
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
		
		self._registry = {}
		if os.path.exists(DATA_FILE):
			try:
				with open(DATA_FILE) as data_file:
					for datasource in pickle.load(data_file):
						ds = DataSource.from_list(datasource)
						self._registry[ds[DataSource.UniqueId]] = ds
				log.debug("Loaded data-source data from %s" % DATA_FILE)
			except Exception, e:
				log.warn("Failed to load data file %s: %s" % (DATA_FILE, e))
		else:
			log.debug("No existing data-source data found.")
		self._running = {}
		
		# Connect to client disconnection signals
		dbus.SessionBus().add_signal_receiver(self._name_owner_changed,
			signal_name="NameOwnerChanged",
			dbus_interface=dbus.BUS_DAEMON_IFACE,
			arg2="", # only match services with no new owner
		)
		
		self._dirty = True
		gobject.timeout_add(DISK_WRITE_TIMEOUT, self._write_to_disk)
		
	def _write_to_disk(self):
		data = [DataSource.get_plain(datasource) for datasource in
			self._registry.itervalues()]
		try:
			if self._dirty:
				self._dirty = False
				with open(DATA_FILE, "w") as data_file:
					pickle.dump(data, data_file)
		except Exception, e:
			log.warn("Failed to write to data file %s: %s" % (DATA_FILE, e))
		return True
		#log.debug("Data-source registry update written to disk.")
	
	def pre_insert_event(self, event, sender):
		for (unique_id, bus_names) in self._running.iteritems():
			if sender in bus_names:
				datasource = self._registry[unique_id]
				# Update LastSeen time
				datasource.last_seen = get_timestamp_for_now()
				self._dirty = True
				# Check whether the data-source is allowed to insert events
				if not datasource.enabled:
					return None
		return event
	
	def unload(self):
		self._write_to_disk()
	
	# PUBLIC
	def register_data_source(self, unique_id, name, description, templates):
		source = DataSource(str(unique_id), unicode(name), unicode(description),
			map(Event.new_for_struct, templates))
		if unique_id in self._registry:
			datasource = self._registry[unique_id]
			datasource.update_from_data_source(source)
		else:
			datasource = self._registry[unique_id] = source
		self._write_to_disk()
		self.DataSourceRegistered(datasource)
		return datasource.enabled
	
	# PUBLIC
	def get_data_sources(self):
		return self._registry.values()
	
	# PUBLIC
	def set_data_source_enabled(self, unique_id, enabled):
		datasource = self._registry[unique_id]
		if not datasource:
			return False
		if datasource.enabled != enabled:
			datasource.enabled = enabled
			self.DataSourceEnabled(datasource.unique_id, enabled)
		return True
	
	@dbus.service.method(REGISTRY_DBUS_INTERFACE,
						 in_signature="sssa("+constants.SIG_EVENT+")",
						 out_signature="b",
						 sender_keyword="sender")
	def RegisterDataSource(self, unique_id, name, description, event_templates,
	    sender):
		"""
		Register a data-source as currently running. If the data-source was
		already in the database, its metadata (name, description and
		event_templates) are updated.
		
		The optional event_templates is purely informational and serves to
		let data-source management applications and other data-sources know
		what sort of information you log.
		
		:param unique_id: unique ASCII string identifying the data-source
		:param name: data-source name (may be translated)
		:param description: data-source description (may be translated)
		:param event_templates: list of
			:class:`Event <zeitgeist.datamodel.Event>` templates.
		"""
		if not unique_id in self._running:
		    self._running[unique_id] = [sender]
		elif sender not in self._running[unique_id]:
		    self._running[unique_id].append(sender)
		return self.register_data_source(unique_id, name, description,
			event_templates)
	
	@dbus.service.method(REGISTRY_DBUS_INTERFACE,
						 in_signature="",
						 out_signature="a"+SIG_FULL_DATASOURCE)
	def GetDataSources(self):
		"""
		Get the list of known data-sources.
		
		:returns: A list of
			:class:`DataSource <zeitgeist.datamodel.DataSource>` objects.
		"""
		return self.get_data_sources()

	@dbus.service.method(REGISTRY_DBUS_INTERFACE,
						 in_signature="sb",)
	def SetDataSourceEnabled(self, unique_id, enabled):
		"""
		Get a list of data-sources.
		
		:param unique_id: unique string identifying a data-source (it's a good
			idea to use a domain name / email address / etc. as part of the
			name, to avoid name clashes).
		:type unique_id: string
		:param enabled: whether the data-source is to be enabled or disabled
		:type enabled: Bool
		:returns: True on success, False if there is no known data-source
			matching the given ID.
		:rtype: Bool
		"""
		self.set_data_source_enabled(unique_id, enabled)

	@dbus.service.signal(REGISTRY_DBUS_INTERFACE,
						signature="sb")
	def DataSourceEnabled(self, value, enabled):
		"""This signal is emitted whenever a data-source is enabled or
		disabled.
		
		:returns: unique string identifier of a data-source and a bool which
			is True if it was enabled False if it was disabled.
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

	@dbus.service.signal(REGISTRY_DBUS_INTERFACE,
						signature=SIG_FULL_DATASOURCE)
	def DataSourceDisconnected(self, datasource):
		"""This signal is emitted whenever the last running instance of a
		data-source disconnects.
		
		:returns: the disconnected data-source
		:rtype: :class:`DataSource <zeitgeist.datamodel.DataSource>`
		"""
		return datasource

	def _name_owner_changed(self, owner, old, new):
		"""
		Cleanup disconnected clients and mark data-sources as not running
		when no client remains.
		"""
		uid = [uid for uid, ids in self._running.iteritems() if owner in ids]
		if not uid:
			return
		uid = uid[0]

		datasource = self._registry[uid]
		
		# Update LastSeen time
		datasource.last_seen = get_timestamp_for_now()
		
		strid = "%s (%s)" % (uid, datasource.name)
		log.debug("Client disconnected: %s" % strid)
		if len(self._running[uid]) == 1:
			log.debug("No remaining client running: %s" % strid)
			del self._running[uid]
			datasource.running = False
			self.DataSourceDisconnected(datasource)
		else:
			self._running[uid].remove(owner)
