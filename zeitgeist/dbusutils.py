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
	
	@classmethod
	def get_session_bus(cls):
		try:
			return cls.__shared_state["_bus"]
		except KeyError, e:
			cls.__shared_state["_bus"] = dbus.SessionBus()
			return cls.__shared_state["_bus"]
		
	@classmethod
	def _get_proxy(cls):
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
					raise RuntimeError(("No running instance of the "
						"zeitgeist daemon found: %s") %e.get_dbus_message())
				else:
					raise
			return cls.__shared_state["proxy_object"]
		
	@classmethod
	def dbus_connect(cls, signal, callback, arg0=None):
		proxy = cls._get_proxy()
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
	
	def __init__(self):
		self.__dict__ = self.__shared_state
		proxy = self._get_proxy()
		dbus.Interface.__init__(
				self,
				proxy,
				self.BUS_NAME
		)

ITEM_STRUCTURE = {
	"timestamp": int,
	"uri": unicode,
	"text": unicode,
	"source": unicode,
	"content": unicode,
	"mimetype": unicode,
	"tags": unicode,
	"comment": unicode,
	"bookmark": bool,
	"use": unicode,
	"icon": unicode,
	"app": unicode,
	"origin": unicode,
}

ITEM_STRUCTURE_KEYS = set(ITEM_STRUCTURE.keys())

DEFAULTS = {int: 0, unicode: "", bool: False} #can be reomved
TYPES = {int: "i", unicode: "s", bool: "b"}
TYPES_DICT = dict(ITEM_STRUCTURE) 

#~ sig_plain_data = "(%s)" %"".join(TYPES[i[1]] for i in ITEM_STRUCTURE)
sig_plain_data = "a{sv}"

def check_dict(event_dict):
	return dict((key, event_dict.get(key, type())) for key, type in TYPES_DICT.iteritems())
		
