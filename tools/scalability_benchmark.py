#! /usr/bin/env python
# -.- coding: utf-8 -.-

# Zeitgeist - Scalability benchmark
#
# Copyright © 2012 Collabora Ltd.
#                  By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
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
#          you don't want to fill your real database with fake events!
#
#          See ./tools/run_fake_zeitgeist.sh for a convenient way of testing
#          Zeitgeist.
# #############################################################################

import sys
import time
from graphy.backends import google_chart_api

from generate_events import EventInserter, EventGenerator
from zeitgeist.client import ZeitgeistDBusInterface
from zeitgeist.datamodel import *

class ScalabilityBenchmark:

    _event_inserter = None
    _event_generator = None
    _zeitgeist_log = None

    def __init__(self):
        self._event_inserter = EventInserter()
        self._event_generator = EventGenerator()
        self._zeitgeist_log = ZeitgeistDBusInterface()

    def _insert_events(self, num_events):
        for i in xrange(num_events):
            event = self._event_generator.get_event()
            event.payload = 'scalability_benchmark.py'
            self._event_inserter.insert(event)
        self._event_inserter.flush()

    def run(self, num_iterations=50, events_per_iteration=5000, sleep_time=0):
        """
        Runs a series of iterations during each of which a fixed number of
        events are inserted into Zeitgeist. After the insertions, there's a
        delay of the given number of seconds and then some queries are done.

        The return value is a tuple containing (in seconds):
         - a list with the insertion time for each iteration
         - a list of lists with the query times for each iteration for:
            - most recent events
            - most recent subjects
            - most popular subjects
        """
        print >>sys.stderr, \
            "Starting %d-iteration test with %d events per interation." % (
            num_iterations, events_per_iteration)

        insertion_times = []
        query_times = ([], [], [])

        for it in xrange(num_iterations):
            print >>sys.stderr, "Starting iteration %d..." % (it+1)
            # Insert events
            start_time = time.time()
            self._insert_events(events_per_iteration)
            iteration_time = time.time() - start_time
            insertion_times.append(iteration_time)

            # Wait the given amount of time
            if sleep_time:
                time.sleep(sleep_time)

            # Queries
            queries = (ResultType.MostRecentEvents,
                ResultType.MostRecentSubjects, ResultType.MostPopularSubjects)
            for i, result_type in enumerate(queries):
                start_time = time.time()
                self._zeitgeist_log.FindEventIds(TimeRange.always(), [], StorageState.Any,
                    50, ResultType.MostRecentEvents)
                query_times[i].append(time.time() - start_time)

        return (insertion_times,) + query_times

def main(iterations=50, events_per_iteration=5000):
    data = ScalabilityBenchmark().run(iterations, events_per_iteration, 5)
    chart = google_chart_api.LineChart()
    chart.AddLine(data[0], label="Insertion time")
    chart.AddLine(data[1], label="Query time (50 most recent events)")
    chart.AddLine(data[2], label="Query time (50 most recent subjects)")
    chart.AddLine(data[3], label="Query time (50 most popular subjects)")
    chart.bottom.labels = [events_per_iteration*(i+1) for i in range(len(data[0]))]
    print "TIMES:\n----"
    print data
    print "\nCHART:\n----"
    print chart.display.Img(800, 250)

if __name__ == '__main__':
    try:
        main(10, 5000)
    except KeyboardInterrupt:
        pass
