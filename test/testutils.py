# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
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

import unittest
import os
import time
import sys
import signal
from subprocess import Popen, PIPE

# DBus setup
import gobject
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

# Import local Zeitgeist modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from zeitgeist.client import ZeitgeistDBusInterface, ZeitgeistClient
from zeitgeist.datamodel import Event, Subject, Interpretation, Manifestation, TimeRange

# Json handling is special in Python 2.5...
try:
	import json
except ImportError:
	# maybe the user is using python < 2.6
	import simplejson as json

from zeitgeist.datamodel import Event, Subject

def dict2event(d):
	ev = Event()
	ev[0][Event.Id] = d.get("id", "").encode("UTF-8")
	ev.timestamp = str(d.get("timestamp", ""))
	ev.interpretation = str(d.get("interpretation", "").encode("UTF-8"))
	ev.manifestation = str(d.get("manifestation", "").encode("UTF-8"))
	ev.actor = str(d.get("actor", "").encode("UTF-8"))
	ev.payload = str(d.get("payload", "").encode("UTF-8"))
	
	subjects = d.get("subjects", [])
	for sd in subjects:
		subj = Subject()
		subj.uri = str(sd.get("uri", "").encode("UTF-8"))
		subj.interpretation = str(sd.get("interpretation", "").encode("UTF-8"))
		subj.manifestation = str(sd.get("manifestation", "").encode("UTF-8"))
		subj.origin = str(sd.get("origin", "").encode("UTF-8"))
		subj.mimetype = str(sd.get("mimetype", "").encode("UTF-8"))
		subj.text = str(sd.get("text", "").encode("UTF-8"))
		subj.storage = str(sd.get("storage", "").encode("UTF-8"))
		ev.append_subject(subj)
	return ev
	
def parse_events(path):
	data = json.load(file(path))
	events = map(dict2event, data)
	return events

def import_events(path, engine):
	"""
	Load a collection of JSON event definitions into 'engine'. Fx:
	
	    import_events("test/data/single_event.js", self.engine)
	"""
	events = parse_events(path)
	
	return engine.insert_events(events)

class RemoteTestCase (unittest.TestCase):
	"""
	Helper class to implement unit tests against a
	remote Zeitgeist process
	"""
	
	def __init__(self, methodName):
		super(RemoteTestCase, self).__init__(methodName)
		self.daemon = None
		self.client = None
	
	def spawn_daemon(self):
		os.environ.update({"ZEITGEIST_DATABASE_PATH": ":memory:"})
		self.daemon = Popen(
			["./zeitgeist-daemon.py", "--no-datahub"], stderr=sys.stderr, stdout=sys.stderr
		)
		# give the daemon some time to wake up
		time.sleep(3)
		err = self.daemon.poll()
		if err:
			raise RuntimeError("Could not start daemon,  got err=%i" % err)
	
	def kill_daemon(self):
		os.kill(self.daemon.pid, signal.SIGKILL)
		self.daemon.wait()
		
	def setUp(self):
		assert self.daemon is None
		assert self.client is None
		self.spawn_daemon()
		
		# hack to clear the state of the interface
		ZeitgeistDBusInterface._ZeitgeistDBusInterface__shared_state = {}
		self.client = ZeitgeistClient()
	
	def tearDown(self):
		assert self.daemon is not None
		assert self.client is not None
		self.kill_daemon()
	
	def insertEventsAndWait(self, events):
		"""
		Insert a set of events and spin a mainloop until the async reply
		is back and return the result - which should be a list of ids.
		
		This method is basically just a hack to invoke an async method
		in a blocking manner.
		"""
		mainloop = gobject.MainLoop()
		result = []
		
		def collect_ids_and_quit(ids):
			result.extend(ids)
			mainloop.quit()
			
		self.client.insert_events(events,
					ids_reply_handler=collect_ids_and_quit)
		mainloop.run()
		return result
	
	def findEventIdsAndWait(self, event_templates, **kwargs):
		"""
		Do search based on event_templates and spin a mainloop until
		the async reply is back and return the result - which should be
		a list of ids.
		
		This method is basically just a hack to invoke an async method
		in a blocking manner.
		"""
		mainloop = gobject.MainLoop()
		result = []
		
		def collect_ids_and_quit(ids):
			result.extend(ids)
			mainloop.quit()
			
		self.client.find_event_ids_for_templates(event_templates,
							collect_ids_and_quit,
							**kwargs)
		mainloop.run()
		return result
	
	def getEventsAndWait(self, event_ids):
		"""
		Request a set of full events and spin a mainloop until the
		async reply is back and return the result - which should be a
		list of Events.
		
		This method is basically just a hack to invoke an async method
		in a blocking manner.
		"""
		mainloop = gobject.MainLoop()
		result = []
		
		def collect_events_and_quit(events):
			result.extend(events)
			mainloop.quit()
			
		self.client.get_events(event_ids, collect_events_and_quit)
		mainloop.run()
		return result
