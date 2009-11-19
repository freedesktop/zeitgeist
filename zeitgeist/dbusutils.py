# -.- coding: utf-8 -.-

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
import sys

from xml.dom.minidom import parseString as minidom_parse

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

from zeitgeist.datamodel import Event, Subject, TimeRange, StorageState

class ZeitgeistDBusInterface(dbus.Interface):
	""" Central DBus interface to the zeitgeist engine
	
	There doe not necessarily have to be one single instance of this
	interface class, but all instances should share the same state
	(like use the same bus and be connected to the same proxy). This is
	achieved by extending the `Borg Pattern` as described by Alex Martelli	
	"""
	__shared_state = {}
	
	INTERFACE_NAME = BUS_NAME = "org.gnome.zeitgeist.LogManager"
	OBJECT_PATH = "/org/gnome/zeitgeist/log"
	
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
		bus_obj = bus.get_object(dbus.BUS_DAEMON_IFACE, dbus.BUS_DAEMON_PATH)
		bus_obj.connect_to_signal(
			"NameOwnerChanged",
			lambda *args: callback(),
			dbus_interface=dbus.BUS_DAEMON_IFACE,
			arg0=cls.INTERFACE_NAME, #only match dying zeitgeist remote interfaces
			arg2="", #only match services with no new owner
		)
		
	@classmethod
	def version(cls):
		""" get the API version """
		proxy = cls._get_proxy()
		return proxy.get_dbus_method("Get", dbus_interface=dbus.PROPERTIES_IFACE)(cls.INTERFACE_NAME, "version")

	
	def __init__(self):
		self.__dict__ = self.__shared_state
		proxy = self._get_proxy()
		dbus.Interface.__init__(
				self,
				proxy,
				self.BUS_NAME
		)
	
class ResultType:
	"""
	An enumeration class used to define the results should be returned
	from the ZeitgeistClient.find_event_* family of methods.
	"""
	(MostRecentEvent,
	LeastRecentEvent,
	MostRecentSubject,
	LeastRecentSubject,
	MostPopularSubject,
	LeastPopularSubject) = range(6)

class ZeitgeistClient:
	"""
	Convenience APIs to have a Pythonic way to call the running Zeitgeist
	engine. For raw DBus access use the ZeitgeistZeitgeistDBusInterface class.
	
	Note that this class only does asynchnous DBus calls. This is almost
	always the right thing to do. If you really want to do synchronous
	DBus calls use the raw DBus API found in the ZeitgeistDBusInterface class.
	"""
	def __init__ (self):
		self._iface = ZeitgeistDBusInterface()
	
	def insert_event (self, event, ids_reply_handler=None, error_handler=None):
		"""
		Send an event to the Zeitgeist event log. The 'event' parameter
		must be an instance of the Event class.
		
		The insertion will be done via an asynchronous DBus call and
		this method will return immediately. This means that the
		Zeitgeist engine will most likely not have inserted the event
		when this method returns. There will be a short delay.
		
		If the ids_reply_handler argument is set to a callable it will
		be invoked with a list containing the ids of the inserted events
		when they have been registered in Zeitgeist.
		
		In case of errors a message will be printed on stderr, and
		an empty result passed to ids_reply_handler (if set).
		To override this default set the error_handler named argument
		to a callable that takes a single exception as its sole
		argument.
		
		In order to use this method there needs to be a mainloop
		runnning. Both Qt and GLib mainloops are supported.
		"""
		self.insert_events([event],
				ids_reply_handler=ids_reply_handler,
				error_handler=error_handler)
	
	def insert_event_for_values (self, **values):
		"""
		Send an event to the Zeitgeist event log. The keyword arguments
		must match those as provided to Event.new_for_values().
		
		The insertion will be done via an asynchronous DBus call and
		this method will return immediately. This means that the
		Zeitgeist engine will most likely not have inserted the event
		when this method returns. There will be a short delay.
		
		If the ids_reply_handler argument is set to a callable it will
		be invoked with a list containing the ids of the inserted events
		when they have been registered in Zeitgeist.
		
		In case of errors a message will be printed on stderr, and
		an empty result passed to ids_reply_handler (if set).
		To override this default set the error_handler named argument
		to a callable that takes a single exception as its sole
		argument.
		
		In order to use this method there needs to be a mainloop
		runnning. Both Qt and GLib mainloops are supported.
		"""
		ev = Event.new_for_values(**values)
		self.insert_event(ev,
				values.get("ids_reply_handler", None),
				values.get("error_handler", None))
	
	def insert_events (self, events, ids_reply_handler=None, error_handler=None):
		"""
		Send a collection of events to the Zeitgeist event log. The
		'events' parameter must be a list or tuple containing only
		members of of type Event.
		
		The insertion will be done via an asynchronous DBus call and
		this method will return immediately. This means that the
		Zeitgeist engine will most likely not have inserted the events
		when this method returns. There will be a short delay.
		
		In case of errors a message will be printed on stderr, and
		an empty result passed to ids_reply_handler (if set).
		To override this default set the error_handler named argument
		to a callable that takes a single exception as its sole
		argument.
		
		In order to use this method there needs to be a mainloop
		runnning. Both Qt and GLib mainloops are supported.
		"""
		
		if ids_reply_handler is None:
			ids_reply_handler = self._void_reply_handler
		
		if error_handler is None:
			error_handler = lambda raw : self._stderr_error_handler(raw, ids_reply_handler, [])
		
		self._check_list_or_tuple(events)
		self._check_members(events, Event)
		self._iface.InsertEvents(events,
					reply_handler=ids_reply_handler,
					error_handler=error_handler)
	
	def find_event_ids_for_templates (self,
					event_templates,
					ids_reply_handler,
					timerange = None,
					storage_state = StorageState.Any,
					num_events = 20,
					result_type = ResultType.MostRecentEvent,
					error_handler=None):
		"""
		Send a query matching a collection of Event-templates to the
		Zeitgeist event log. The query will be joined as a big
		OR-query between the templates. If an event template has more
		than one subject the query will match if any one of the subject
		templates match.
		
		The query will be done via an asynchronous DBus call and
		this method will return immediately. The return value
		will be passed to 'ids_reply_handler' as a list
		of integer event ids. This list must be the sole argument for
		the callback.
		
		The actual Events can be looked up via the get_events() method.
		 
		In case of errors a message will be printed on stderr, and
		an empty result passed to ids_reply_handler.
		To override this default set the error_handler named argument
		to a callable that takes a single exception as its sole
		argument.
		
		In order to use this method there needs to be a mainloop
		runnning. Both Qt and GLib mainloops are supported.
		
		Arguments:
		    * event_templates - List or tuple of Event instances
		    * ids_reply_handler - Callable taking a list of integers
		    * timerange - A TimeRange instance that the events must
		        have occured within. Defaults to TimeRange.until_now().
		    * storage_state - A value from the StorageState enumeration.
		        Defaults to StorageState.Available
		    * num_events - The number of events to return; default is 20
		    * result_type - A value from the ResultType enumeration.
		        Defaults to ResultType.MostRecentEvent
		    * error_handler - Callback to catch error messages.
		        Read about the default behaviour above
		"""
		self._check_list_or_tuple(event_templates)
		self._check_members(event_templates, Event)
		
		if error_handler is None :
			error_handler = lambda raw : self._stderr_error_handler(raw, ids_reply_handler, [])
		
		if not callable(ids_reply_handler):
			raise ValueError("Reply handler not callable, found %s" % ids_reply_handler)
		
		if timerange is None:
			timerange = TimeRange.until_now()
		
		self._iface.FindEventIds(timerange,
					event_templates,
					storage_state,
					num_events,
					result_type,
					reply_handler=ids_reply_handler,
					error_handler=error_handler)
	
	def find_event_ids_for_template (self, event_template, ids_reply_handler, **kwargs):
		"""
		Send a query matching a single Event-template to the
		Zeitgeist event log. If the event template has more
		than one subject the query will match if any one of the subject
		templates match.
		
		The query will be done via an asynchronous DBus call and
		this method will return immediately. The return value
		will be passed to 'ids_reply_handler' as a list
		of integer event ids. This list must be the sole argument for
		the callback.
		
		The actual Events can be looked up via the get_events() method.
		 
		In case of errors a message will be printed on stderr, and
		an empty result passed to ids_reply_handler.
		To override this default set the error_handler named argument
		to a callable that takes a single exception as its sole
		argument.
		
		In order to use this method there needs to be a mainloop
		runnning. Both Qt and GLib mainloops are supported.
		"""
		self.find_event_ids_for_templates([event_template],
						ids_reply_handler,
						**kwargs)
	
	def find_event_ids_for_values(self, ids_reply_handler, **kwargs):
		"""
		Send a query for events matching the keyword arguments passed
		to this function. The allowed keywords are the same as the ones
		allowed by Event.new_for_values().
		
		The query will be done via an asynchronous DBus call and
		this method will return immediately. The return value
		will be passed to 'ids_reply_handler' as a list
		of integer event ids. This list must be the sole argument for
		the callback.
		
		The actual Events can be looked up via the get_events() method.
		
		In case of errors a message will be printed on stderr, and
		an empty result passed to ids_reply_handler.
		To override this default set the error_handler named argument
		to a callable that takes a single exception as its sole
		argument.
		
		In order to use this method there needs to be a mainloop
		runnning. Both Qt and GLib mainloops are supported.
		"""
		ev = Event.new_for_values(**kwargs)
		
		self.find_event_ids_for_templates([ev],
						ids_reply_handler,
						**kwargs)
	
	def get_events (self, event_ids, events_reply_handler, error_handler=None):
		"""
		Look up a collection of Events in the Zeitgeist event log
		given a collection of event ids. This is useful for looking
		up the event data for events found with the find_event_ids_*
		family of functions.
		
		The query will be done via an asynchronous DBus call and
		this method will return immediately. The returned events
		will be passed to 'events_reply_handler' as a list
		of Events, which must be the only argument of the function.
		 
		In case of errors a message will be printed on stderr, and
		an empty result passed to events_reply_handler.
		To override this default set the error_handler named argument
		to a callable that takes a single exception as its sole
		argument.
		
		In order to use this method there needs to be a mainloop
		runnning. Both Qt and GLib mainloops are supported.
		"""
		
		if error_handler is None :
			error_handler = lambda raw : self._stderr_error_handler(raw, events_reply_handler, [])
		
		if not callable(events_reply_handler):
			raise ValueError("Reply handler not callable, found %s" % events_reply_handler)
		
		# Generate a wrapper callback that does automagic conversion of
		# the raw DBus reply into a list of Event instances
		self._iface.GetEvents(event_ids,
				reply_handler=lambda raw : events_reply_handler(map(Event, raw)),
				error_handler=error_handler)
		
	def _check_list_or_tuple(self, collection):
		"""
		Raise a ValueError unless 'collection' is a list or tuple
		"""
		if not (isinstance(collection, list) or isinstance(collection, tuple)):
			raise ValueError("Expected list or tuple, found %s" % type(collection))
	
	def _check_members (self, collection, member_class):
		"""
		Raise a ValueError unless all of the members of 'collection'
		are of class 'member_class'
		"""
		for m in collection:
			if not isinstance(m, member_class):
				raise ValueError("Collection contains member of invalid type %s. Expected %s" % (ev.__class__, member_class) )
	
	def _void_reply_handler(self, *args, **kwargs):
		"""
		Reply handler for async DBus calls that simply ignores the response
		"""
		pass
		
	def _stderr_error_handler(self, exception, normal_reply_handler, normal_reply_data):
		"""
		Error handler for async DBus calls that prints the error
		to sys.stderr
		"""
		print >> sys.stderr, "Error from Zeitgeist engine:", exception
		normal_reply_handler(normal_reply_data)
	
	
