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
import logging

from zeitgeist.datamodel import TimeRange

log = logging.getLogger("zeitgeist.notify")

class _MonitorProxy (dbus.Interface):
	"""
	Connection to a org.gnome.zeitgeist.Monitor interface running on some
	client to the Zeitgeist engine.
	"""
	
	def __init__ (self, owner, monitor_path, time_range, event_templates):
		"""
		Create a new MonitorProxy for the unique DBus name *owner* on the
		path *monitor_path*. Note that the path points to an object
		living under *owner* and not necessarily inside the current
		process.
		
		:param owner: Unique DBus name of the process owning the monitor
		:param monitor_path: The DBus object path to the monitor object
			in the client process
		:param time_range: a 
			:class:`TimeRange <zeitgeist.datamodel.TimeRange` instance
			the monitored events must lie within
		:param event_templates: List of event templates that any events
			must match in order to notify this monitor
		:type event_templates: list of
			:class:`Events <zeitgeist.datamodel.Event>`
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
		self._time_range = time_range
		self._templates = event_templates
	
	def __str__ (self):
		return "%s%s" % (self.owner, self.path)
	
	def get_owner (self) : return self._owner
	owner = property(get_owner, doc="Read only property with the unique DBus name of the process owning the monitor")
	
	def get_path (self) : return self._path
	path = property(get_path, doc="Read only property with the object path of the monitor in the process owning the monitor")
	
	def get_time_range (self) : return self._time_range
	time_range = property(get_time_range, doc="Read only property with matched :class:`TimeRange` of the monitor")
	
	def __hash__ (self):
		return hash(_MonitorProxy.hash(self._owner, self._path))
	
	def matches (self, event):
		"""
		Returns True of this monitor has a template matching *event*
		
		:param event: The event to check against the monitor's templates
		:type event: :class:`Event <zeitgeist.datamodel.Event>`
		"""
		if not event.in_time_range(self._time_range):
			return False
		
		if len(self._templates) == 0:
			return True
		
		for tmpl in self._templates:
			if event.matches_template(tmpl) : return True
		return False
	
	def notify_insert (self, time_range, events):
		"""
		Asynchronously notify the monitor that a collection of matching events has been inserted
		
		The events will *not* be filtered through the :meth:`matches`
		method. It is the responsability of the caller to do that.
		"""
		for ev in events : ev._make_dbus_sendable()
		self.NotifyInsert(time_range, events,
					reply_handler=self._notify_reply_handler,
					error_handler=self._notify_error_handler)
	
	def notify_delete (self, time_range, event_ids):
		"""
		Asynchronously notify the monitor that a collection of events has been deleted
		
		Only the event ids are passed back to the monitor. Note this
		method does not check that *time_range* is within the monitor's
		time range. That is the responsibility of the caller
		"""
		self.NotifyDelete(time_range, event_ids,
					reply_handler=self._notify_reply_handler,
					error_handler=self._notify_error_handler)
	
	@staticmethod
	def hash(owner, path):
		"""
		Calculate an integer uniquely identifying the monitor based on
		the DBus name of the owner and object path of the monitor itself
		"""
		return hash("%s#%s" % (owner, path))
	
	def _notify_reply_handler (self):
		"""
		Async reply handler for invoking Notify() over DBus
		"""
		pass
	
	def _notify_error_handler (self, error):
		"""
		Async error handler for invoking Notify() over DBus
		"""
		log.warn("Failed to deliver notification: %s" % error)
		
class MonitorManager:
	
	def __init__ (self):
		self._monitors = {} # hash -> Monitor
		self._connections = {} # owner -> list of paths
		
		# Listen for disconnecting clients to clean up potential dangling monitors
		dbus.SessionBus().add_signal_receiver (self._name_owner_changed,
											   signal_name="NameOwnerChanged",
											   dbus_interface=dbus.BUS_DAEMON_IFACE,
											   arg2="")
	
	def install_monitor (self, owner, monitor_path, time_range, event_templates):
		"""
		Install a :class:`MonitorProxy` and set it up to receive
		notifications when events are pushed into the :meth;`dispatch`
		method.
		
		Monitors will automatically be cleaned up if :const:`monitor.owner`
		disconnects from the bus. To manually remove a monitor call the
		:meth:`remove_monitor` on this object passing in
		:const:`monitor.owner` and :const:`monitor.path`.
		
		:param owner: Unique DBus name of the process owning the monitor
		:type owner: string
		:param monitor_path: The DBus object path for the monitor object
			in the client process
		:type monitor_path: String or :class:`dbus.ObjectPath`
		:param time_range: a 
			:class:`TimeRange <zeitgeist.datamodel.TimeRange` instance
			the monitored events must lie within
		:param event_templates: A list of
			:class:`Event <zeitgeist.datamodel.Event>` templates to match
		:returns: This method has no return value
		"""
		# Check that we don't already have the monitor, so we don't
		# needlesly set up a full dbus Proxy
		monitor_key = _MonitorProxy.hash(owner, monitor_path)
		if monitor_key in self._monitors:
			raise KeyError("Monitor for %s already installed at path %s" % (owner, monitor_path))
		
		monitor = _MonitorProxy(owner, monitor_path, time_range, event_templates)
		self._monitors[monitor_key] = monitor
		
		if not monitor.owner in self._connections:
			self._connections[owner] = set()
		
		self._connections[owner].add(monitor.path)
	
	def remove_monitor (self, owner, monitor_path):
		"""
		Remove an installed monitor.
		
		:param owner: Unique DBus name of the process owning the monitor
		:type owner: string
		:param monitor_path: The DBus object path for the monitor object
			in the client process
		:type monitor_path: String or :class:`dbus.ObjectPath`
		"""
		log.debug("Removing monitor %s%s", owner, monitor_path)
		mon = self._monitors.pop(_MonitorProxy.hash(owner, monitor_path))
		
		if not mon:
			raise KeyError("Unknown monitor %s for owner %s" % (monitor_path, owner))
		
		conn = self._connections[owner]
		if conn : conn.remove(monitor_path)
	
	def notify_insert (self, time_range, events):
		"""
		Send events to matching monitors.
		The monitors will only be notified about the events for which
		they have a matching template, ie. :meth:`MonitorProxy.matches`
		returns True.
		
		:param events: The events to check against the monitor templates
		:type events: list of :class:`Events <zeitgeist.datamodel.Event>`
		"""
		for mon in self._monitors.itervalues():
			log.debug("Checking monitor %s" % mon)
			matching_events = []
			
			for ev in events:
				if mon.matches(ev):
					matching_events.append(ev)
			
			if matching_events :
				log.debug("Notifying %s about %s insertions" % (mon, len(matching_events)))
				try:
					mon.notify_insert(time_range.intersect(mon.time_range), matching_events)
				except Exception:
					log.exception("Failed to notify monitor: %s" % mon)
	
	def notify_delete (self, time_range, event_ids):
		"""
		Notify monitors with matching time ranges that the events with the given ids have been deleted from the log
		
		:param time_range: A TimeRange instance that spans the deleted events
		:param event_ids: A list of event ids
		"""
		for mon in self._monitors.itervalues():
			log.debug("Checking monitor %s" % mon)
			intersecting_range = mon.time_range.intersect(time_range)
			
			if intersecting_range:
				log.debug("Notifying %s about %s deletions" % (mon, len(event_ids)))
				try:
					mon.notify_delete(intersecting_range, event_ids)
				except Exception:
					log.exception("Failed to notify monitor: %s" % mon)
		
	def _name_owner_changed (self, owner, old, new):
		"""
		Clean up monitors for processes disconnecting from the bus
		"""
		# Don't proceed if this is a disconnect of an unknown connection
		if not owner in self._connections :
			return
		
		conn = self._connections[owner]
		
		log.debug("Client disconnected %s" % owner)
		# we need to copy the conn set here, otherwise self.remove()
		# will possibly change size of self._connection during iteration
		# which results in a RuntimeError (thekorn)
		for path in conn.copy():
			self.remove_monitor(owner, path)
		
		self._connections.pop(owner)
	
