#! /usr/bin/env python
# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2010 Markus Korn <thekorn@gmx.net>
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

# usage
#  ./query_timings.py -o output.json
#  ./query_timings.py -m -o output.json
#  ./query_timings.py --plot output.json --plot output1.json -o plot.svg

import os
import random
import time
import json
import sys
import logging

from optparse import OptionParser
from logging import handlers

from zeitgeist.datamodel import TimeRange, StorageState, ResultType
from zeitgeist.datamodel import Event
from _zeitgeist.engine import constants
from _zeitgeist.engine import get_engine
from _zeitgeist.engine.sql import UnicodeCursor

from cairoplot import vertical_bar_plot

QUERIES = [
    "TimeRange.always(), [], StorageState.Any, 6, ResultType.MostRecentEvents",
    "TimeRange.always(), [], StorageState.Any, 6, ResultType.LeastRecentEvents",
    "TimeRange.always(), [], StorageState.Any, 6, ResultType.MostRecentSubjects",
    "TimeRange.always(), [], StorageState.Any, 6, ResultType.LeastRecentSubjects",
    "TimeRange.always(), [], StorageState.Any, 6, ResultType.MostPopularSubjects",
    "TimeRange.always(), [], StorageState.Any, 6, ResultType.LeastPopularSubjects",
    "TimeRange.always(), [], StorageState.Any, 6, ResultType.MostPopularActor",
    "TimeRange.always(), [], StorageState.Any, 6, ResultType.LeastPopularActor",
    "TimeRange.always(), [], StorageState.Any, 6, ResultType.MostRecentActor",
    "TimeRange.always(), [], StorageState.Any, 6, ResultType.LeastRecentActor",
    "TimeRange.always(), [], StorageState.Any, 6, ResultType.MostRecentOrigin",
    "TimeRange.always(), [], StorageState.Any, 6, ResultType.LeastRecentOrigin",
    "TimeRange.always(), [], StorageState.Any, 6, ResultType.MostPopularOrigin",
    "TimeRange.always(), [], StorageState.Any, 6, ResultType.LeastPopularOrigin",
    "TimeRange.always(), [], StorageState.Any, 6, ResultType.OldestActor",
    "TimeRange.always(), [], StorageState.Any, 6, ResultType.MostRecentSubjectInterpretation",
    "TimeRange.always(), [], StorageState.Any, 6, ResultType.LeastRecentSubjectInterpretation",
    "TimeRange.always(), [], StorageState.Any, 6, ResultType.MostPopularSubjectInterpretation",
    "TimeRange.always(), [], StorageState.Any, 6, ResultType.LeastPopularSubjectInterpretation",
    "TimeRange.always(), [], StorageState.Any, 6, ResultType.MostRecentMimeType",
    "TimeRange.always(), [], StorageState.Any, 6, ResultType.LeastRecentMimeType",
    "TimeRange.always(), [], StorageState.Any, 6, ResultType.MostPopularMimeType",
    "TimeRange.always(), [], StorageState.Any, 6, ResultType.LeastPopularMimeType",
]

class QueryPlanHandler(handlers.MemoryHandler):
    
    @staticmethod
    def get_plan(msg):
        msg = msg.splitlines()
        if not "PLAN:" in msg:
            return None
        for plan in msg[msg.index("PLAN:")+1:]:
            if "INDEX" not in plan and "PRIMARY KEY" not in plan:
                return False
        return True
        
    def __init__(self):
        handlers.MemoryHandler.__init__(self, 200000, logging.DEBUG)
        self.uses_index = None
        
    def emit(self, record):
        x = self.get_plan(record.msg)
        if x is not None:
            if not x or self.uses_index is None:
                self.uses_index = x
        return handlers.MemoryHandler.emit(self, record)

def get_reference_engine():
    # for now we are building an in memory db with some content
    # in the future we should use some pre-build reference db
    os.environ["ZEITGEIST_DEFAULT_EXTENSIONS"] = ""
    os.environ["ZEITGEIST_EXTRA_EXTENSIONS"] = ""
    os.environ["ZEITGEIST_DEBUG_QUERY_PLANS"] = ""

    constants.DEFAULT_EXTENSIONS = []
    constants.DATABASE_FILE = ":memory:"
            
    engine = get_engine()
    
    COUNTER = dict.fromkeys(range(100), 0)
    def make_actor(id):
        i = random.randint(0, 99)
        COUNTER[i] += 1
        return u"applications://%i" %i
    
    min_timestamp = 0
    #~ max_timestamp = 500
    max_timestamp = 50000
    
    nums = range(min_timestamp, max_timestamp, 500)
    while len(nums) > 1:
        start = nums.pop(0)
        end = nums[0]
        events = [
            Event.new_for_values(
                actor=make_actor(i), timestamp="%i" %i, subject_uri=u"http://%i" %i
            ) for i in range(start, end)]
        engine.insert_events(events)
    return engine

def get_cmdline():
    parser = OptionParser()
    parser.add_option("-o", dest="output", help="write output to FILE", metavar="FILE")
    parser.add_option("--name", dest="name", help="name of the data series", metavar="NAME")
    parser.add_option("-i", dest="isolated", action="store_true",
        default=False, help="run each query isolated")
    parser.add_option("-m", dest="merge", action="store_true",
        default=False, help="if the datafile already contains data the new data gets merged")
    parser.add_option("--plot", dest="plot_files", metavar="DATA_FILE",
        action="append", type="str")
    (options, args) = parser.parse_args()
    assert not args
    return options
    
def get_name(data, alternative_name):
    try:
        return data["__metadata__"]["name"]
    except:
        return alternative_name
    
def plot(output_filename, *data_files):
    raw_data = map(lambda x: json.load(open(x)), data_files)
    series_labels = map(lambda x: get_name(x[1], data_files[x[0]]), enumerate(raw_data))
    queries = filter(lambda x: x != "__metadata__", sorted(set(sum([d.keys() for d in raw_data], []))))
    data = []
    max_value = 0
    for query in queries:
        x = [float(d[query]["timing"]) for d in raw_data]
        y = max(x)
        if y > max_value:
            max_value = y
        data.append(x)
    y_parts = max_value / float(4)
    y_labels = ["%.2fs" %(i*y_parts) for i in range(5)]
    vertical_bar_plot(
        output_filename, data, len(QUERIES)*400, 600,
        x_labels=queries, y_labels=y_labels,
        grid=True, series_labels=series_labels)
    

if __name__ == "__main__":
    options = get_cmdline()
    if options.plot_files:
        assert options.output
        plot(options.output, *options.plot_files)
    else:
        engine = get_reference_engine()
        result = {}
        if options.name:
            result["__metadata__"] = {
                "name": options.name,
            }
        if options.output and os.path.exists(options.output):
            existing_data = json.load(open(options.output))
        else:
            existing_data = {}
        UnicodeCursor.debug_explain = True
        logging.basicConfig(level=logging.DEBUG)
        for query in QUERIES:
            args = eval(query)
            start_time = time.time()
            logging.getLogger("").removeHandler(logging.getLogger("").handlers[0])
            handler = QueryPlanHandler()
            logging.getLogger("").addHandler(handler)
            ids = engine.find_events(*args)
            run_time = time.time() - start_time
            if query in existing_data and options.merge:
                counter = existing_data[query].get("counter", 1)
                old_time = existing_data[query]["timing"]
                run_time = (old_time * counter + run_time)/(counter + 1)
                result[query] = {
                    "timing": run_time,
                    "counter": counter + 1,
                    "uses_index": handler.uses_index,
                }
            else:
                result[query] = {
                    "timing": run_time,
                    "uses_index": handler.uses_index,
                }
        if options.output:
            f = open(options.output, "w")
        else:
            f = sys.stdout
        try:
            json.dump(result, f, indent=4)
        finally:
            f.close()
