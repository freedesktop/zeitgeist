# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
# Copyright © 2009-2010 Markus Korn <thekorn@gmx.de>
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

import unittest
import dbus
import os
import time
import sys
import signal
import tempfile
import shutil
import random
import gi
from subprocess import Popen, PIPE

# DBus setup
from gi.repository import GLib
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

# Import local Zeitgeist modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from zeitgeist.client import ZeitgeistDBusInterface, ZeitgeistClient, \
	get_bus, _set_bus
from zeitgeist.datamodel import Event, Subject, Interpretation, Manifestation, \
	TimeRange, NULL_EVENT

# Json handling is special in Python 2.5...
try:
	import json
except ImportError:
	# maybe the user is using python < 2.6
	import simplejson as json

def dict2event(d):
	ev = Event()
	ev[0][Event.Id] = d.get("id", "")
	ev.timestamp = d.get("timestamp", "")
	ev.interpretation = d.get("interpretation", "")
	ev.manifestation = d.get("manifestation", "")
	ev.actor = d.get("actor", "")
	ev.origin = d.get("origin", "")
	ev.payload = d.get("payload", "")
	
	subjects = d.get("subjects", [])
	for sd in subjects:
		subj = Subject()
		subj.uri = sd.get("uri", "")
		subj.current_uri = sd.get("current_uri", "")
		subj.interpretation = sd.get("interpretation", "")
		subj.manifestation = sd.get("manifestation", "")
		subj.origin = sd.get("origin", "")
		subj.current_origin = sd.get("current_origin", "")
		subj.mimetype = sd.get("mimetype", "")
		subj.text = sd.get("text", "")
		subj.storage = sd.get("storage", "")
		ev.append_subject(subj)
	return ev
	
def parse_events(path):
	with open(path) as f:
		data = json.load(f)
	events = list(map(dict2event, data))
	return events

def import_events(path, engine):
	"""
	Load a collection of JSON event definitions into 'engine'. Fx:
	
		import_events("test/data/single_event.js", self.engine)
	"""
	events = parse_events(path)
	return engine.insertEventsAndWait(events)

def complete_event(event):
	"""
	Completes the given event by filling in any required fields that are missing
	with some default value.
	"""
	if not event.interpretation:
		event.interpretation = Interpretation.ACCESS_EVENT
	if not event.manifestation:
		event.manifestation = Manifestation.USER_ACTIVITY
	if not event.actor:
		event.actor = "application://zeitgeist-test.desktop"

	for subject in event.subjects:
		if not subject.uri:
			subject.uri = "file:///tmp/example file"

	return event

def complete_events(events):
	return list(map(complete_event, events))

def new_event(*args, **kwargs):
	"""
	Creates a new event, initializing all required fields with default values.
	"""
	return complete_event(Event.new_for_values(*args, **kwargs))

def asyncTestMethod(mainloop):
	"""
	Any callbacks happening in a MainLoopWithFailure must use
	this decorator for exceptions raised inside them to be visible.
	"""
	def wrap(f):
		def new_f(*args, **kwargs):
			try:
				f(*args, **kwargs)
			except AssertionError as e:
				mainloop.fail("Assertion failed: %s" % e)
			except Exception as e:
				mainloop.fail("Unexpected exception: %s" % e)
		return new_f
	return wrap

class RemoteTestCase (unittest.TestCase):
	"""
	Helper class to implement unit tests against a
	remote Zeitgeist process
	"""
	
	@staticmethod
	def _get_pid(matching_string):
		p1 = Popen(["pgrep", "-x", "zeitgeist-daemo"], stdout=PIPE, stderr=PIPE)
		out = p1.communicate()[0]
		pid = out.decode().split('\n')[0]

		p2 = Popen(["ps", "--no-headers", "-fp", pid], stderr=PIPE, stdout=PIPE)
		pid_line = p2.communicate()[0].decode()

		return pid_line
		
	@staticmethod
	def _safe_start_subprocess(cmd, env, timeout=1, error_callback=None):
		""" starts `cmd` in a subprocess and check after `timeout`
		if everything goes well"""
		args = { 'env': env }
		if not '--verbose-subprocess' in sys.argv:
			args['stderr'] = PIPE
			args['stdout'] = PIPE
		process = Popen(cmd, **args)
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
			stderr = stderr.decode()
			if "--replace" in stderr:
				return "%r | %s" %(stderr, RemoteTestCase._get_pid(
					"./src/zeitgeist-daemon").replace("\n", "|"))
			else:
				return stderr
			
		return RemoteTestCase._safe_start_subprocess(
			("./src/zeitgeist-daemon", "--no-datahub", "--log-level=DEBUG"),
			env, timeout, error_callback)
	
	def __init__(self, methodName):
		super(RemoteTestCase, self).__init__(methodName)
		self.daemon = None
		self.client = None
	
	def spawn_daemon(self):
		self.daemon = self._safe_start_daemon(env=self.env)
	
	def kill_daemon(self, kill_signal=signal.SIGKILL):
		os.kill(self.daemon.pid, kill_signal)
		return self.daemon.wait()

	def setUp(self, database_path=None):
		assert self.daemon is None
		assert self.client is None
		self.env = os.environ.copy()
		self.datapath = tempfile.mkdtemp(prefix="zeitgeist.datapath.")
		self.env.update({
			"ZEITGEIST_DATABASE_PATH": database_path or ":memory:",
			"ZEITGEIST_DATA_PATH": self.datapath,
			"XDG_CACHE_HOME": os.path.join(self.datapath, "cache"),
		})
		self.spawn_daemon()
		
		# hack to clear the state of the interface
		ZeitgeistDBusInterface._ZeitgeistDBusInterface__shared_state = {}
		
		# Replace the bus connection with a private one for each test case,
		# so that they don't share signals or other state
		_set_bus(dbus.SessionBus(private=True))
		get_bus().set_exit_on_disconnect(False)
		
		self.client = ZeitgeistClient()
	
	def tearDown(self):
		assert self.daemon is not None
		assert self.client is not None
		get_bus().close()
		self.kill_daemon()
		if 'ZEITGEIST_TESTS_KEEP_TMP' in os.environ:
			print('\n\nAll temporary files have been preserved in %s\n' \
				% self.datapath)
		else:
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
			for event in events:
				if event:
					event[0][0] = int(event.id)
			result.extend(events)
			mainloop.quit()
			
		self.client.get_events(event_ids, collect_events_and_quit)
		mainloop.run()
		return result
	
	def findEventsForTemplatesAndWait(self, event_templates, **kwargs):
		"""
		Execute ZeitgeistClient.find_events_for_templates in a blocking manner.
		"""
		mainloop = self.create_mainloop()
		result = []
		
		def collect_events_and_quit(events):
			result.extend(events)
			mainloop.quit()
		
		self.client.find_events_for_templates(
			event_templates, collect_events_and_quit, **kwargs)
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
			"""
			Remember to wrap callbacks using the asyncTestMethod decorator.
			"""
			
			def __init__(self):
				self._mainloop = GLib.MainLoop()
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
					raise AssertionError(self.failure_message)
		
		mainloop = MainLoopWithFailure()
		if timeout is not None:
			def cb_timeout():
				mainloop.fail("Timed out -- "
					"operations not completed in reasonable time.")
				return False # stop timeout from being called again
			
			# Add an arbitrary timeout so this test won't block if it fails
			GLib.timeout_add_seconds(timeout, cb_timeout)
		
		return mainloop
	
	@staticmethod
	def get_plain_event(ev):
		"""
		Ensure that an Event instance is a Plain Old Python Object (popo),
		without DBus wrappings, etc.
		"""
		if not ev:
			return NULL_EVENT
		for subject in ev.subjects:
			if not subject.current_uri:
				subject.current_uri = subject.uri
			if not subject.current_origin:
				subject.current_origin = subject.origin
		popo = []
		popo.append(list(map(str, ev[0])))
		popo.append([list(map(str, subj)) for subj in ev[1]])
		# We need the check here so that if D-Bus gives us an empty
		# byte array we don't serialize the text "dbus.Array(...)".
		popo.append(str(ev[2]) if ev[2] else '')
		return popo
	
	def assertEventsEqual(self, ev1, ev2):
		ev1 = self.get_plain_event(Event(ev1))
		ev2 = self.get_plain_event(Event(ev2))
		if ev1 is not NULL_EVENT and ev2 is not NULL_EVENT:
			if (ev1[0][0] and not ev2[0][0]) or (ev2[0][0] and not ev1[0][0]):
				ev1[0][0] = ev2[0][0] = "" # delete IDs
		self.assertEqual(ev1, ev2)

class DBusPrivateMessageBus(object):
	# Choose a random number so it's possible to have more than
	# one test running at once.
	DISPLAY = ":%d" % random.randint(20, 100)

	def _run(self):
		os.environ.update({"DISPLAY": self.DISPLAY})
		devnull = open("/dev/null", "w")
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
		self.dbus_config = dict(l.split("=", 1) for l in dbus.communicate()[0].decode().split("\n") if l)
		os.environ.update(self.dbus_config)
		
	def run(self, ignore_errors=False):
		try:
			return self._run()
		except Exception as e:
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
		except Exception as e:
			if ignore_errors:
				return e
			raise

def run():
	unittest.main()

# vim:noexpandtab:ts=4:sw=4
