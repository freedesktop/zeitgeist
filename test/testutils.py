# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
# Copyright © 2009-2010 Markus Korn <thekorn@gmx.de>
# Copyright © 2011 Collabora Ltd.
#             By Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
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

import unittest
import os
import time
import sys
import signal
import tempfile
import shutil
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

def dict2event(d):
	ev = Event()
	ev[0][Event.Id] = d.get("id", "").encode("UTF-8")
	ev.timestamp = str(d.get("timestamp", ""))
	ev.interpretation = str(d.get("interpretation", "").encode("UTF-8"))
	ev.manifestation = str(d.get("manifestation", "").encode("UTF-8"))
	ev.actor = str(d.get("actor", "").encode("UTF-8"))
	ev.origin = str(d.get("origin", "").encode("UTF-8"))
	ev.payload = str(d.get("payload", "").encode("UTF-8"))
	
	subjects = d.get("subjects", [])
	for sd in subjects:
		subj = Subject()
		subj.uri = str(sd.get("uri", "").encode("UTF-8"))
		subj.current_uri = str(sd.get("current_uri", "")).encode("UTF-8")
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
	
	@staticmethod
	def _get_pid(matching_string):
		p1 = Popen(["ps", "aux"], stdout=PIPE, stderr=PIPE)
		p2 = Popen(["grep", matching_string], stdin=p1.stdout, stderr=PIPE, stdout=PIPE)
		return p2.communicate()[0]
		
	@staticmethod
	def _safe_start_subprocess(cmd, env, timeout=1, error_callback=None):
		""" starts `cmd` in a subprocess and check after `timeout`
		if everything goes well"""
		process = Popen(cmd, stderr=PIPE, stdout=PIPE, env=env)
		# give the process some time to wake up
		time.sleep(timeout)
		error = process.poll()
		if error:
			cmd = " ".join(cmd)
			error = "'%s' exits with error %i." %(cmd, error)
			if error_callback:
				error += " *** %s" %error_callback(*process.communicate())
			raise RuntimeError(error)
		return process
		
	@staticmethod
	def _safe_start_daemon(env=None, timeout=1):
		if env is None:
			env = os.environ.copy()
			
		def error_callback(stdout, stderr):
			if "--replace" in stderr:
				return "%r | %s" %(stderr, RemoteTestCase._get_pid("zeitgeist-daemon").replace("\n", "|"))
			else:
				return stderr
			
		return RemoteTestCase._safe_start_subprocess(
			("./zeitgeist-daemon.py", "--no-datahub"), env, timeout, error_callback
		)
	
	def __init__(self, methodName):
		super(RemoteTestCase, self).__init__(methodName)
		self.daemon = None
		self.client = None
	
	def spawn_daemon(self):
		self.daemon = self._safe_start_daemon(env=self.env)
	
	def kill_daemon(self, kill_signal=signal.SIGKILL):
		os.kill(self.daemon.pid, kill_signal)
		self.daemon.wait()
		
	def setUp(self):
		assert self.daemon is None
		assert self.client is None
		self.env = os.environ.copy()
		self.datapath = tempfile.mkdtemp(prefix="zeitgeist.datapath.")
		self.env.update({
			"ZEITGEIST_DATABASE_PATH": ":memory:",
			"ZEITGEIST_DATA_PATH": self.datapath,
		})
		self.spawn_daemon()
		
		# hack to clear the state of the interface
		ZeitgeistDBusInterface._ZeitgeistDBusInterface__shared_state = {}
		self.client = ZeitgeistClient()
	
	def tearDown(self):
		assert self.daemon is not None
		assert self.client is not None
		self.kill_daemon()
		shutil.rmtree(self.datapath)
	
	def insertEventsAndWait(self, events):
		"""
		Insert a set of events and spin a mainloop until the async reply
		is back and return the result - which should be a list of ids.
		
		This method is basically just a hack to invoke an async method
		in a blocking manner.
		"""
		mainloop = self.create_mainloop()
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
		mainloop = self.create_mainloop()
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
		mainloop = self.create_mainloop()
		result = []
		
		def collect_events_and_quit(events):
			result.extend(events)
			mainloop.quit()
			
		self.client.get_events(event_ids, collect_events_and_quit)
		mainloop.run()
		return result
	
	def findEventsForValuesAndWait(self, *args, **kwargs):
		"""
		Execute ZeitgeistClient.find_events_for_value in a blocking manner.
		"""
		mainloop = self.create_mainloop()
		result = []
		
		def collect_events_and_quit(events):
			result.extend(events)
			mainloop.quit()
		
		self.client.find_events_for_values(
			collect_events_and_quit, *args, **kwargs)
		mainloop.run()
		return result
	
	def deleteEventsAndWait(self, event_ids):
		"""
		Delete events given by their id and run a loop until the result 
		containing a timetuple describing the interval of changes is
		returned.
		
		This method is basically just a hack to invoke an async method
		in a blocking manner.
		"""
		mainloop = self.create_mainloop()
		result = []
		
		def collect_timestamp_and_quit(timestamps):
			result.append(timestamps)
			mainloop.quit()
		
		self.client.delete_events(event_ids, collect_timestamp_and_quit)
		mainloop.run()
		return result[0]
		
	def findRelatedAndWait(self, subject_uris, num_events, result_type):
		"""
		Find related subject uris to given uris and return them.
		
		This method is basically just a hack to invoke an async method
		in a blocking manner.
		"""
		mainloop = self.create_mainloop()
		result = []
		
		def callback(uri_list):
			result.extend(uri_list)
			mainloop.quit()
		
		self.client.find_related_uris_for_uris(subject_uris, callback,
			num_events=num_events, result_type=result_type)
		mainloop.run()
		return result
	
	@staticmethod
	def create_mainloop(timeout=5):
		
		class MainLoopWithFailure(object):
			
			def __init__(self):
				self._mainloop = gobject.MainLoop()
				self.failed = False
			
			def __getattr__(self, name):
				return getattr(self._mainloop, name)
			
			def fail(self, message):
				self.failed = True
				self.failure_message = message
				mainloop.quit()
			
			def run(self):
				assert self.failed is False
				self._mainloop.run()
				if self.failed:
					raise AssertionError, self.failure_message
		
		mainloop = MainLoopWithFailure()
		if timeout is not None:
			def cb_timeout():
				mainloop.fail("Timed out -- "
					"operations not completed in reasonable time.")
				return False # stop timeout from being called again
			
			# Add an arbitrary timeout so this test won't block if it fails
			gobject.timeout_add_seconds(timeout, cb_timeout)
		
		return mainloop

class DBusPrivateMessageBus(object):
	DISPLAY = ":27"

	def _run(self):
		os.environ.update({"DISPLAY": self.DISPLAY})
		devnull = file("/dev/null", "w")
		self.display = Popen(
			["Xvfb", self.DISPLAY, "-screen", "0", "1024x768x8"],
			stderr=devnull, stdout=devnull
		)
		# give the display some time to wake up
		time.sleep(1)
		err = self.display.poll()
		if err:
			raise RuntimeError("Could not start Xvfb on display %s, got err=%i" %(self.DISPLAY, err))
		dbus = Popen(["dbus-launch"], stdout=PIPE)
		time.sleep(1)
		self.dbus_config = dict(l.split("=", 1) for l in dbus.communicate()[0].split("\n") if l)
		os.environ.update(self.dbus_config)
		
	def run(self, ignore_errors=False):
		try:
			return self._run()
		except Exception, e:
			if ignore_errors:
				return e
			raise

	def _quit(self):
		os.kill(self.display.pid, signal.SIGKILL)
		self.display.wait()
		pid = int(self.dbus_config["DBUS_SESSION_BUS_PID"])
		os.kill(pid, signal.SIGKILL)
		try:
			os.waitpid(pid, 0)
		except OSError:
			pass
			
	def quit(self, ignore_errors=False):
		try:
			return self._quit()
		except Exception, e:
			if ignore_errors:
				return e
			raise
