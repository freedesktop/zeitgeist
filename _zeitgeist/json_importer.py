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

import os.path
from simplejson import *

from zeitgeist.datamodel import Event, Subject

def dict2event(d):
	ev = Event()
	ev[0][Event.Id] = d.get("id", None)
	ev.timestamp = str(d.get("timestamp", None))
	ev.interpretation = str(d.get("interpretation", None))
	ev.manifestation = str(d.get("manifestation", None))
	ev.actor = str(d.get("actor", None))
	ev.payload = str(d.get("payload", None))
	
	subjects = d.get("subjects", [])
	for sd in subjects:
		subj = Subject()
		subj.uri = str(sd.get("uri", None))
		subj.interpretation = str(sd.get("interpretation", None))
		subj.manifestation = str(sd.get("manifestation", None))
		subj.origin = str(sd.get("origin", None))
		subj.mimetype = str(sd.get("mimetype", None))
		subj.text = str(sd.get("text", None))
		subj.storage = str(sd.get("storage", None))
		ev.append_subject(subj)
	return ev
	

def import_events(path, engine):
	"""
	Load a collection of JSON event definitions into 'engine'. Fx:
	
	    import_events("test/data/single_event.js", self.engine)
	"""	
	json_string = "".join(file(path).readlines())
	decoder = JSONDecoder()
	json = decoder.decode(json_string)
	
	events = []
	for event_node in json:
		events.append(dict2event(event_node))
	
	engine.insert_events(events)
