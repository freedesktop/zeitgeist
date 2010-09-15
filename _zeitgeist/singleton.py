# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Natan Yellin <aantny@gmail.com>
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

import logging
import sys
import dbus

from zeitgeist.client import ZeitgeistDBusInterface
from zeitgeist import _config

class SingletonApplication (dbus.service.Object):
	"""
	Base class for singleton applications and dbus services.
	
	Subclasses must implement a Quit method which will be called
	when a new process wants to replace an existing process.
	"""
	
	def __init__ (self):
		logging.debug("Checking for another running instance...")
		sbus = dbus.SessionBus()
		dbus_service = sbus.get_object("org.freedesktop.DBus", "/org/freedesktop/DBus")
		
		if dbus_service.NameHasOwner(ZeitgeistDBusInterface.BUS_NAME):
			# already running daemon instance
			if hasattr(_config, "options") and (_config.options.replace or _config.options.quit):
				if _config.options.quit:
					logging.info("Stopping the currently running instance.")
				else:
					logging.debug("Replacing currently running process.")
				# TODO: This only works for the engine and wont work for the DataHub
				interface = ZeitgeistDBusInterface()
				interface.Quit()
				while dbus_service.NameHasOwner(ZeitgeistDBusInterface.BUS_NAME):
					pass
				# TODO: We should somehow set a timeout and kill the old process
				# if it doesn't quit when we ask it to. (Perhaps we should at least
				# steal the bus using replace_existing=True)
			else:
				raise RuntimeError(
					("An existing instance was found. Please use "
					 "--replace to quit it and start a new instance.")
				)
		elif hasattr(_config, "options") and _config.options.quit:
			logging.info("There is no running instance; doing nothing.")
		else:
			# service is not running, save to start
			logging.debug("No running instances found.")
		
		if hasattr(_config, "options") and _config.options.quit:
			sys.exit(0)
		
		bus = dbus.service.BusName(ZeitgeistDBusInterface.BUS_NAME, sbus, do_not_queue=True)
		dbus.service.Object.__init__(self, bus, ZeitgeistDBusInterface.OBJECT_PATH)
