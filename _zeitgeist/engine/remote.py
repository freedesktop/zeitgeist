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
SIG_EVENTS = "asaasay"

class RemoteInterface(SingletonApplication):
	
	# Initialization
	
	def __init__(self, start_dbus=True, mainloop=None):
		SingletonApplication.__init__(self)
		self._mainloop = mainloop
	
	# Reading stuff
	
	@dbus.service.method(DBUS_INTERFACE,
						in_signature="iiibsaa{sv}", out_signature="("+SIG_EVENTS+")")
	def FindEvents(self, min_timestamp, max_timestamp, limit,
			sorting_asc, mode, filters):
		"""Search for items which match different criterias
		
		:param min_timestamp: search for events beginning after this timestamp
		:type min_timestamp: integer
		:param max_timestamp: search for events beginning before this timestamp;
			``max_timestamp`` equals ``0`` means indefinite time
		:type max_timestamp: integer
		:param limit: limit the number of returned items;
			``limit`` equals ``0`` returns all matching items
		:type limit: integer
		:param sorting_asc: sort result in ascending order of timestamp, otherwise descending
		:type sorting_asc: boolean
		:param mode: The first mode returns all events, the second one only returns
			the last event when items are repeated and the ``mostused`` mode
			is like ``item`` but returns the results sorted by the number of
			events.
		:type mode: string, either ``event``, ``item`` or ``mostused``
		:param filters: list of filter, multiple filters are connected by an ``OR`` condition
		:type filters: list of tuples presenting a :ref:`filter-label`
		:returns: list of items
		:rtype: list of tuples presenting an :ref:`item-label`
		"""
		# filters is a list of dicts, where each dict can have the following items:
		#   name: <list> of <str>
		#   uri: <list> of <str>
		#   tags: <list> of <str>
		#   mimetypes: <list> of <str>
		#   source: <list> of <str>
		#   content: <list> of <str>
		#	application <list> of <str>
		#   bookmarked: <bool> (True means bookmarked items, and vice versa
		return _engine.find_events(min_timestamp, max_timestamp, limit,
			sorting_asc, mode, filters, False)
	
	@dbus.service.method("org.gnome.zeitgeist",
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
						in_signature=SIG_EVENTS+"aa{ss}", out_signature="i")
	def InsertEvents(self, events, items, annotations):
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
		result = _engine.insert_events(events, items, annotations)
		if result[0]:
			self.EventsChanged(("added", result[0], result[1]))
		return len(result[0])

	@dbus.service.method(DBUS_INTERFACE,
						in_signature="as", out_signature="")
	def DeleteEvents(self, uris):
		"""Delete items from the database
		
		:param uris: list of URIs representing an item
		:type uris: list of strings
		"""
		result = _engine.delete_items(uris)
		self.EventsChanged(("deleted", result))
	
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
