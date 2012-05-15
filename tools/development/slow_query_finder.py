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

from pyevolve import G1DList
from pyevolve import GSimpleGA
from zeitgeist.datamodel import TimeRange, StorageState, ResultType
from zeitgeist.datamodel import Event, Subject, Interpretation, Manifestation
import benchmark as engine
import time

# Chromosome to data mapping:
# 0, 1 - Timerange begin and end. If both are zero, we use timerange.always()
# 2 - The search type. Anything over 30 is a dead individual.
# 3-5 - Specify template properties. Anything besides 0 and 1 is dead.
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
  searchType = chromosome[2]%30

  eventTemplate = {}
  subjectTemplate = {}

  if chromosome[3]%2 == 1:
    subjectTemplate['interpretation'] = Interpretation.VIDEO
  if chromosome[4]%2 == 1:
    subjectTemplate['manifestation'] = Manifestation.FILE_DATA_OBJECT
  if chromosome[5]%2 == 1:
    eventTemplate['actor'] = "application://google-chrome.desktop"

  templates = [Event.new_for_values(subjects=[Subject.new_for_values(**subjectTemplate)], **eventTemplate)]

  return (timerange, templates, storage, numResults, searchType)
  
def eval_func(chromosome):
  query = buildQuery(chromosome)
  if query is None:
    return 0

  start = time.time()
  results = engine.find_events(*query)
  return (time.time() - start)*1000

genome = G1DList.G1DList(6)
genome.evaluator.set(eval_func)
ga = GSimpleGA.GSimpleGA(genome)
ga.evolve(freq_stats = 1)
query = buildQuery(ga.bestIndividual())
assert query is not None
print query, len(engine.find_events(*query))
