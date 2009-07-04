# -.- encoding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Natan Yellin <aantny@gmail.com>
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

from dbusutils import get_session_bus, get_engine_interface

class SingletonApplication (dbus.service.Object):
	"""
	Base class for singleton applications and dbus services.
	
	Subclasses must implement a Quit method which will be called
	when a new process wants to replace an existing process.
	"""
	
	def __init__ (self, bus_name, path_name):
		sbus = get_session_bus()
		
		try:
			logging.info("Checking for another running instance...")
			bus = dbus.service.BusName(bus_name, sbus, do_not_queue=True)
			dbus.service.Object.__init__(self, bus, path_name)
			logging.info("No other instances found.")
		
		except dbus.exceptions.NameExistsException, ex:
			if "--replace" in sys.argv:
				logging.info("Replacing currently running process.")
				# TODO: This only works for the engine and wont work for the DataHub
				iface = get_engine_interface()
				iface.Quit()
				# Try to initialize our service again
				# TODO: We should somehow set a timeout and kill the old process
				# if it doesn't quit when we ask it to. (Perhaps we should at least
				# steal the bus using replace_existing=True)
				bus = dbus.service.BusName(bus_name, sbus, do_not_queue=False)
				dbus.service.Object.__init__(self, bus, path_name)
			
			else:
				logging.critical("An existing instance was found. Please use --replace to quit it and start a new instance.")
				sys.exit(1)
