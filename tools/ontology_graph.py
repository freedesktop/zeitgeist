#! /usr/bin/env python
# -.- coding: utf-8 -.-

# Zeitgeist - Ontology viewer
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

import sys
import pydot

from zeitgeist import datamodel

graphs = {
    'event_interpretation': datamodel.Interpretation.EVENT_INTERPRETATION,
    'event_manifestation':  datamodel.Manifestation.EVENT_MANIFESTATION,
    'subject_interpretation': datamodel._SYMBOLS_BY_URI['Interpretation'],
        # ie. nie.InformationElement,
    'subject_manifestation': datamodel._SYMBOLS_BY_URI['Manifestation']
        # ie. nie.DataObject,
}

USAGE = 'Usage: %s [type] [output]\n\n\tAvailable types: ' % sys.argv[0]
USAGE += ', '.join(graphs.iterkeys())

def introspect(graph, symbol, parent=None, exclude_set=()):
    """
    Adds the given symbol to the graph and recursively does the same
    for its childs.
    """

    if symbol in exclude_set:
        return

    node = pydot.Node(symbol.display_name)
    graph.add_node(node)

    if parent:
        edge = pydot.Edge(parent, node)
        graph.add_edge(edge)

    for subsymbol in symbol.get_children():
        introspect(graph, subsymbol, node, exclude_set)

def generate_graph(symbol, exclude_set):
    """
    Generates a graph starting with the given root symbol.
    """

    print 'Introspecting ontology and generating graph...'
    graph = pydot.Dot(graph_type='graph')
    introspect(graph, symbol, None, exclude_set)
    return graph

def main():
    if len(sys.argv) != 3 or sys.argv[1] not in graphs:
        raise SystemExit, USAGE

    graph_type = sys.argv[1]
    exclude = []
    if graph_type.startswith('subject_'):
        exclude.append(datamodel.Interpretation.EVENT_INTERPRETATION)
        exclude.append(datamodel.Manifestation.EVENT_MANIFESTATION)
    graph = generate_graph(graphs[graph_type], exclude)

    filename = sys.argv[2]
    ext = (filename.rsplit('.', 1) + [None])[1]
    if ext is None:
        filename += '.png'
        ext = 'png'

    if not hasattr(graph, 'write_'+ext):
        raise SystemExit, 'Invalid file extension: %s' % ext
    getattr(graph, 'write_'+ext)(filename)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
