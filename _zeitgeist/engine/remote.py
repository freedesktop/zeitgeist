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
SIG_EVENTS = "aa{sv}a{sa{sv}}"

class RemoteInterface(SingletonApplication):
		
	_dbus_properties = {
		"version": property(lambda self: (0, 3, 0)),
	}
	
	# Initialization
	
	def __init__(self, start_dbus=True, mainloop=None):
		SingletonApplication.__init__(self)
		self._mainloop = mainloop
	
	# Reading stuff
	
	@dbus.service.method(DBUS_INTERFACE,
						in_signature="as", out_signature="("+SIG_EVENTS+")")
	def GetItems(self, uris):
		"""Get items by URI
		
		:param uris: list of uris
		:type uris: list of strings
		:returns: list of items
		:rtype: list of tuples presenting an :ref:`item-label`
		"""
		return _engine.get_items(uris)
	
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
						in_signature="iiis", out_signature="a(si)")
	def GetTags(self, min_timestamp, max_timestamp, limit, name_filter):
		"""Returns a list containing tuples with the name and the number of
		occurencies of the tags matching ``name_filter``, or all existing
		tags in case it's empty, sorted from most used to least used. ``amount``
		can base used to limit the amount of results.
		
		Use ``min_timestamp`` and ``max_timestamp`` to limit the time frames you
		want to consider.
		
		:param min_timestamp:
		:type min_timestamp: Integer
		:param max_timestamp:
		:type max_timestamp: Integer
		:param name_filter: 
		:type name_filter: string
		:param limit: max amount of returned elements, ``limit`` equals ``0``
			means the result not beeing limited
		:type amount: integer
		:returns: list of tuple containing the name and number of occurencies
		:rtype: list of tuples
		"""
		return _engine.get_tags(min_timestamp, max_timestamp, limit, name_filter)
	
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
	
	@dbus.service.method(DBUS_INTERFACE,
						in_signature="", out_signature="as")
	def GetTypes(self):
		"""Returns a list of all different types in the database.
		
		:returns: list of types
		:rtype: list of strings
	   	"""
		return _engine.get_types()
	
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
						in_signature="aa{ss}", out_signature="i")
	def SetAnnotations(self, annotations_list):
		"""Inserts annotations into the database.
		
		:param annotations_list: list of annotations to be inserted into the database
		:type annotations_list: list of dicts presenting an :ref:`annotation-label`
		:returns: URIs of the successfully inserted annotations
		:rtype: list of strings
		"""
		result = _engine.set_annotations(annotations_list)
		#if result:
			#self.AnnotationsChanged(("created", result))
		return result
	
	#@dbus.service.method(DBUS_INTERFACE,
	#					in_signature=SIG_EVENTS, out_signature="")
	#def UpdateItems(self, item_list):
	#	"""Update items in the database
	#	
	#	:param item_list: list of items to be inserted in the database
	#	:type item_list: list of tuples presenting an :ref:`item-label`
	#	"""
	#	result = _engine.update_items(item_list)
	#	self.EventsChanged(("modified", result))
	
	@dbus.service.method(DBUS_INTERFACE,
						in_signature="as", out_signature="")
	def DeleteItems(self, uris):
		"""Delete items from the database
		
		:param uris: list of URIs representing an item
		:type uris: list of strings
		"""
		result = _engine.delete_items(uris)
		self.EventsChanged(("deleted", result))
        
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
	
	@dbus.service.signal(DBUS_INTERFACE)
	def EngineStart(self):
		"""This signal is emmitted once the engine successfully started and
		is ready to process requests
		"""
		return True
	
	@dbus.service.signal(DBUS_INTERFACE)
	def EngineExit(self):
		return True
	
	# Commands
	
	@dbus.service.method(DBUS_INTERFACE)
	def Quit(self):
		"""Terminate the running RemoteInterface process; use with caution,
		this action must only be triggered with the user's explicit consent,
		as it will affect all application using Zeitgeist"""
		if self._mainloop:
			self._mainloop.quit()
