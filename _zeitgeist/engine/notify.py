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

import dbus

from _zeitgeist.engine.remote import make_dbus_sendable

class MonitorProxy (dbus.Interface):
	"""
	Connection to a org.gnome.zeitgeist.Monitor interface running on some
	client to the Zeitgeist engine.
	"""
	
	def __init__ (self, owner, monitor_path, event_templates):
		"""
		Create a new MonitorProxy for the unique DBus name *owner* on the
		path *monitor_path*. Note that the path points to an object
		living under *owner* and not necessarily inside the current
		process.
		"""
		bus = dbus.SessionBus()
		proxy = bus.get_object(owner, monitor_path)
		dbus.Interface.__init__(
				self,
				proxy,
				"org.gnome.zeitgeist.Monitor"
		)
		
		self._owner = owner
		self._path = monitor_path
		self._templates = event_templates
		self._iface = MonitorDBusInterface(owner, monitor_path)
	
	def get_owner (self) : return self._owner
	owner = property(get_owner)
	
	def get_path (self) : return self._path
	path = property(get_path)
	
	def __hash__ (self):
		return hash(Monitor.hash(self._owner, self._path))
	
	def matches (self, event):
		for tmpl in self._templates:
			if event.matches_template(tmpl) : return True
		return False
	
	def notify (self, events):
		self.Notify([make_dbus_sendable(ev) for ev in events])
	
	@staticmethod
	def hash(owner, path):
		return hash("%s#%s" % (owner, path))

class NotificationManager:
	
	def __init__ (self):
		self._monitors = {} # hash -> Monitor
		self._connections = {} # owner -> list of paths
		
		# Listen for disconnecting clients to clean up potential dangling monitors
		bus.SessionBus().add_signal_receiver ("NameOwnerChanged", self._name_owner_changed, arg2="")
	
	def install (self, monitor):
		if monitor in self._monitors[monitor]:
			raise KeyError("Monitor for %s already installed at path %s" % (monitor.owner, monitor.path))
		self._monitors[monitor] = monitor
		
		if not monitor.owner in self._connections:
			self._connections[owner] = [monitor.path]
		else:
			self._connections[owner].append(monitor.path)
	
	def remove (self, owner, monitor_path):
		mon = self._monitors.pop(Monitor.hash(owner, monitor_path))
		
		if not mon:
			raise KeyError("Unknown monitor %s for owner %s" % (monitor_path, owner))
		
		conn = self._connections[owner]
		if conn : conn.remove(monitor_path)
	
	def _name_owner_changed (self, owner, old, new):
		conn = self._connections.pop(owner)

		if not conn:
			return
		
		print "DEBUG: Disconnected %s" % old
		for path in conn:
			print "DEBUG: Removing ", owner, path
			self._monitors.pop(Monitor.hash(owner, path))
