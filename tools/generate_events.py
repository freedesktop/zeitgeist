#! /usr/bin/env python
# -.- coding: utf-8 -.-

# Zeitgeist - Insert random events into the database
#
# Copyright © 2012 Canonical Ltd.
#             By Siegfried-A. Gevatter <siegfried.gevatter@collabora.co.uk>
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
#
# #############################################################################
# WARNING: Make sure you launch Zeitgeist with ZEITGEIST_DATA_PATH set if
#          you don't want to fill your real database!
#
#          See ./tools/run_fake_zeitgeist.sh for a convenient way of testing
#          Zeitgeist.
# #############################################################################

import os
import sys
import time
import random
from collections import deque
from gi.repository import GLib, GObject

from zeitgeist import mimetypes
from zeitgeist.datamodel import *
from zeitgeist.client import ZeitgeistDBusInterface

class EventGenerator:

    NUM_WORDS = 1000
    NUM_SIMULTANEOUS_URIS = 1000

    _words = None
    _mimetypes = None
    _desktop_files = None
    _schemas = None
    _uri_table = None
    _timestamp_generator = None

    def __init__(self):
        # Initialize a pool of random words for use in URIs, etc.
        dictionary_words = map(str.strip,
            open('/usr/share/dict/words').readlines())
        dictionary_words = filter(lambda x: '\'s' not in x, dictionary_words)
        self._words = random.sample(dictionary_words, self.NUM_WORDS)

        # Initialize timestamp generator
        self._timestamp_generator = TimestampGenerator()

        # Initialize a pool of MIME-Types
        self._mimetypes = mimetypes.MIMES.keys()

        # Initialize a pool of application names
        self._desktop_files =  filter(lambda actor: actor.endswith('.desktop'),
            os.listdir('/usr/share/applications'))

        # Initialize a list of URI schemas
        self._schemas = ('application', 'davs', 'http', 'https', 'ftp')

        # Initialize a cache of URIs
        self._uri_table = deque(maxlen=self.NUM_SIMULTANEOUS_URIS)

    def get_word(self):
        # FIXME: add numbers and stuff?
        return random.choice(self._words)

    def get_extension(self):
        if random.random() < 0.8:
            extensions = [
                'odt', 'odp', 'doc',
                'oga', 'ogv', 'mp3'
                'png', 'jpg', 'gif', 'tiff'
                'html', 'xml', 'txt'
                'py', 'c', 'cpp', 'js', 'vala'
            ]
        else:
            extensions = self._words
        return filter(str.isalpha, random.choice(extensions))

    def get_path(self, force_directory=False):
        path = ''
        num_parts = 1 + abs(int(random.gauss(3, 3)))
        for i in range(num_parts):
            path += '/%s' % self.get_word()
        if random.random() < 0.9 and not force_directory:
            path += '.%s' % self.get_extension()
        return path

    def get_schema(self):
        rand = random.random()
        if rand < 0.005:
            return '%s://' % random.choice(self._words)
        elif rand < 0.4:
            return '%s://' % random.choice(self._schemas)
        else:
            return 'file:///'

    def generate_uri(self):
        file_uri = GLib.filename_to_uri(self.get_path(), None)
        return self.get_schema() + file_uri[8:]

    def get_uri(self):
        """
        We keep a cache of NUM_SIMULATENOUS_URIS uris for reuse. Every access
        has a 1% chance of replacing a URI in the table with a new one.
        """
        index = random.randint(0, self.NUM_SIMULTANEOUS_URIS)
        if index >= len(self._uri_table):
            # The URI table isn't fully initialized yet...
            uri = self.generate_uri()
            self._uri_table.append(uri)
            return uri
        if random.random() < 0.01:
            # Generate a new URI
            self._uri_table[index] = self.generate_uri()
        return self._uri_table[index]

    def get_text(self):
        num_words = abs(int(random.gauss(4, 3)))
        return ' '.join(self.get_word() for i in range(num_words))

    def get_subject_origin(self, uri):
        scheme = GLib.uri_parse_scheme(uri)
        if scheme == 'file':
            return GLib.path_get_dirname(uri)
        elif scheme in ('http', 'https'):
            scheme, domain = uri.split('://', 1)
            return '%s://%s' % (scheme, domain.split('/', 1)[0])
        else:
            return GLib.filename_to_uri(
                self.get_path(force_directory=True), None)

    def get_event_origin(self):
        if random.random() < 0.005:
            return self.get_uri()
        return ''

    def get_actor(self):
        return 'application://%s' % random.choice(self._desktop_files)

    def get_timestamp(self):
        return self._timestamp_generator.next()

    def get_event_interpretation(self):
        interpretations = Interpretation.EVENT_INTERPRETATION.get_children()
        return random.choice(list(interpretations))

    def get_subject_interpretation(self):
        ev_interp = Interpretation.EVENT_INTERPRETATION.get_children()
        subj_interp = set(Interpretation.get_children())
        subj_interp.difference_update(ev_interp)
        return random.choice(list(subj_interp))

    def get_event_manifestation(self):
        if random.random() < 0.3:
            manifestations = Manifestation.EVENT_MANIFESTATION.get_children()
            return random.choice(list(manifestations))
        else:
            return Manifestation.USER_ACTIVITY

    def get_subject_manifestation(self):
        ev_manif = Manifestation.EVENT_MANIFESTATION.get_children()
        subj_manif = set(Interpretation.get_children())
        subj_manif.difference_update(ev_manif)
        return random.choice(list(subj_manif))

    def get_subject(self, event_interpretation):
        uri = self.get_uri()

        subject = Subject.new_for_values(
            uri            = uri,
            current_uri    = uri,
            interpretation = self.get_subject_interpretation(),
            manifestation  = self.get_subject_manifestation(),
            origin         = self.get_subject_origin(uri),
            mimetype       = random.choice(self._mimetypes),
            text           = self.get_text(),
            storage        = "")

        if event_interpretation == Interpretation.MOVE_EVENT:
            while subject.uri == subject.current_uri:
                subject.current_uri = self.get_uri()

        return subject

    def get_event(self):
        event_interpretation = self.get_event_interpretation()
        event = Event.new_for_values(
            timestamp      = self.get_timestamp(),
            interpretation = event_interpretation,
            manifestation  = self.get_event_manifestation(),
            actor          = self.get_actor(),
            origin         = self.get_event_origin())

        num_subjects = max(1, abs(int(random.gauss(1, 1))))
        while len(event.subjects) < num_subjects:
            subject = self.get_subject(event_interpretation)
            if subject.uri not in (x.uri for x in event.get_subjects()):
                # events with two subjects having the same URI aren't supported
                event.append_subject(subject)

        return event

class TimestampGenerator():

    MAX_EVENT_AGE = 366*24*3600*1000

    _start_time = None
    _lowest_limit = None

    _next_time = None

    def __init__(self):
        self._start_time = self.current_time() - (7*24*3600*1000)
        self._lowest_time = self._start_time - self.MAX_EVENT_AGE
        self._next_time = self._start_time

    def next(self):
        if random.random() < 0.005:
            return random.randint(self._lowest_time, self.current_time())
        return_time = self._next_time
        self._next_time += abs(int(random.gauss(1000, 5000)))
        return return_time

    @staticmethod
    def current_time():
        return int(time.time() * 1000)

class EventInserter():

    BUFFER_SIZE = 1000

    _log = None
    _buffer = None
    _events_inserted = None

    def __init__(self):
        self._log = ZeitgeistDBusInterface()
        self._buffer = []
        self._events_inserted = 0

    def insert(self, event):
        buffer_full = len(self._buffer) >= self.BUFFER_SIZE
        if buffer_full:
            self.flush()
        self._buffer.append(event)
        return buffer_full

    def flush(self):
        if self._buffer:
            self._log.InsertEvents(self._buffer)
            self._events_inserted += len(self._buffer)
            self._buffer = []

    def get_insertion_count(self):
        return self._events_inserted

def main():
    limit = '10000000' if len(sys.argv) < 2 else sys.argv[1]
    if len(sys.argv) > 2 or not limit.isdigit():
        print "Usage: %s [<num_events>]" % sys.argv[0]
        sys.exit(1)
    limit = int(limit)

    event_inserter = EventInserter()
    try:
        generator = EventGenerator()
        for i in xrange(limit):
            event = generator.get_event()
            event.payload = 'generate_events.py'
            if event_inserter.insert(event):
                print "Inserted %d events." % i
    except KeyboardInterrupt:
        pass
    event_inserter.flush()
    print "Inserted %d events. Done." % event_inserter.get_insertion_count()

if __name__ == '__main__':
    main()
