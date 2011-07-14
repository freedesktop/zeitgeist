# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Natan Yellin <aantny@gmail.com>
# Copyright © 2009 Markus Korn <thekorn@gmx.de>
# Copyright © 2011 Collabora Ltd.
#             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 2.1 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import dbus

from zeitgeist.client import ZeitgeistDBusInterface
from zeitgeist import _config

log = logging.getLogger("singleton")

class _DBusFlags:

	NameAcquired = 1		# REQUEST_NAME_REPLY_PRIMARY_OWNER
	NameQueued = 2			# REQUEST_NAME_REPLY_IN_QUEUE 
	NameAlreadyExists = 3	# REQUEST_NAME_REPLY_EXISTS
	NameAlreadyOwned = 4	# REQUEST_NAME_REPLY_ALREADY_OWNED

	AllowReplacement = 1	# NAME_FLAG_ALLOW_REPLACEMENT
	ReplaceExisting = 2		# NAME_FLAG_REPLACE_EXISTING
	DoNotQueue = 4			# NAME_FLAG_DO_NOT_QUEUE

class SingletonApplication(dbus.service.Object):
	"""
	Base class for singleton applications and dbus services.
	
	Subclasses must implement a Quit method which will be called
	when a new process wants to replace an existing process.
	"""
	
	def __init__ (self):
		log.debug("Checking for another running instance...")
		if dbus.SessionBus().name_has_owner(ZeitgeistDBusInterface.BUS_NAME):
			# already running daemon instance
			self._handle_existing_instance()
		elif hasattr(_config, "options") and _config.options.quit:
			logging.info("There is no running instance; doing nothing.")
		
		if hasattr(_config, "options") and _config.options.quit:
			raise SystemExit(0)
		
		bus = self._acquire_bus(recursive=True)
		dbus.service.Object.__init__(self, dbus.SessionBus(),
			ZeitgeistDBusInterface.OBJECT_PATH)

	def _acquire_bus(self, recursive):
		result = dbus.SessionBus().request_name(ZeitgeistDBusInterface.BUS_NAME,
			_DBusFlags.DoNotQueue)
		if result != _DBusFlags.NameAcquired:
			# Look what we've got, a race condition! (LP: #732015)
			if recursive:
				# Let's call _handle_existing_instance again; it'll either raise
				# a RuntimeError or free the bus for us.
				self._handle_existing_instance()

				# If we're still here, try to get the bus a second time.
				return self._acquire_bus(recursive=False)
			else:
				raise RuntimeError("Failed to acquire the bus. Please try again.")

	def _handle_existing_instance(self):
		if hasattr(_config, "options") and (_config.options.replace or _config.options.quit):
			if _config.options.quit:
				logging.info("Stopping the currently running instance...")
			else:
				logging.debug("Replacing currently running process...")
			try:
				interface = ZeitgeistDBusInterface(reconnect=False)
				interface.Quit()
				while dbus.SessionBus().name_has_owner(ZeitgeistDBusInterface.BUS_NAME):
					pass
				# TODO: We should somehow set a timeout and kill the old process
				# if it doesn't quit when we ask it to. (Perhaps we should at least
				# steal the bus using replace_existing=True)
			except dbus.exceptions.DBusException, e:
				if e.get_dbus_name() != "org.freedesktop.DBus.Error.ServiceUnknown":
					raise
		else:
			raise RuntimeError("An existing instance was found. Please use " \
				 "--replace to quit it and start a new instance.")
				 
	def _safe_quit(self):
		# safely quit the interface on the bus by removing this interface
		# from the bus, and releasing the (by-hand) registered bus name
		self.remove_from_connection()
		self.connection.release_name(ZeitgeistDBusInterface.BUS_NAME)
