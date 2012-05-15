#! /usr/bin/env python
# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2011 Collabora Ltd.
#                  By Trever Fischer <trever.fischer@collabora.co.uk>
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
import random
from pyevolve import G1DList
from pyevolve import GSimpleGA
from zeitgeist.datamodel import TimeRange, StorageState, ResultType
from zeitgeist.datamodel import Event, Subject, Interpretation, Manifestation
import benchmark as engine
import time

# Chromosome to data mapping:
# 0, 1 - Timerange begin and end. If both are zero, we use timerange.always()
# 2 - The search type. Anything over 30 is a dead individual.
# 3-5 - Specify template properties. Even is yes, odd is no
# 3 - Specify a subject interpretation
# 4 - Specify a subject manifestation
# 5 - Specify an event actor
def buildQuery(chromosome):
  storage = StorageState.Any
  numResults = 10
  if chromosome[0] == 0 or chromosome[1] == 0:
    timerange = TimeRange.always()
  else:
    timerange = (chromosome[0]*60*60*24, chromosome[1]*60*60*24)
    if timerange[0] > timerange[1]:
       timerange = (timerange[1], timerange[0])
  searchType = chromosome[2]%30

  eventTemplate = {}
  subjectTemplate = {}

  if chromosome[3]%2 == 0:
    subjectTemplate['interpretation'] = random.choice(list(Interpretation.EVENT_INTERPRETATION.get_children()))
  if chromosome[4]%2 == 0:
    subjectTemplate['manifestation'] = random.choice(list(Manifestation.EVENT_MANIFESTATION.get_children()))
  if chromosome[5]%2 == 0:
    eventTemplate['actor'] = "application://google-chrome.desktop"
  if chromosome[6]%2 == 0:
    subjectTemplate['origin'] = "http://google.com"
  if chromosome[7]%2 == 0:
    subjectTemplate['uri'] = "http://google.com"
  if chromosome[8]%2 == 0:
    subjectTemplate['mimetype'] = "text/html"
  if chromosome[9]%2 == 0:
    subjectTemplate['text'] = "fish"
  if chromosome[10]%2 == 0:
    eventTemplate['manifestation'] = random.choice(list(Manifestation.EVENT_MANIFESTATION.get_children()))
  if chromosome[11]%2 == 0:
    eventTemplate['interpretation'] = random.choice(list(Interpretation.EVENT_INTERPRETATION.get_children()))
  templates = [Event.new_for_values(subjects=[Subject.new_for_values(**subjectTemplate)], **eventTemplate)]

  return (timerange, templates, storage, numResults, searchType)
  
def eval_func(chromosome):
  query = buildQuery(chromosome)
  if query is None:
    return 0

  start = time.time()
  results = engine.find_events(*query)
  overall = (time.time() - start)
  return (results["find_events"]*2+results["find_event_ids"]*4+results["get_events"])*1000

genome = G1DList.G1DList(12)
genome.evaluator.set(eval_func)
ga = GSimpleGA.GSimpleGA(genome)
ga.evolve(freq_stats = 1)
query = buildQuery(ga.bestIndividual())
print ga.bestIndividual()
print query
print "Result count: %d"%(len(engine.find_events(*query)))
