#! /usr/bin/env python
# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2010 Markus Korn <thekorn@gmx.net>
# Copyright © 2011 Collabora Ltd.
#                  By Seif Lotfy <seif@lotfy.com>
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

# USAGE
#
# To run the benchmarks on a certain branch of zeitgeist make sure this
# branch is in PYTHONPATH.
# To benchmark and output overall to 'output.json' run
#  ./query_overalls.py -o output.json
# If you already have data in the output file and want to merge both
# data sets (build avg.) run
#  ./query_overalls.py -m -o output.json
# To plot the data use the '--plot' argument, multible '--plot' arguments
# will define multible series.
#  ./query_overalls.py --plot output.json --plot output1.json -o plot.svg
# In short, a run always looks like:
#  PYTHONPATH=../trunk tools/development/query_overalls.py --name "lp:zeitgeist" -o trunk.json \
#       --queries tools/development/query_sets/timerange_always.txt
#  PYTHONPATH=. tools/development/query_overalls.py --name "lp:some-branch" -o somebranch.json
#  PYTHONPATH=. tools/development/query_overalls.py --plot somebranch.json --plot trunk.json -o benchmark.svg

import os
import random
import time
import json
import sys
import logging

from optparse import OptionParser
from logging import handlers
from collections import defaultdict

from zeitgeist.datamodel import TimeRange, StorageState, ResultType
from zeitgeist.datamodel import Event
import benchmark as engine

from cairoplot import vertical_bar_plot


class QueryPlanHandler(handlers.MemoryHandler):
    
    @staticmethod
    def get_plan(msg):
        if "SELECT id FROM event_view" not in msg:
            return None
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
    return engine
    
def get_query_set(source):
    for line in open(source):
        yield line.strip()

def get_cmdline():
    parser = OptionParser()
    parser.add_option("-o", dest="output", help="write output to FILE", metavar="FILE")
    parser.add_option("--queries", dest="queryset", help="run all queries in FILE", metavar="FILE")
    parser.add_option("--name", dest="name", help="name of the data series", metavar="NAME")
    parser.add_option("-i", dest="isolated", action="store_true",
        default=False, help="run each query isolated")
    parser.add_option("-m", dest="merge", action="store_true",
        default=False, help="if the datafile already contains data the new data gets merged")
    parser.add_option("--plot", dest="plot_files", metavar="DATA_FILE",
        action="append", type="str")
    parser.add_option("--type", dest="type", help="type of plot")
    (options, args) = parser.parse_args()
    assert not args
    return options
    
def get_name(data, alternative_name):
    try:
        return data["__metadata__"]["name"]
    except:
        return alternative_name
        
def get_data(dataset, query, key):
    try:
        return float(dataset[query][key])
    except:
        return 0.0
        
def compare_queries(a, b):
    result = cmp(a.strip().split()[-1], b.strip().split()[-1])
    if result != 0:
        return result
    return cmp(a[0], b[0])
    
def plot(output_filename, plot_type, *data_files):
    raw_data = map(lambda x: json.load(open(x)), data_files)
    series_labels = map(lambda x: get_name(x[1], data_files[x[0]]), enumerate(raw_data))
    queries = sorted(
        filter(lambda x: x != "__metadata__", set(sum([d.keys() for d in raw_data], []))),
        cmp=compare_queries
    )
    data = []
    max_value = 0
    no_index = list()
    style = plot_type
    for n, query in enumerate(queries):
        x = [get_data(d, query, style) for d in raw_data]
        print x
        y = max(x)
        idx_border = [not d.get(query, {}).get("uses_index", True) for d in raw_data]
        for i, b in enumerate(idx_border):
            if b:
                no_index.append((n, i))
        if y > max_value:
            max_value = y
        data.append(x)
    y_parts = max_value / float(4)
    y_labels = ["%.5fs" %(i*y_parts) for i in range(5)]
    vertical_bar_plot(
        output_filename, data, len(queries)*400, 600,
        x_labels=queries, y_labels=y_labels,
        grid=True, series_labels=series_labels, bar_borders=no_index)
    

if __name__ == "__main__":
    options = get_cmdline()
    if options.plot_files:
        if options.type in ("marsh_time", "get_events_time", "find_ids_time", "find_events", "overall"):
            assert options.output
            plot(options.output, options.type, *options.plot_files)
        else:
            print "please specify plot type (marsh_time, get_events_time, find_ids_time, find_events, overall)"
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
        logging.basicConfig(level=logging.DEBUG)
        for query in get_query_set(options.queryset):
            args = eval(query)
            start_time = time.time()
            logging.getLogger("").removeHandler(logging.getLogger("").handlers[0])
            handler = QueryPlanHandler()
            logging.getLogger("").addHandler(handler)
            results = {}
            for i in xrange (50):
                t1 = time.time()
                temp = engine.find_events(*args)
                temp["overall"] = time.time() - t1
                if len(results.keys()) == 0:
                    for key in results.keys():
                        temp[key] = temp[key]
                    results = temp
                else:
                    for key in temp.keys():
                        if key != "events":
                            results[key] += temp[key]
                            print results[key]
            
            for key in temp.keys():
                if key != "events":
                    results[key] = results[key]/50
            
            print (results.keys())
            
            events = results["events"]
            run_time = results["find_events"]
            find_ids_time = results["overall"]
            find_events_time = results["find_event_ids"]
            get_events_time = results["get_events"]
            marsh_time = results["marsh_events"]
            
            print "===>", find_ids_time
            
            if query in existing_data and options.merge:
                print "=================================="
                counter = existing_data[query].get("counter", 1)
                old_time = existing_data[query]["overall"]
                run_time = (old_time * counter + run_time)/(counter + 1)
                
                result[query] = {
                    "overall": run_time,
                    "counter": counter + 1,
                    "find_ids_time": find_ids_time,
                    "get_events_time": get_events_time,
                    "find_events": find_events_time,
                    "marsh_time": marsh_time,
                }
            else:
                result[query] = {
                    "overall": run_time,
                    "find_ids_time": find_ids_time,
                    "get_events_time": get_events_time,
                    "find_events": find_events_time,
                    "marsh_time": marsh_time,
                }
        if options.output:
            f = open(options.output, "w")
        else:
            f = sys.stdout
        try:
            json.dump(result, f, indent=4)
        finally:
            f.close()
