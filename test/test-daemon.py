#!/usr/bin/python

import dbus
import unittest
import sys
import os.path
import time
from subprocess import Popen, PIPE
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from zeitgeist.client import ZeitgeistDBusInterface

def service_isRunning(bus_name, bus=dbus.SessionBus()):
	return bool(bus.get_object("org.freedesktop.DBus", "/org/freedesktop/DBus").NameHasOwner(bus_name))
	
def service_isActivable(bus_name, bus=dbus.SessionBus()):
	return bus_name in bus.get_object("org.freedesktop.DBus", "/org/freedesktop/DBus").ListActivatableNames()

DAEMON = os.path.join(os.path.dirname(__file__), "../zeitgeist-daemon.py")

def wait_until(times, timeout, condition, *args):
	counter = 0
	while counter < times and not condition(*args):
		time.sleep(timeout)
		counter += 1
	if not counter < times:
		raise RuntimeError("waited maximum of time")

class TestDaemon(unittest.TestCase):
	
	def setUp(self):
		if service_isActivable(ZeitgeistDBusInterface.BUS_NAME):
			# skip test, unfortunatly there is not SKIP method in stdlib's unittest module
			raise RuntimeError("the dbus system will always try to start the service from the .service file, skip test")
		if service_isRunning(ZeitgeistDBusInterface.BUS_NAME):
			# skip test, unfortunatly there is not SKIP method in stdlib's unittest module
			raise RuntimeError("service is already running, skip test")
		self.__processes = list()
	
	def tearDown(self):
		while self.__processes:
			p = self.__processes.pop()
			try:
				p.kill()
			except OSError:
				# already terminated process
				pass
	
	def test_not_running(self):
		self.assertRaises(RuntimeError, ZeitgeistDBusInterface)
	
	def test_run(self):
		# start the first daemon instance
		p1 = Popen([DAEMON,], stderr=PIPE, stdout=PIPE)
		self.__processes.append(p1)
		wait_until(10, 0.2, service_isRunning, ZeitgeistDBusInterface.BUS_NAME)
		# dbus interface should work now
		#~ iface = ZeitgeistDBusInterface()
		#start second instance, this should fail
		p2 = Popen([DAEMON,], stderr=PIPE, stdout=PIPE)
		self.__processes.append(p2)
		wait_until(10, 0.2, lambda : p2.poll() is not None)
		self.assertEqual(p2.poll(), 1)
		#start daemon and replace already running instance
		#the already running one should exit, and the new one should run instead
		p3 = Popen([DAEMON, "--replace"], stderr=PIPE, stdout=PIPE)
		self.__processes.append(p3)
		wait_until(10, 0.2, lambda : p1.poll() is not None)
		self.assertEqual(p1.poll(), 0)
		self.assertEqual(p3.poll(), None)

if __name__ == '__main__':
	unittest.main()
