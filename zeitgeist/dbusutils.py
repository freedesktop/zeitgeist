# -.- encoding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
# Copyright © 2009 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
# Copyright © 2009 Markus Korn <thekorn@gmx.de>
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
import dbus.mainloop.glib
import logging
import os.path

from xml.dom.minidom import parseString as minidom_parse

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

class DBusInterface(dbus.Interface):
	""" Central DBus interface to the zeitgeist engine
	
	There doe not necessarily have to be one single instance of this
	interface class, but all instances should share the same state
	(like use the same bus and be connected to the same proxy). This is
	achieved by extending the `Borg Pattern` as described by Alex Martelli	
	"""
	__shared_state = {}
	
	INTERFACE_NAME = BUS_NAME = "org.gnome.zeitgeist"
	OBJECT_PATH = "/org/gnome/zeitgeist"
	
	@staticmethod
	def get_members(introspection_xml):
		"""Parses the xml context returned by Introspect() and returns
		a tuple, where the first item is a list of all methods and the
		second one a list of all signals for the related interface
		"""
		doc = minidom_parse(introspection_xml)
		nodes = doc.getElementsByTagName("signal")
		signals = [node.getAttribute("name") for node in nodes]
		nodes = doc.getElementsByTagName("method")
		methods = [node.getAttribute("name") for node in nodes]
		try:
			methods.remove("Introspect") # Introspect is not part of the API
		except ValueError:
			pass
		return methods, signals
	
	@classmethod
	def get_session_bus(cls):
		"""Returns the bus used by the interface.
		
		If there is no bus set, the '_bus' attribute is set to
		dbus.SessionBus() and returned
		"""
		return cls.__shared_state.setdefault("_bus", dbus.SessionBus())
	
	@classmethod
	def _get_proxy(cls):
		"""Returns the proxy instance used by the interface.
		
		If the current interface has no proxy object set, it tries to
		generate one. If this fails because no zeitgeist-daemon is
		running a RuntimeError will be raised
		"""
		try:
			return cls.__shared_state["proxy_object"]
		except KeyError, e:
			bus = cls.get_session_bus()
			try:
				cls.__shared_state["proxy_object"] = bus.get_object(
					cls.BUS_NAME,
					cls.OBJECT_PATH
				)
			except dbus.exceptions.DBusException, e:
				if e.get_dbus_name() == "org.freedesktop.DBus.Error.ServiceUnknown":
					raise RuntimeError(("Found no running instance of the "
						"Zeitgeist daemon: %s") % e.get_dbus_message())
				else:
					raise
			else:
				introspection_xml = cls.__shared_state["proxy_object"].Introspect()
				methods, signals = cls.get_members(introspection_xml)
				cls.__shared_state["__methods"] = methods
				cls.__shared_state["__signals"] = signals
			return cls.__shared_state["proxy_object"]
	
	@classmethod
	def connect(cls, signal, callback, arg0=None):
		"""Connect a callback to a signal of the current proxy instance """
		proxy = cls._get_proxy()
		if signal not in cls.__shared_state["__signals"]:
			raise TypeError("unknown signal name: %s" %signal)
		if arg0 is None:
			proxy.connect_to_signal(
				signal,
				callback,
				dbus_interface=cls.INTERFACE_NAME
			)
		else:
			# TODO: This is ugly and limited to 1 argument. Find a better
			# way to do it.
			proxy.connect_to_signal(
				signal,
				callback,
				dbus_interface=cls.INTERFACE_NAME,
				arg0=arg0
			)
			
	@classmethod
	def connect_exit(cls, callback):
		"""executes callback when the RemoteInterface exists"""
		bus = cls.get_session_bus()
		bus_obj = bus.get_object("org.freedesktop.DBus", "/org/freedesktop/DBus")
		bus_obj.connect_to_signal(
			"NameOwnerChanged",
			lambda *args: callback(),
			dbus_interface="org.freedesktop.DBus",
			arg0=cls.INTERFACE_NAME, #only match dying zeitgeist remote interfaces
			arg2="", #only match services with no new owner
		)
	
	def __init__(self):
		self.__dict__ = self.__shared_state
		proxy = self._get_proxy()
		dbus.Interface.__init__(
				self,
				proxy,
				self.BUS_NAME
		)

class EventDict(dict):
	""" A dict representing an event """
	
	# a dict of all possible keys of an event dict and the type of its
	# values and whether this item is required or not
	_ITEM_TYPE_MAP = {
		"timestamp": (int, True),
		"uri": (unicode, True),
		"text": (unicode, False),
		"source": (unicode, True),
		"content": (unicode, True),
		"mimetype": (unicode, True),
		"tags": (unicode, False),
		"comment": (unicode, False),
		"bookmark": (bool, False),
		"use": (unicode, False),
		"icon": (unicode, False),
		"app": (unicode, False),
		"origin": (unicode, False),
	}
	
	# set containing the keys of all required items
	_REQUIRED_ITEMS = set(
		key for key, (type, required) in _ITEM_TYPE_MAP.iteritems() if required
	)
	
	@staticmethod
	def check_missing_items(event_dict, inplace=False):
		""" Method to check for required items.
		
		In case one or more required items are missing a KeyError is raised.
		If 'inplace' is False (default) an Event dict is returned, otherwise
		the given dict will be filled with missing optional items inplace.
		"""
		keys = set(event_dict.keys())
		missing = EventDict._REQUIRED_ITEMS - keys
		if missing:
			raise KeyError(("Some keys are missing in order to add "
				"this item properly: %s" % ", ".join(missing)))
		unknown = keys - set(EventDict._ITEM_TYPE_MAP.keys())
		if unknown:
			raise KeyError("There are some invalid values in the item: %s" %", ".join(unknown))
		result = EventDict.check_dict(event_dict, inplace)
		if not inplace:
			return result
	
	@classmethod
	def check_dict(cls, event_dict, inplace=False):
		""" Method to check the type of the items in an event dict.
		
		It automatically changes the type of all values to the expected on.
		If a value is not given an item with a default value is added.
		If 'inplace' is False (default) a new EventDict instance is returned,
		otherwise the dict given as argument will be ckecked (and changed)
		in place.
		"""
		for key, (type, required) in EventDict._ITEM_TYPE_MAP.iteritems():
			event_dict[key] = type(event_dict.get(key, type()))
		if not inplace:
			return cls(event_dict)
		
	@classmethod
	def convert_result_to_dict(cls, result_tuple):
		""" Method to convert a sql result tuple into an EventDict """
		return cls(
			timestamp = result_tuple[1],
			uri = result_tuple[0],
			text = result_tuple[7] or os.path.basename(result_tuple[0]), # FIXME: why not u"" as alternative value?
			source = result_tuple[5], 
			content = result_tuple[3],
			mimetype = result_tuple[8],
			tags = result_tuple[12] or u"",
			comment = u"",
			bookmark = bool(result_tuple[11]),
			use = result_tuple[4], # usage is determined by the event Content type # event.item.content.value
			icon = result_tuple[9],
			app = result_tuple[10],
			origin = result_tuple[6],
		)
