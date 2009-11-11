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
from zeitgeist.dbusutils import DBusInterface
from _zeitgeist.singleton import SingletonApplication

_engine = get_default_engine()

DBUS_INTERFACE = DBusInterface.INTERFACE_NAME
SIG_EVENT = "asaasay"

class RemoteInterface(SingletonApplication):
	
	# Initialization
	
	def __init__(self, start_dbus=True, mainloop=None):
		SingletonApplication.__init__(self)
		self._mainloop = mainloop
	
	# Reading stuff
	
	@dbus.service.method(DBUS_INTERFACE,
						in_signature="au", out_signature="a("+SIG_EVENT+")")
	def GetEvents(self, event_seqnums):
		events = _engine.get_events(event_seqnums)
		try:
			# If the list contains a None we have a missing event,
			# meaning that the client requested a non-existing event
			offset = events.index(None)
			raise KeyError("No event with id %s" % event_seqnums[offset])
		except ValueError:
			# This is what we want, it means that there are no
			# holes in the list
			return events
	
	@dbus.service.method(DBUS_INTERFACE,
						in_signature="(ii)a(asas)uuu", out_signature="a("+SIG_EVENT+")")
	def FindEventIds(self, time_range, event_templates, storage_state,
			max_events, order):
		"""Search for items which match different criterias
		
		:param time_range: two timestamps defining the timerange for the query
		:type time_range: tuple of integers
		:param event_templates: template with which the returned events should match
		:type event_templates: array of templates
		:param storage_state: whether the item is currently known to be available
		:type storage_state: unsigned integer
		:param max_events: maximal amount of returned events
		:type max_events: unsigned integer
		:param order: unsigned integer representing a :ref:`sorting-label`
		:type order: unsigned integer
		:returns: list of items
		:rtype: list of tuples presenting an :ref:`item-label`
		"""
		return _engine.find_eventids(time_range, event_templates, storage_state,
			max_events, order)
	
	@dbus.service.method(DBUS_INTERFACE,
						in_signature="iiaa{sv}", out_signature="a(si)")
	def FindApplications(self, min_timestamp, max_timestamp, filters):
		"""This method takes a subset of the parameters from ``FindEvents()``
		and returns the path to the .desktop file of the applications which
		were used for the matching events.
		
		:param min_timestamp: search for application beginning after this timestamp
		:type min_timestamp: integer
		:param max_timestamp: search for applications beginning before this timestamp;
			``max_timestamp`` equals ``0`` means indefinite time
		:type max_timestamp: integer
		:param filters: list of filter, multiple filters are connected by an ``OR`` condition
		:type filters: list of tuples presenting a :ref:`filter-label`
		:returns: list of tuples containing the path to a .desktop file and the amount of matches for it
		:rtype: list of tuples containing a string and an integer
		"""
		return _engine.find_events(min_timestamp, max_timestamp, 0, False,
			u"event", filters, return_mode=2)
	
	@dbus.service.method(DBUS_INTERFACE,
						in_signature="iisaa{sv}", out_signature="i")
	def CountEvents(self, min_timestamp, max_timestamp, mode, filters):
		"""This method takes a subset of the parameters from ``FindEvents()``
		and returns the amount of results a ``FindEvents()`` call with the
		same parameter would yield if the maximal amount of items to return
		isn't limited.
		
		:param min_timestamp: search for events beginning after this timestamp
		:type min_timestamp: integer
		:param max_timestamp: search for events beginning before this timestamp;
			``max_timestamp`` equals ``0`` means indefinite time
		:type max_timestamp: integer
		:param mode: The first mode returns all events, the second and third
			ones only return repeated items once.
		:type mode: string, either ``event``, ``item`` or ``mostused``
		:param filters: list of filter, multiple filters are connected by an ``OR`` condition
		:type filters: list of tuples presenting a :ref:`filter-label`
		:returns: list of items
		:rtype: list of tuples presenting an :ref:`item-label`
		"""
		return _engine.find_events(min_timestamp, max_timestamp, 0, True,
			mode, filters, return_mode=1)
	
	@dbus.service.method(DBUS_INTERFACE,
						in_signature="s", out_signature="i")
	def GetLastInsertionDate(self, application):
		"""Returns the timestamp of the last item which was inserted
		related to the given ``application``. If there is no such record,
		0 is returned.
		
		:param application: application to query for
		:type application: string
		:returns: timestamp of last insertion date
		:rtype: integer
		"""
		return _engine.get_last_insertion_date(application)

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
	
	#@dbus.service.method(DBUS_INTERFACE,
	#					in_signature=SIG_EVENT, out_signature="")
	#def UpdateItems(self, item_list):
	#	"""Update items in the database
	#	
	#	:param item_list: list of items to be inserted in the database
	#	:type item_list: list of tuples presenting an :ref:`item-label`
	#	"""
	#	result = _engine.update_items(item_list)
	#	self.EventsChanged(("modified", result))
	
	@dbus.service.method(DBUS_INTERFACE, in_signature="au", out_signature="")
	def DeleteEvents(self, ids):
		"""Delete items from the database
		
		:param ids: list of event ids obtained, for example, by calling
		    FindEventIds()
		:type ids: list of integers
		"""
		_engine.delete_events(event_templates)

	@dbus.service.method(DBUS_INTERFACE, in_signature="", out_signature="")
	def DeleteLog(self):
		_engine.delete_log()
	
	# Signals and signal emitters
	
	@dbus.service.signal(DBUS_INTERFACE,
						signature="(sav)")
	def EventsChanged(self, value):
		"""This Signal is emitted whenever one or more items have been changed
		
		It contains a tuple, where the first item is one of `added`,
		`modified` and `deleted`. If the first item is `added` or `modified`
		the second item is a list of :ref:`event-label` and a dict of
		:ref:`item-label`, otherwise it is a list of uris.
		
		:returns: added and modified events/items and URIs of deleted items
		:rtype: list of dictionaries
		"""
		return value
	
	# Commands
	
	@dbus.service.method(DBUS_INTERFACE)
	def Quit(self):
		"""Terminate the running RemoteInterface process; use with caution,
		this action must only be triggered with the user's explicit consent,
		as it will affect all application using Zeitgeist"""
		if self._mainloop:
			self._mainloop.quit()
