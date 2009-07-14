# -.- encoding: utf-8 -.-

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

from zeitgeist.dbusutils import DBusInterface

class SingletonApplication (dbus.service.Object):
	"""
	Base class for singleton applications and dbus services.
	
	Subclasses must implement a Quit method which will be called
	when a new process wants to replace an existing process.
	"""
	
	def __init__ (self):
		logging.debug("Checking for another running instance...")
		sbus = DBusInterface.get_session_bus()
		
		def running_daemon():
			running_services = sbus.get_object("org.freedesktop.DBus",
				"/org/freedesktop/DBus").ListNames()
			return DBusInterface.BUS_NAME in running_services
		
		if running_daemon():
			# already running daemon instance
			if "--replace" in sys.argv:
				logging.debug("Replacing currently running process.")
				# TODO: This only works for the engine and wont work for the DataHub
				interface = DBusInterface()
				interface.Quit()
				while running_daemon():
					pass
				# TODO: We should somehow set a timeout and kill the old process
				# if it doesn't quit when we ask it to. (Perhaps we should at least
				# steal the bus using replace_existing=True)
			else:
				raise RuntimeError(
					("An existing instance was found. Please use "
					 "--replace to quit it and start a new instance.")
				)
		else:
			# service is not running, save to start
			logging.debug("No other instances found.")
		
		bus = dbus.service.BusName(DBusInterface.BUS_NAME, sbus, do_not_queue=True)
		dbus.service.Object.__init__(self, bus, DBusInterface.OBJECT_PATH)
