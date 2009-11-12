#!/usr/bin/python

# Update python path to use local zeitgeist module
import sys
import os
import time
import gobject
import dbus

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from zeitgeist.dbusutils import DBusInterface
from zeitgeist.datamodel import Event, Subject, Content, Source

import _zeitgeist.engine
from _zeitgeist.engine import create_engine

#
# IMPORTANT: We don't use the unittest module here because it is too hard
#            to control the processes spawned.
#            
#            Because of the simplified test environment changes are persistet
#            on the engine in between tests
#

class TestFailed (RuntimeError):
	def __init__(self, msg=None):
		if msg : RuntimeError.__init__(self, msg)
		else : RuntimeError.__init__(self)

class RemoteTest:
	
	def __init__ (self, iface):
		self.iface = iface
		
	def assertEquals(self, expected, actual):
		if expected != actual : raise TestFailed("Expected %s found %s" % (expected, actual))
	
	def testNothing(self):
		# Simply assert that we start and stop correctly
		pass
	
	def testInsertAndGetEvent(self):
		ev = Event.new_for_values(timestamp=123,
					interpretation=Content.VISIT_EVENT.uri,
					manifestation=Source.USER_ACTIVITY.uri,
					actor="Freak Mamma")
		subj = Subject.new_for_values(uri="void://foobar",
					interpretation=Content.DOCUMENT.uri,
					manifestation=Source.FILE.uri)
		ev.append_subject(subj)
		ids = iface.InsertEvents([ev])
		events = iface.GetEvents(ids)
		self.assertEquals(1, len(ids))
		self.assertEquals(1, len(events))
		
		
	
if __name__ == "__main__":
	child_pid = os.fork()
	if child_pid > 0:
		# parent process, this is the client
		# connect to server, but give it a 1s gracetime to come up
		time.sleep(1)
		retries = 0
		while retries <= 10:
			retries += 1
			try:					
				iface = DBusInterface()
				break
			except:
				# retry
				time.sleep(0.5)
		if retries >= 10 : raise TestFailed("Failed to start server")
	else:
		# child process, this is the server
		_zeitgeist.engine.DB_PATH = ":memory:"
		engine = create_engine()
	
		# The remote.py module is hacky so we must import this a bit late
		from _zeitgeist.engine.remote import RemoteInterface
	
		# We run the DBus server in a separate thread
		mainloop = gobject.MainLoop()
		
		remote = RemoteInterface(mainloop=mainloop)
		
		mainloop.run()
		print "Server stopped"
		raise SystemExit(0)
	
	suite = RemoteTest(iface)
	
	try:
		for test in dir(suite):
			method = getattr(suite, test)
			if callable(method):
				test_name = method.im_func.func_name
				if test_name.startswith("test"):
					print "******", test_name
					method()
	finally:
		print "All tests done, waiting for server to stop"
		iface.Quit()
		os.waitpid(child_pid, 0)
	
