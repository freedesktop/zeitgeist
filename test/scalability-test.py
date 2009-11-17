#! /usr/bin/python

#
# Tests inserting and querying with huge amounts of events
#

# Update python path to use local zeitgeist module
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from zeitgeist.datamodel import *
from zeitgeist.dbusutils import *

REPORT = \
"""EVENT METADATA:
Number of events: %s
Number of event interpretations: %s
Number of event manifestations: %s
Number of event actors: %s
Event payload frequency: %s
Event subject frequency: %s

SUBJECT METADATA:
Number of subjects: %s
Number if subject interpretations: %s
Number of subject manifestations: %s
Number if subject mimetypes: %s
Number of subject origins: %s
Number of subject storage mediums: %s
Subject text frequency: %s"""

class EventGenerator:
	"""
	Generate a collection of random events. The entire event set is
	pre-compiled in order to not influence benchmarks etc. with
	event generation time.
	"""
	def __init__ (self,
			num_events=100000,
			num_event_interpretations=10,
			num_event_manifestations=5,
			num_event_actors=100,
			num_subjects=10000,
			num_subject_interpretations=100,
			num_subject_manifestations=50,
			num_subject_mimetypes=50,
			num_subject_origins=70000,
			num_subject_storages=8,
			subject_freq=1.0,
			subject_text_freq=0.0,
			payload_freq=0.0):
		
		self.subject_freq = subject_freq
		self.subject_text_freq = subject_text_freq
		self.payload_freq = payload_freq
		
		# Event metadata
		self.event_interpretations = ["interpretation%s" % i for i in range(num_event_interpretations)]
		self.event_manifestations = ["manifestation%s" % i for i in range(num_event_manifestations)]
		self.event_actors = ["actor%s" % i for i in range(num_event_actors)]
		
		# Subject data
		self.subject_uris = ["subject%s" % i for i in range(num_subjects)]
		self.subject_interpretations = ["subject_interpretation%s" % i for i in range(num_subject_interpretations)]
		self.subject_manifestations = ["subject_manifestation%s" % i for i in range(num_subject_manifestations)]
		self.subject_mimetypes = ["subject_mimetype%s" % i for i in range(num_subject_mimetypes)]
		self.subject_origins = ["subject_origin%s" % i for i in range(num_subject_origins)]
		self.subject_storages = ["subject_storage%s" % i for i in range(num_subject_storages)]
		
		# Compile all the events ahead of time in order not to
		# influence query/insertion time.
		# We give each event a bogus timestamp in order to avoid
		# duplicate event exceptions
		self.events = []
		for i in range(num_events):
			ev = Event()
			ev.timestamp = i
			ev.interpretation = self.event_interpretations[i % len(self.event_interpretations)]
			ev.manifestation = self.event_manifestations[i % len(self.event_manifestations)]
			ev.actor = self.event_actors[i % len(self.event_actors)]
			
			#if payload_freq > 0 and  (int((1/payload_freq)*num_events) % i == 0):
			#	event.payload = "payload%s" % i
				
			for j in range(self._calc_num_subjects()):
				subj = Subject()
				subj.uri = self.subject_uris[(i+j) % num_subjects]
				subj.interpretation = self.subject_interpretations[(i+j) % len(self.subject_interpretations)]
				subj.manifestation = self.subject_manifestations[(i+j) % len(self.subject_manifestations)]
				subj.mimetype = self.subject_mimetypes[(i+j) % len(self.subject_mimetypes)]
				subj.origin = self.subject_origins[(i+j) % len(self.subject_origins)]
				subj.storage = self.subject_storages[(i+j) % len(self.subject_storages)]
				
				#if subject_text_freq > 0 and  (int((1/subject_text_freq)*num_subjects) % (i+j) == 0):
				#	event.payload = "payload%s" % i
				
				ev.subjects.append(subj)
			self.events.append(ev)
	
	def __iter__ (self):
		return self.events.__iter__()
	
	def __len__ (self):
		return self.events.__len__()
	
	def __getitem__ (self, key):
		return self.events[key]
	
	def _calc_num_subjects(self):
		# FIXME: DO this right
		return 1
	
	def report(self):
		return REPORT % (len(self), len(self.event_interpretations), len(self.event_manifestations), len(self.event_actors), self.payload_freq, self.subject_freq, len(self.subject_uris), len(self.subject_interpretations), len(self.subject_manifestations), len(self.subject_mimetypes), len(self.subject_origins), len(self.subject_storages), self.subject_text_freq)
 

if __name__ == "__main__":
	import sys, time
	events = EventGenerator(10000)
	print events.report() + "\n"
	log = DBusInterface()
	start = time.time()
	
	# Insert events in batches of 10
	for i in range(len(events) / 10):
		batch = [events[i*10 + j] for j in range(10)]
		log.InsertEvents(batch)
		
	print "Insertion time: %ss" % (time.time() - start)
