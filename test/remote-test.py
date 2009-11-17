import unittest
import os
import time
import sys
import signal

from subprocess import Popen, PIPE

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from zeitgeist.dbusutils import DBusInterface
from zeitgeist.datamodel import Event, Subject, Interpretation, Manifestation

class ZeitgeistRemoteAPITest(unittest.TestCase):
	
	def __init__(self, methodName):
		super(ZeitgeistRemoteAPITest, self).__init__(methodName)
		self.daemon = None
		self.iface = None
	
	def spawn_daemon(self):
		os.environ.update({"ZEITGEIST_DATABASE_PATH": ":memory:"})
		self.daemon = Popen(["./zeitgeist-daemon", "--no-passive-loggers"])
		# give the daemon some time to wake up
		time.sleep(3)
		err = self.daemon.poll()
		if err:
			raise RuntimeError("Could not start daemon,  got err=%i" %err)
		
		
	def kill_daemon(self):
		os.kill(self.daemon.pid, signal.SIGKILL)
		self.daemon.wait()
		
	def setUp(self):
		assert self.daemon is None
		assert self.iface is None
		self.spawn_daemon()
		
		# hack to clear the state of the interface
		DBusInterface._DBusInterface__shared_state = {}
		self.iface = DBusInterface()
		
	def tearDown(self):
		assert self.daemon is not None
		assert self.iface is not None
		self.kill_daemon()
	
	def testInsertAndGetEvent(self):
		ev = Event.new_for_values(timestamp=123,
					interpretation=Interpretation.VISIT_EVENT.uri,
					manifestation=Manifestation.USER_ACTIVITY.uri,
					actor="Freak Mamma")
		subj = Subject.new_for_values(uri="void://foobar",
					interpretation=Interpretation.DOCUMENT.uri,
					manifestation=Manifestation.FILE.uri)
		ev.append_subject(subj)
		ids = self.iface.InsertEvents([ev])
		events = self.iface.GetEvents(ids)
		self.assertEquals(1, len(ids))
		self.assertEquals(1, len(events))
		
		ev = Event(events[0])
		self.assertEquals("123", ev.timestamp)
		self.assertEquals(Interpretation.VISIT_EVENT.uri, ev.interpretation)
		self.assertEquals(Manifestation.USER_ACTIVITY.uri, ev.manifestation)
		self.assertEquals("Freak Mamma", ev.actor)
		self.assertEquals(1, len(ev.subjects))
		self.assertEquals("void://foobar", ev.subjects[0].uri)
		self.assertEquals(Interpretation.DOCUMENT.uri, ev.subjects[0].interpretation)
		self.assertEquals(Manifestation.FILE.uri, ev.subjects[0].manifestation)
		
	def testFindTwoOfThreeEvents(self):
		ev1 = Event.new_for_values(timestamp=400,
					interpretation=Interpretation.VISIT_EVENT.uri,
					manifestation=Manifestation.USER_ACTIVITY.uri,
					actor="Boogaloo")	
		ev2 = Event.new_for_values(timestamp=500,
					interpretation=Interpretation.VISIT_EVENT.uri,
					manifestation=Manifestation.USER_ACTIVITY.uri,
					actor="Boogaloo")
		ev3 = Event.new_for_values(timestamp=600,
					interpretation=Interpretation.SEND_EVENT.uri,
					manifestation=Manifestation.USER_ACTIVITY.uri,
					actor="Boogaloo")
		subj1 = Subject.new_for_values(uri="foo://bar",
					interpretation=Interpretation.DOCUMENT.uri,
					manifestation=Manifestation.FILE.uri)
		subj2 = Subject.new_for_values(uri="foo://baz",
					interpretation=Interpretation.IMAGE.uri,
					manifestation=Manifestation.FILE.uri)
		subj3 = Subject.new_for_values(uri="foo://quiz",
					interpretation=Interpretation.MUSIC.uri,
					manifestation=Manifestation.FILE.uri)
		ev1.append_subject(subj1)
		ev2.append_subject(subj1)
		ev2.append_subject(subj2)
		ev3.append_subject(subj2)
		ev3.append_subject(subj3)
		ids = self.iface.InsertEvents([ev1, ev2, ev3])
		self.assertEquals(3, len(ids))
		
		events = self.iface.GetEvents(ids)
		self.assertEquals(3, len(events))
		events = map(Event, events)
		for event in events:
			self.assertEquals(Manifestation.USER_ACTIVITY.uri, event.manifestation)
			self.assertEquals("Boogaloo", event.actor)
		
		# Search for everything
		import dbus
		ids = self.iface.FindEventIds((1,1000),
					dbus.Array(signature="(asaasay)"), 0, 3, 1)
		self.assertEquals(3, len(ids)) # (we can not trust the ids because we don't have a clean test environment)
		
		# Search for some specific templates
		subj_templ1 = Subject.new_for_values(uri="foo://bar")
		subj_templ2 = Subject.new_for_values(uri="foo://baz")
		event_template = Event.new_for_values(
					actor="Boogaloo",
					interpretation=Interpretation.VISIT_EVENT.uri,
					subjects=[subj_templ1,subj_templ2])
		ids = self.iface.FindEventIds((0,10000),
					[event_template],
					0, 10, 1)
		print "RESULTS", map(int, ids)
		self.assertEquals(2, len(ids))

	
if __name__ == "__main__":
	unittest.main()
