# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
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

from _zeitgeist.engine import get_default_engine
from zeitgeist.client import ZeitgeistDBusInterface
from _zeitgeist.singleton import SingletonApplication

_engine = get_default_engine()

DBUS_INTERFACE = ZeitgeistDBusInterface.INTERFACE_NAME
SIG_EVENT = "asaasay"

def special_str(obj):
	""" Return a string representation of obj
	If obj is None, return an empty string.
	"""
	return unicode(obj) if obj is not None else ""

def make_dbus_sendable(event):
	for n, value in enumerate(event[0]):
		event[0][n] = special_str(value)
	for subject in event[1]:
		for n, value in enumerate(subject):
			subject[n] = special_str(value)
	event[2] = special_str(event[2])
	return event

class RemoteInterface(SingletonApplication):
		
	_dbus_properties = {
		"version": property(lambda self: (0, 2, 99)),
	}
	
	# Initialization
	
	def __init__(self, start_dbus=True, mainloop=None):
		SingletonApplication.__init__(self)
		self._mainloop = mainloop
	
	# Reading stuff
	
	@dbus.service.method(DBUS_INTERFACE,
						in_signature="au", out_signature="a("+SIG_EVENT+")")
	def GetEvents(self, event_ids):
		"""Get full event data for a set of event ids
		
		:param event_ids: An array of event ids. Fx. obtained by calling
		    FindEventIds()
		:type event_ids: Array of unsigned 32 bit integers.
		    DBus signature au
		:returns: Full event data for all the requested ids
		:rtype: A list of Event objects. DBus signature a(asaasay).
		"""
		events = _engine.get_events(event_ids)
		try:
			# If the list contains a None we have a missing event,
			# meaning that the client requested a non-existing event
			offset = events.index(None)
			raise KeyError("No event with id %s" % event_ids[offset])
		except ValueError:
			# This is what we want, it means that there are no
			# holes in the list
			return [make_dbus_sendable(event) for event in events]
	
	@dbus.service.method(DBUS_INTERFACE,
						in_signature="(xx)a("+SIG_EVENT+")uuu", out_signature="au")
	def FindEventIds(self, time_range, event_templates, storage_state,
			num_events, result_type):
		"""Search for events which match different criterias and return the ids of matching events
		
		:param time_range: two timestamps defining the timerange for the query
		:type time_range: tuple of 64 bit integers. DBus signature (xx)
		:param event_templates: An array of event templates which the
		    returned events should match at least one of. Unset fields
		    in the templates (empty strings) are matched as wildcards.
		    If a template has more than one subject then events will
		    match the template if any one of their subjects match any
		    one of the subject templates.
		:type event_templates: array of events. DBus signature a(asaasay).
		   When using the Python bindings you pass Event objects directly
		   to this method 
		:param storage_state: whether the item is currently known to be available
		:type storage_state: unsigned integer
		:param num_events: maximal amount of returned events
		:type num_events: unsigned integer
		:param order: unsigned integer representing a :ref:`sorting-label`
		:type order: unsigned integer
		:returns: list of items
		:rtype: list of tuples presenting an :ref:`item-label`
		"""		
		return _engine.find_eventids(time_range, event_templates, storage_state, num_events, result_type)

	# Writing stuff
	
	@dbus.service.method(DBUS_INTERFACE,
						in_signature="a("+SIG_EVENT+")", out_signature="au")
	def InsertEvents(self, events):
		"""Inserts events into the database. Returns the amount of sucessfully
		inserted events
		
		:param events: list of events to be inserted in the database
		:type events: list of dicts presenting an :ref:`event-label`
		:param items: list of corresponding items
		:type items: dict of dicts presenting an :ref:`item-label`
		:param annotations: list of annotations to be passed to SetAnnotations
		:type annotation: list of dicts presenting an :ref:`annotation-label`
		:returns: a positive value on success, ``0`` otherwise
		:rtype: Integer
		"""
		return _engine.insert_events(events)
	
	@dbus.service.method(DBUS_INTERFACE, in_signature="au", out_signature="")
	def DeleteEvents(self, ids):
		"""Delete a set of events from the log given their ids
		
		:param ids: list of event ids obtained, for example, by calling
		    FindEventIds()
		:type ids: list of integers
		"""
		_engine.delete_events(ids)

	@dbus.service.method(DBUS_INTERFACE, in_signature="", out_signature="")
	def DeleteLog(self):
		"""Delete the log file and all its content
		
		This method is used to delete the entire log file and all its
		content in one go. To delete specific subsets use FIndEventIds()
		and DeleteEvents().
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
	
