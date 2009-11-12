#!/usr/bin/python

# Update python path to use local zeitgeist module
import sys
import os
import time
import gobject
import dbus

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from zeitgeist.dbusutils import DBusInterface
from zeitgeist.datamodel import Event, Subject, Content, Source, EventTemplate, SubjectTemplate

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
	
	def testFindTwoOfThreeEvents(self):
		ev1 = Event.new_for_values(timestamp=400,
					interpretation=Content.VISIT_EVENT.uri,
					manifestation=Source.USER_ACTIVITY.uri,
					actor="Freak Mamma")		
		ev2 = Event.new_for_values(timestamp=500,
					interpretation=Content.VISIT_EVENT.uri,
					manifestation=Source.USER_ACTIVITY.uri,
					actor="Freak Mamma")
		ev3 = Event.new_for_values(timestamp=600,
					interpretation=Content.SEND_EVENT.uri,
					manifestation=Source.USER_ACTIVITY.uri,
					actor="Freak Mamma")
		subj1 = Subject.new_for_values(uri="foo://bar",
					interpretation=Content.DOCUMENT.uri,
					manifestation=Source.FILE.uri)
		subj2 = Subject.new_for_values(uri="foo://baz",
					interpretation=Content.IMAGE.uri,
					manifestation=Source.FILE.uri)
		subj3 = Subject.new_for_values(uri="foo://quiz",
					interpretation=Content.MUSIC.uri,
					manifestation=Source.FILE.uri)
		ev1.append_subject(subj1)
		ev2.append_subject(subj1)
		ev2.append_subject(subj2)
		ev3.append_subject(subj2)
		ev3.append_subject(subj3)
		ids = iface.InsertEvents([ev1, ev2, ev3])
		self.assertEquals(3, len(ids))
		
		events = iface.GetEvents(ids)
		self.assertEquals(3, len(events))
		events = map(Event, events)
		for event in events:
			self.assertEquals(Source.USER_ACTIVITY.uri, event.manifestation)
			self.assertEquals("Freak Mamma", event.actor)
		
		# Search for everything
		ids = iface.FindEventIds((1,1000),
					dbus.Array(signature="(asaasay)"), 0, 3, 1)
		self.assertEquals(3, len(ids)) # (we can not trust the ids because we don't have a clean test environment)
		
		# Search for some specific templates
		subj_templ1 = Subject.new_for_values(uri="foo://bar")
		subj_templ2 = Subject.new_for_values(uri="foo://baz")
		event_template = Event.new_for_values(
					interpretation=Content.VISIT_EVENT.uri,
					subjects=[subj_templ1,subj_templ2])
		ids = iface.FindEventIds((0,10000),
					[event_template],
					0, 10, 1)
		print "RESULTS", ids
		self.assertEquals(2, len(ids))
		
	
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
	
