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

def special_str(obj):
	""" returns a string representation of an object
	if obj is None returns an empty string.
	"""
	if obj is None:
		return ""
	return str(obj)
	
def make_dbus_sendable(event):
	for n, value in enumerate(event[0]):
		event[0][n] = special_str(value)
	for subject in event[1]:
		for n, value in enumerate(subject):
			subject[n] = special_str(value)
	event[2] = special_str(event[2])
	return event

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
			return [make_dbus_sendable(event) for event in events]
	
	@dbus.service.method(DBUS_INTERFACE,
						in_signature="(ii)a(asas)uuu", out_signature="au")
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
		if storage_state:
			raise NotImplementedError
		return _engine.find_eventids(time_range, event_templates, storage_state,
			max_events, order)
	
	# FIXME: Do we want this or let people use
	# GetEvents(FindEventIds(limit=1,sorting=desc)).timestamp
	#   -- RainCT
	@dbus.service.method(DBUS_INTERFACE,
						in_signature="s", out_signature="u")
	def GetHighestTimestampForActor(self, actor):
		"""Returns the timestamp of the last item which was inserted
		related to the given ``actor``. If there is no such record,
		0 is returned.
		
		:param actor: actor to query for
		:type actor: string
		:returns: timestamp of the last event with that actor
		:rtype: integer
		"""
		return _engine.get_highest_timestamp_for_actor(actor)

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
		_engine.delete_events(ids)

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
