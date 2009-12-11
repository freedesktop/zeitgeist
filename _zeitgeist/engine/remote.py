# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
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
import dbus.service
import logging

from zeitgeist.datamodel import Event, Subject, TimeRange, StorageState, ResultType, NULL_EVENT
from _zeitgeist.engine import get_default_engine
from _zeitgeist.engine.notify import MonitorManager
from zeitgeist.client import ZeitgeistDBusInterface
from _zeitgeist.singleton import SingletonApplication

_engine = get_default_engine()

DBUS_INTERFACE = ZeitgeistDBusInterface.INTERFACE_NAME
SIG_EVENT = "asaasay"

class RemoteInterface(SingletonApplication):
	
	_dbus_properties = {
		"version": property(lambda self: (0, 2, 99)),
	}
	
	# Initialization
	
	def __init__(self, start_dbus=True, mainloop=None):
		SingletonApplication.__init__(self)
		self._mainloop = mainloop
		self._notifications = MonitorManager()
	
	# Reading stuff
	
	@dbus.service.method(DBUS_INTERFACE,
						in_signature="au", out_signature="a("+SIG_EVENT+")")
	def GetEvents(self, event_ids):
		"""Get full event data for a set of event ids
		
		:param event_ids: An array of event ids. Fx. obtained by calling
		    :meth:`FindEventIds`
		:type event_ids: Array of unsigned 32 bit integers.
		    DBus signature au
		:returns: Full event data for all the requested ids. The
		   event data can be conveniently converted into a list of
		   :class:`Event` instances by calling *events = map(Event, result)*
		:rtype: A list of serialized events. DBus signature a(asaasay).
		"""
		events = _engine.get_events(event_ids)
		for event in events:
			if event is not None:
				event._make_dbus_sendable()
		events = [NULL_EVENT if event is None else event for event in events]
		return events
	
	@dbus.service.method(DBUS_INTERFACE,
						in_signature="s", out_signature="as")
	def GetMostUsedWithSubject(self, uri):
		"""Get the URI of the :class:`Subject`s most frequently used together
		with the indicated URI.
		
		:param uri: URI of the :class:`Subject` for which you want to find the
		   related items.
		:type uri: String.
		:returns: A variable number of URIs.
		:rtype: A list of strings.
		"""
		return _engine.get_most_used_with_subject(uri)
	
	@dbus.service.method(DBUS_INTERFACE,
						in_signature="(xx)a("+SIG_EVENT+")uuu", out_signature="au")
	def FindEventIds(self, time_range, event_templates, storage_state,
			num_events, result_type):
		"""Search for events matching a given set of templates and return the ids of matching events.
		Use :meth:`GetEvents` passing in the returned ids to look up
		the full event data.
		
		The matching is done where unset fields in the templates
		are treated as wildcards. If a template has more than one
		subject then events will match the template if any one of their
		subjects match any one of the subject templates.
		
		:param time_range: two timestamps defining the timerange for
		    the query. When using the Python bindings for Zeitgeist you
		    may pass a :class:`TimeRange <zeitgeist.datamodel.TimeRange>`
		    instance directly to this method
		:type time_range: tuple of 64 bit integers. DBus signature (xx)
		:param event_templates: An array of event templates which the
		    returned events should match at least one of.
		    When using the Python bindings for Zeitgeist you may pass
		    a list of  :class:`Event <zeitgeist.datamodel.Event>`
		    instances directly to this method.
		:type event_templates: array of events. DBus signature a(asaasay)
		:param storage_state: whether the item is currently known to be available. The list of possible values is enumerated in :class:`StorageState <zeitgeist.datamodel.StorageState>` class
		:type storage_state: unsigned integer
		:param num_events: maximal amount of returned events
		:type num_events: unsigned integer
		:param order: unsigned integer representing a :class:`result type <zeitgeist.datamodel.ResultType>`
		:type order: unsigned integer
		:returns: An array containing the ids of all matching events,
		    up to a maximum of *num_events* events. Sorted and grouped
		    as defined by the *result_type* parameter.
		:rtype: Array of unsigned 32 bit integers
		"""
		time_range = TimeRange(time_range[0], time_range[1])
		event_templates = map(Event, event_templates)
		return _engine.find_eventids(time_range, event_templates, storage_state, num_events, result_type)

	# Writing stuff
	
	@dbus.service.method(DBUS_INTERFACE,
						in_signature="a("+SIG_EVENT+")", out_signature="au")
	def InsertEvents(self, events):
		"""Inserts events into the log. Returns an array containing the ids of the inserted events
		
		Any monitors with matching templates will get notified about
		the insertion. Note that the monitors are notified *after* the
		events have been inserted.
		
		:param events: List of events to be inserted in the log.
		    If you are using the Python bindings you may pass
		    :class:`Event <zeitgeist.datamodel.Event>` instances
		    directly to this method
		:returns: An array containing the event ids of the inserted
		    events. In case the any of the events where already logged
		    the id of the existing event will be returned
		:rtype: Array of unsigned 32 bits integers. DBus signature au.
		"""
		if not events : return []
		events = map(Event, events)
		event_ids = _engine.insert_events(events)
		
		_events = []
		min_stamp = events[0].timestamp
		max_stamp = min_stamp
		for ev, ev_id in zip(events, event_ids):
			if not ev_id:
				# event has not been inserted because of an error or 
				# because of being blocked by an extension
				# this is why we do not notify clients about this event
				continue
			_ev = Event(ev)
			_ev[0][Event.Id] = ev_id
			_events.append(_ev)
			min_stamp = min(min_stamp, _ev.timestamp)
			max_stamp = max(max_stamp, _ev.timestamp)
		self._notifications.notify_insert(TimeRange(min_stamp, max_stamp), _events)
		
		return event_ids
	
	@dbus.service.method(DBUS_INTERFACE, in_signature="au", out_signature="")
	def DeleteEvents(self, event_ids):
		"""Delete a set of events from the log given their ids
		
		:param event_ids: list of event ids obtained, for example, by calling
		    :meth:`FindEventIds`
		:type ids: list of integers
		"""
		# FIXME: Notify monitors - how do we do this? //kamstrup
		min_stamp, max_stamp = _engine.delete_events(event_ids)
		self._notifications.notify_delete(TimeRange(min_stamp, max_stamp), event_ids)

	@dbus.service.method(DBUS_INTERFACE, in_signature="", out_signature="")
	def DeleteLog(self):
		"""Delete the log file and all its content
		
		This method is used to delete the entire log file and all its
		content in one go. To delete specific subsets use
		:meth:`FindEventIds` combined with :meth:`DeleteEvents`.
		"""
		_engine.delete_log()
        
        @dbus.service.method(DBUS_INTERFACE)
	def Quit(self):
		"""Terminate the running Zeitgeist engine process; use with caution,
		this action must only be triggered with the user's explicit consent,
		as it will affect all applications using Zeitgeist"""
		if self._mainloop:
			self._mainloop.quit()
	
	# Properties interface

	@dbus.service.method(dbus_interface=dbus.PROPERTIES_IFACE,
						 in_signature="ss", out_signature="v")
	def Get(self, interface_name, property_name):
		try:
			return self._dbus_properties[property_name].fget(self)
		except KeyError, e:
			raise AttributeError(property_name)

	@dbus.service.method(dbus_interface=dbus.PROPERTIES_IFACE,
						 in_signature="ssv", out_signature="")
	def Set(self, interface_name, property_name, value):
		try:
			prop = self._dbus_properties[property_name].fset(self, value)
		except (KeyError, TypeError), e:
			raise AttributeError(property_name)

	@dbus.service.method(dbus_interface=dbus.PROPERTIES_IFACE,
						 in_signature="s", out_signature="a{sv}")
	def GetAll(self, interface_name):
		return dict((k, v.fget(self)) for (k,v) in self._dbus_properties.items())
	
	# Notifications interface
	
	@dbus.service.method(DBUS_INTERFACE,
			in_signature="o(xx)a("+SIG_EVENT+")", sender_keyword="owner")
	def InstallMonitor(self, monitor_path, time_range, event_templates, owner=None):
		"""Register a client side monitor object to receive callbacks when events matching *time_range* and *event_templates* are inserted or deleted.
		
		The monitor object must implement the interface :ref:`org.gnome.zeitgeist.Monitor <org_gnome_zeitgeist_Monitor>`
		
		:param monitor_path: DBus object path to the client side monitor object. DBus signature o.
		:param time_range: A two-tuple with the time range monitored
		    events must fall within. Recall that time stamps are in
		    milliseconds since the Epoch. DBus signature (xx)
		:param event_templates: Event templates that events must match
		    in order to trigger the monitor. Just like :meth:`FindEventIds`.
		    DBus signature a(asaasay)
		"""
		event_templates = map(Event, event_templates)
		time_range = TimeRange(time_range[0], time_range[1])
		self._notifications.install_monitor(owner, monitor_path, time_range, event_templates)
	
	@dbus.service.method(DBUS_INTERFACE,
			in_signature="o", sender_keyword="owner")
	def RemoveMonitor(self, monitor_path, owner=None):
		"""Remove a monitor installed with :meth:`InstallMonitor`
		
		:param monitor_path: DBus object path of monitor to remove as
		    supplied to :meth:`InstallMonitor`.
		"""
		self._notifications.remove_monitor(owner, monitor_path)
