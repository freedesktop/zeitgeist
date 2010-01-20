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

from zeitgeist.datamodel import Datasource
from _zeitgeist.engine.extension import Extension
from _zeitgeist.engine import constants

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("zeitgeist.datasource_registry")

DATA_FILE = os.path.join(constants.DATA_PATH, "datasources.pickle")
REGISTRY_DBUS_OBJECT_PATH = "/org/gnome/zeitgeist/datasource_registry"
REGISTRY_DBUS_INTERFACE = "org.gnome.zeitgeist.DatasourceRegistry"

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
				self._registry = [Datasource(datasource) for datasource in \
					pickle.load(open(DATA_FILE))]
				log.debug("Loaded datasource data from %s" % DATA_FILE)
			except Exception, e:
				log.warn("Failed to load data file %s: %s" % (DATA_FILE, e))
				self._registry = []
		else:
			log.debug("No existing blacklist config found")
			self._blacklist = []

	# TODO: Block events from disabled data sources
	#def insert_event_hook(self, event):
	#	for tmpl in self._blacklist:
	#		if ........: return None
	#	return event
	
	def _write_to_disk(self):
		data = [list(datasource) for datasource in self._registry]
		with open(DATA_FILE, "w") as data_file:
			pickle.dump(data, data_file)
		log.debug("Datasource registry updated: %s" % self._blacklist)
	
	# PUBLIC
	def register_datasource(self, name, description, actors):
		source = Datasource(name, description, actors)
		for datasource in self._registry:
			if datasource == source:
				datasource.update_from_datasource(source)
				return datasource[Datasource.Enabled]
		self._registry.append(source)
		return True
	
	# PUBLIC
	def get_datasources(self):
		return self._registry
	
	@dbus.service.method(REGISTRY_DBUS_INTERFACE,
						 in_signature="ssas",
						 out_signature="b")
	def RegisterDatasource(self, name, description, actors):
		"""
		Register a datasource as currently running. If the datasource was
		already in the database, its metadata (description and actors) are
		updated.
		
		:param name: unique string
		:param description: string
		:param actors: list of strings representing event actors
		"""
		return self.register_datasource(name, description, actors)
	
	@dbus.service.method(REGISTRY_DBUS_INTERFACE,
						 in_signature="",
						 out_signature="a("+constants.SIG_EVENT+")")
	def GetDatasources(self):
		"""
		Get a list of datasources.
		
		:returns: A list of
			:class:`Datasource <zeitgeist.datamodel.Datasource>`
		"""
		return self.get_datasources()
