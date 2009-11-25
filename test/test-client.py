#! /usr/bin/python

# Update python path to use local zeitgeist module
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from zeitgeist.datamodel import *
from zeitgeist.client import *

iface = ZeitgeistDBusInterface()

#
# Create an event
#
ev = Event.new_for_values(timestamp=123,
			interpretation=Interpretation.VISIT_EVENT.uri,
			manifestation=Manifestation.USER_ACTIVITY.uri,
			actor="Freak Mamma")
subj = Subject.new_for_values(uri="void://foobar",
			interpretation=Interpretation.DOCUMENT.uri,
			manifestation=Manifestation.FILE.uri)#,
			#origin="adsf",
			#mimetype="text/plain",
			#storage="bleh")
			
ev.append_subject(subj)

#
# Log event
#
print "Inserting event"
ids = iface.InsertEvents([ev])
print "Inserted events with ids %s" % ids

#
# Pull the event out again
#
events = iface.GetEvents(ids)
print "Got events back %s" % events

#
# Find event via a search
#
template = (["","","","",""],["","","","","","",""])
found_ids = iface.FindEventIds((0, 200), [template,], 0, 10, 1)
print "Found event ids: %s" % found_ids
