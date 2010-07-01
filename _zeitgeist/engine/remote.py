# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009-2010 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
# Copyright © 2009 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
# Copyright © 2010 Seif Lotfy <seif@lotfy.com>
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

from zeitgeist.datamodel import TimeRange, StorageState, ResultType, NULL_EVENT
from _zeitgeist.engine.datamodel import Event, Subject
from _zeitgeist.engine import get_engine
from _zeitgeist.engine.notify import MonitorManager
from _zeitgeist.engine import constants
from _zeitgeist.singleton import SingletonApplication

_engine = get_engine()

class RemoteInterface(SingletonApplication):
	"""
	Primary interface to the Zeitgeist engine. Used to update and query
	the log. It also provides means to listen for events matching certain
	criteria. All querying is heavily based around an
	"event template"-concept.
	
	The main log of the Zeitgeist engine has DBus object path
	:const:`/org/gnome/zeitgeist/log/activity` under the bus name
	:const:`org.gnome.zeitgeist.Engine`.
	"""
	_dbus_properties = {
		"version": property(lambda self: (0, 4, 0)),
	}
	
	# Initialization
	
	def __init__(self, start_dbus=True, mainloop=None):
		SingletonApplication.__init__(self)
		self._mainloop = mainloop
		self._notifications = MonitorManager()
	
	# Private methods
	
	def _make_events_sendable(self, events):
		for event in events:
			if event is not None:
				event._make_dbus_sendable()
		return [NULL_EVENT if event is None else event for event in events]
	
	# Reading stuff
	
	@dbus.service.method(constants.DBUS_INTERFACE,
						in_signature="au",
						out_signature="a("+constants.SIG_EVENT+")",
						sender_keyword="sender")
	def GetEvents(self, event_ids, sender):
		"""Get full event data for a set of event IDs
		
		Each event which is not found in the event log is represented
		by the `NULL_EVENT` struct in the resulting array.
		
		:param event_ids: An array of event IDs. Fx. obtained by calling
			:meth:`FindEventIds`
		:type event_ids: Array of unsigned 32 bit integers.
			DBus signature au
		:returns: Full event data for all the requested IDs. The
		   event data can be conveniently converted into a list of
		   :class:`Event` instances by calling *events = map(Event.new_for_struct, result)*
		:rtype: A list of serialized events. DBus signature a(asaasay).
		"""
		return self._make_events_sendable(_engine.get_events(ids=event_ids,
		    sender=sender))
	
	@dbus.service.method(constants.DBUS_INTERFACE,
						in_signature="(xx)a("+constants.SIG_EVENT+")a("+constants.SIG_EVENT+")uuu",
						out_signature="as")
	def FindRelatedUris(self, time_range, event_templates,
		result_event_templates, storage_state, num_events, result_type):
		"""Warning: This API is EXPERIMENTAL and is not fully supported yet.
		
		Get a list of URIs of subjects which frequently occur together
		with events matching `event_templates` within `time_range`.
		The resulting URIs must occur as subjects of events matching
		`result_event_templates` and have storage state
		`storage_state`.
		
		:param time_range: two timestamps defining the timerange for
			the query. When using the Python bindings for Zeitgeist you
			may pass a :class:`TimeRange <zeitgeist.datamodel.TimeRange>`
			instance directly to this method.
		:type time_range: tuple of 64 bit integers,
			DBus signature :const:`(xx)`
		:param event_templates: An array of event templates
			which you want URIs that relate to.
			When using the Python bindings for Zeitgeist you may pass
			a list of  :class:`Event <zeitgeist.datamodel.Event>`
			instances directly to this method.
		:type event_templates: array of events,
			DBus signature :const:`a(asaasay)`
		:param result_event_templates: An array of event templates which
			the returned URIs must occur as subjects of.
			When using the Python bindings for Zeitgeist you may pass
			a list of  :class:`Event <zeitgeist.datamodel.Event>`
			instances directly to this method.
		:type result_event_templates: array of events,
			DBus signature :const:`a(asaasay)`
		:param storage_state: whether the item is currently known to be
		   available. The list of possible values is enumerated in the
		   :class:`StorageState <zeitgeist.datamodel.StorageState>` class
		:type storage_state: unsigned 32 bit integer, DBus signature :const:`u`
		:param num_events: maximal amount of returned events
		:type num_events: unsigned integer
		:param result_type: unsigned integer 0 for relevancy 1 for recency
		:type order: unsigned integer
		:returns: A list of URIs matching the described criteria
		:rtype: An array of strings, DBus signature :const:`as`.
		"""
		event_templates = map(Event, event_templates)
		return _engine.find_related_uris(time_range, event_templates,
			result_event_templates, storage_state, num_events, result_type)
	
	@dbus.service.method(constants.DBUS_INTERFACE,
						in_signature="(xx)a("+constants.SIG_EVENT+")uuu",
						out_signature="au")
	def FindEventIds(self, time_range, event_templates, storage_state,
			num_events, result_type):
		"""Search for events matching a given set of templates and return
		the IDs of matching events.
		
		Use :meth:`GetEvents` passing in the returned IDs to look up
		the full event data.
		
		The matching is done where unset fields in the templates
		are treated as wildcards. If a template has more than one
		subject then events will match the template if any one of their
		subjects match any one of the subject templates.
		
		The fields uri, interpretation, manifestation, origin, and mimetype
		can be prepended with an exclamation mark '!' in order to negate
		the matching.
		
		The fields uri, origin, and mimetype can be prepended with an
		asterisk '*' in order to do truncated matching.
		
		This method is intended for queries potentially returning a
		large result set. It is especially useful in cases where only
		a portion of the results are to be displayed at the same time
		(eg., by using paging or dynamic scrollbars), as by holding a
		list of IDs you keep a stable ordering and you can ask for the
		details associated to them in batches, when you need them. For queries
		yielding a small amount of results, or where you need the information
		about all results at once no matter how many of them there are,
		see :meth:`FindEvents`.
		
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
		:param storage_state: whether the item is currently known to be
			available. The list of possible values is enumerated in
			:class:`StorageState <zeitgeist.datamodel.StorageState>` class
		:type storage_state: unsigned integer
		:param num_events: maximal amount of returned events
		:type num_events: unsigned integer
		:param order: unsigned integer representing
			a :class:`result type <zeitgeist.datamodel.ResultType>`
		:type order: unsigned integer
		:returns: An array containing the IDs of all matching events,
			up to a maximum of *num_events* events. Sorted and grouped
			as defined by the *result_type* parameter.
		:rtype: Array of unsigned 32 bit integers
		"""
		time_range = TimeRange(time_range[0], time_range[1])
		event_templates = map(Event, event_templates)
		return _engine.find_eventids(time_range, event_templates, storage_state,
			num_events, result_type)

	@dbus.service.method(constants.DBUS_INTERFACE,
						in_signature="(xx)a("+constants.SIG_EVENT+")uuu",
						out_signature="a("+constants.SIG_EVENT+")",
						sender_keyword="sender")
	def FindEvents(self, time_range, event_templates, storage_state,
			num_events, result_type, sender):
		"""Get events matching a given set of templates.
		
		The matching is done where unset fields in the templates
		are treated as wildcards. If a template has more than one
		subject then events will match the template if any one of their
		subjects match any one of the subject templates.
		
		The fields uri, interpretation, manifestation, origin, and mimetype
		can be prepended with an exclamation mark '!' in order to negate
		the matching.
		
		The fields uri, origin, and mimetype can be prepended with an
		asterisk '*' in order to do truncated matching.
		
		In case you need to do a query yielding a large (or unpredictable)
		result set and you only want to show some of the results at the
		same time (eg., by paging them), use :meth:`FindEventIds`.
		
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
		:param storage_state: whether the item is currently known to be
			available. The list of possible values is enumerated in
			:class:`StorageState <zeitgeist.datamodel.StorageState>` class
		:type storage_state: unsigned integer
		:param num_events: maximal amount of returned events
		:type num_events: unsigned integer
		:param order: unsigned integer representing
			a :class:`result type <zeitgeist.datamodel.ResultType>`
		:type order: unsigned integer
		:returns: Full event data for all the requested IDs, up to a maximum
			of *num_events* events, sorted and grouped as defined by the
			*result_type* parameter. The event data can be conveniently
			converted into a list of :class:`Event` instances by calling
			*events = map(Event.new_for_struct, result)*
		:rtype: A list of serialized events. DBus signature a(asaasay).
		"""
		time_range = TimeRange(time_range[0], time_range[1])
		event_templates = map(Event, event_templates)
		return self._make_events_sendable(_engine.find_events(time_range,
			event_templates, storage_state, num_events, result_type, sender))

	# Writing stuff
	
	@dbus.service.method(constants.DBUS_INTERFACE,
						in_signature="a("+constants.SIG_EVENT+")",
						out_signature="au",
						sender_keyword="sender")
	def InsertEvents(self, events, sender):
		"""Inserts events into the log. Returns an array containing the IDs
		of the inserted events
		
		Each event which failed to be inserted into the log (either by
		being blocked or because of an error) will be represented by `0`
		in the resulting array.
		
		One way events may end up being blocked is if they match any
		of the :ref:`blacklist templates <org_gnome_zeitgeist_Blacklist>`.
		
		Any monitors with matching templates will get notified about
		the insertion. Note that the monitors are notified *after* the
		events have been inserted.
		
		:param events: List of events to be inserted in the log.
			If you are using the Python bindings you may pass
			:class:`Event <zeitgeist.datamodel.Event>` instances
			directly to this method
		:returns: An array containing the event IDs of the inserted
			events. In case any of the events where already logged,
			the ID of the existing event will be returned. `0` as ID
			indicates a failed insert into the log.
		:rtype: Array of unsigned 32 bits integers. DBus signature au.
		"""
		if not events : return []
		events = map(Event, events)
		event_ids = _engine.insert_events(events, sender)
		
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
	
	@dbus.service.method(constants.DBUS_INTERFACE,
	                     in_signature="au",
	                     out_signature="",
	                     sender_keyword="sender")
	def DeleteEvents(self, event_ids, sender):
		"""Delete a set of events from the log given their IDs
		
		:param event_ids: list of event IDs obtained, for example, by calling
			:meth:`FindEventIds`
		:type event_ids: list of integers
		"""
		# FIXME: Notify monitors - how do we do this? //kamstrup
		timestamps = _engine.delete_events(event_ids, sender=sender)
		if timestamps:
			# We need to check the return value, as the events could already
			# have been deleted before or the IDs might even have been invalid.
			self._notifications.notify_delete(
			    TimeRange(timestamps[0], timestamps[1]), event_ids)

	@dbus.service.method(constants.DBUS_INTERFACE, in_signature="", out_signature="")
	def DeleteLog(self):
		"""Delete the log file and all its content
		
		This method is used to delete the entire log file and all its
		content in one go. To delete specific subsets use
		:meth:`FindEventIds` combined with :meth:`DeleteEvents`.
		"""
		_engine.delete_log()
	
	@dbus.service.method(constants.DBUS_INTERFACE)
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
	
	@dbus.service.method(constants.DBUS_INTERFACE,
			in_signature="o(xx)a("+constants.SIG_EVENT+")", sender_keyword="owner")
	def InstallMonitor(self, monitor_path, time_range, event_templates, owner=None):
		"""Register a client side monitor object to receive callbacks when
		events matching *time_range* and *event_templates* are inserted or
		deleted.
		
		The monitor object must implement the interface :ref:`org.gnome.zeitgeist.Monitor <org_gnome_zeitgeist_Monitor>`
		
		The monitor templates are matched exactly like described in
		:meth:`FindEventIds`.
		
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
	
	@dbus.service.method(constants.DBUS_INTERFACE,
			in_signature="o", sender_keyword="owner")
	def RemoveMonitor(self, monitor_path, owner=None):
		"""Remove a monitor installed with :meth:`InstallMonitor`
		
		:param monitor_path: DBus object path of monitor to remove as
			supplied to :meth:`InstallMonitor`.
		"""
		self._notifications.remove_monitor(owner, monitor_path)
