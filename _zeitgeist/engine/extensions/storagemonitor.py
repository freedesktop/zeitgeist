# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
# Copyright © 2011 Canonical Ltd
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
import dbus
import dbus.service
import gio
import logging

from zeitgeist.datamodel import Event
from _zeitgeist.engine.extension import Extension
from _zeitgeist.engine import constants

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("zeitgeist.storagemonitor")

#
# Storage mediums we need to handle:
#
# - USB drives
# - Data CD/DVDs
# - Audio CDs
# - Video DVD
# - Networked file systems
# - Online resources
#
# A storage medium is  gio.Volume (since this is a physical entity for the user)
# or a network interface - how ever NetworkManager/ConnMan model these
#
# We can not obtain UUIDs for all of the listed gio.Volumes, so we need a
# fallback chain of identifiers
#
# DB schema: 
# It may be handy for app authors to have the human-readable
# description at hand. We can not currently easily do this in the
# current db... We may be able to do this in a new table, not
# breaking compat with the log db. We might also want a formal type
# associated with the storage so apps can use an icon for it.
# A new table and a new object+interface on DBus could facilitate this
#
# 'storage' table
#   id
#   name
#   state
#   +type
#   +display_name
#
# FIXME: We can not guess what the correct ID of CDs and DVDs were when they
#        are ejected, and also guess "UNKNOWN"
#

import logging
log = logging.getLogger("zeitgeist.storagemonitor")

from zeitgeist.datamodel import StorageState
from _zeitgeist.engine.sql import get_default_cursor

class StorageMonitor(Extension):
	"""
	
	"""
	PUBLIC_METHODS = []
	
	def __init__ (self, engine):		
		Extension.__init__(self, engine)
		self._db = get_default_cursor()
		mon = gio.VolumeMonitor()
		
		# Update DB with all current states
		for vol in mon.get_volumes():
			self.add_storage_medium(self._get_volume_id(vol))
		
		# React to volumes comming and going
		mon.connect("volume-added", self._on_volume_added)
		mon.connect("volume-removed", self._on_volume_removed)
		
		# Write connectivity to the DB. Dynamically decide whether to use
		# Connman or NetworkManager
		if dbus.SystemBus().name_has_owner ("net.connman"):
			self._network = ConnmanNetworkMonitor(lambda : self.add_storage_medium("net"),
			                                      lambda : self.remove_storage_medium("net"))
		elif dbus.SystemBus().name_has_owner ("org.freedesktop.NetworkManager"):
			self._network = NMNetworkMonitor(lambda : self.add_storage_medium("net"),
			                               lambda : self.remove_storage_medium("net"))
		else:
			log.info("No network monitoring system found (Connman or NetworkManager)."
			         "Network monitoring disabled")
	
	def insert_event_hook (self, event):
		"""
		On-the-fly add subject.storage to events if it is not set
		"""
		for subj in event.subjects:
			if not subj.storage:
				storage = self._find_storage(subj.uri)
				#log.debug("Subject %s resides on %s" % (subj.uri, storage))
				subj.storage = storage
		return event
	
	def _find_storage (self, uri):
		"""
		Given a URI find the name of the storage medium is resides on
		"""
		uri_scheme = uri.rpartition("://")[0]
		if uri_scheme in ["http", "ftp", "sftp", "ssh", "mailto"]:
			return "net"
		elif uri_scheme == "file":
			# Note: gio.File.find_enclosing_mount() does not behave
			#       as documented, but throws errors when no
			#       gio.Mount is found.
			#       Cases where we have no mount often happens when
			#       we are on a non-removable drive , and this is
			#       the assumption here. We use the stora medium
			#       'local' for this situation
			try:
				mount = gio.File(uri=uri).find_enclosing_mount()
			except gio.Error:
				return "local"
			if mount is None: return "UNKNOWN"
			return self._get_volume_id(mount.get_volume())
	
	def _on_volume_added (self, mon, volume):
		self.add_storage_medium (self._get_volume_id(volume))
	
	def _on_volume_removed (self, mon, volume):
		self.remove_storage_medium (self._get_volume_id(volume))

	def _get_volume_id (self, volume):
		"""
		Get a string identifier for a gio.Volume. The id is constructed
		as a "best effort" since we can not always uniquely identify
		volumes, especially audio- and data CDs are problematic.
		"""
		volume_id = volume.get_uuid()
		if volume_id : return volume_id
		
		volume_id = volume.get_identifier("uuid")
		if volume_id : return volume_id
		
		volume_id = volume.get_identifier("label")
		if volume_id : return volume_id
		
		volume_id = volume.get_name()
		if volume_id : return volume_id
		
		return "UNKNOWN"
		
	def add_storage_medium (self, medium_name):
		"""
		Mark storage medium  as available in the Zeitgeist DB
		"""
		# FIXME
		print "ADD", medium_name
		
	def remove_storage_medium (self, medium_name):
		"""
		Mark storage medium  as `not` available in the Zeitgeist DB
		"""
		# FIXME
		print "REMOVE", medium_name

class NMNetworkMonitor:
	"""
	Checks whether there is a funtioning network interface via
	NetworkManager (requires NM >= 0.8).
	See http://projects.gnome.org/NetworkManager/developers/spec-08.html
	"""
	NM_BUS_NAME = "org.freedesktop.NetworkManager"
	NM_IFACE = "org.freedesktop.NetworkManager"
	NM_OBJECT_PATH = "/org/freedesktop/NetworkManager"
	
	NM_STATE_UNKNOWN = 0
	NM_STATE_ASLEEP = 1
	NM_STATE_CONNECTING = 2
	NM_STATE_CONNECTED = 3
	NM_STATE_DISCONNECTED = 4
	
	def __init__ (self, on_network_up, on_network_down):
		log.debug("Creating NetworkManager network monitor")
		if not callable(on_network_up):
			raise TypeError((
				"First argument to NMNetworkMonitor constructor "
				"must be callable, found %s" % on_network_up))
		if not callable(on_network_down):
			raise TypeError((
				"Second argument to NMNetworkMonitor constructor "
				"must be callable, found %s" % on_network_up))
		
		self._up = on_network_up
		self._down = on_network_down
		
		proxy = dbus.SystemBus().get_object(NetworkMonitor.NM_BUS_NAME,
		                                    NetworkMonitor.NM_OBJECT_PATH)
		self._props = dbus.Interface(proxy, dbus.PROPERTIES_IFACE)
		self._nm = dbus.Interface(proxy, NetworkMonitor.NM_IFACE)
		self._nm.connect_to_signal("StateChanged", self._on_state_changed)
		
		# Register the initial state
		state = self._props.Get(NetworkMonitor.NM_IFACE, "State")
		self._on_state_changed(state)
		
	def _on_state_changed(self, state):
		log.debug("NetworkManager network state")
		if state == NetworkMonitor.NM_STATE_CONNECTED:
			self._up ()
		else:
			self._down()

class ConnmanNetworkMonitor:
	"""
	Checks whether there is a funtioning network interface via Connman
	"""
	CM_BUS_NAME = "net.connman"
	CM_IFACE = "net.connman.Manager"
	CM_OBJECT_PATH = "/"
	
	def __init__ (self, on_network_up, on_network_down):
		log.debug("Creating Connman network monitor")
		if not callable(on_network_up):
			raise TypeError((
				"First argument to ConnmanNetworkMonitor constructor "
				"must be callable, found %s" % on_network_up))
		if not callable(on_network_down):
			raise TypeError((
				"Second argument to ConnmanNetworkMonitor constructor "
				"must be callable, found %s" % on_network_up))
		
		self._up = on_network_up
		self._down = on_network_down
		
		proxy = dbus.SystemBus().get_object(ConnmanNetworkMonitor.CM_BUS_NAME,
		                                    ConnmanNetworkMonitor.CM_OBJECT_PATH)
		self._cm = dbus.Interface(proxy, ConnmanNetworkMonitor.CM_IFACE)
		self._cm.connect_to_signal("StateChanged", self._on_state_changed)
		#
		# ^^ There is a bug in some Connman versions causing it to not emit the
		#    net.connman.Manager.StateChanged signal. We take our chances this
		#    instance is working properly :-)
		#

		
		# Register the initial state
		state = self._cm.GetState()
		self._on_state_changed(state)
		
	def _on_state_changed(self, state):
		log.debug("Connman network state is '%s'" % state)
		if state == "online":
			self._up ()
		else:
			self._down()
