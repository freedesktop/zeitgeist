# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Markus Korn <thekorn@gmx.de>
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

from rdflib.syntax.serializers.RecursiveSerializer import RecursiveSerializer
from rdflib import RDF, RDFS
from rdflib.Namespace import Namespace

NIENS = Namespace("http://www.semanticdesktop.org/ontologies/2007/01/19/nie#")

import sys, pprint

def escape_chars(text, strip=True):
	text = text.replace("'", "\\'")
	text = text.replace('"', '\\"')
	if strip:
		text = text.strip()
	return text
	
def replace_items(item_set, item_map):
	if not item_set:
		return
	for item, value in item_map.iteritems():
		try:
			item_set.remove(item)
		except KeyError:
			# item is not in set
			continue
		else:
			# item was in set, replace it with value
			item_set.add(value)


class PythonSerializer(RecursiveSerializer):

	def _create_symbol_collection(self, stream, collection_type):
		collection_name = escape_chars(str(collection_type).split("#")[-1])
		comments = list(self.store.objects(collection_type, RDFS.comment))
		doc = escape_chars(comments[0] if comments else "")
		labels = list(self.store.objects(collection_type, RDFS.label))
		display_name = escape_chars(labels[0] if labels else collection_name)
		root_type = set(map(str, self.store.objects(collection_type, RDFS.subClassOf)))
		replace_items(root_type,
			{str(NIENS["InformationElement"]): "Interpretation", str(NIENS["DataObject"]): "Manifestation"})
		if root_type:
			stream.write(
				#TBD: not sure ?!
				"%s = Symbol('%s', parent=%r, uri='%s', doc='%s')\n" %(collection_name,
					display_name, root_type, collection_type, doc)
			)
		else:
			stream.write(
				#TBD: not sure ?!
				"%s = Symbol('%s', uri='%s', doc='%s')\n" %(collection_name, display_name, collection_type, doc)
			)
		return collection_name

	def _create_symbol(self, stream, member):
		name = str(member).split("#")[-1]
		comments = list(self.store.objects(member, RDFS.comment))
		doc = escape_chars(comments[0] if comments else "")
		labels = list(self.store.objects(member, RDFS.label))
		display_name = escape_chars(labels[0] if labels else name)
		root_type = set(map(str, self.store.objects(member, RDFS.subClassOf)))
		replace_items(root_type,
			{str(NIENS["InformationElement"]): "Interpretation", str(NIENS["DataObject"]): "Manifestation"})
		assert root_type
		#TODO: displayname, how are translation handled? on trig level or on python level?
		stream.write(
			"Symbol('%s', parent=%r, uri='%s', display_name='%s', doc='%s')\n" %(name, 
				root_type, member, display_name, doc)
		)

	def serialize(self, stream, base=None, encoding=None, **args):
		#~ # this is not working yet, and does not do anything
		#~ for resource in self.store.subjects(RDFS.subClassOf, RDFS.Resource):
			#~ #stream.write("""class %s(RDFSResource):\n\tpass\n\n""" %str(resource).split("#")[-1])
#~ 
			#~ for member in self.store.subjects(RDFS.domain, resource):
				#~ attributes = dict(self.store.predicate_objects(member))
				#~ if attributes.pop(RDF.type) == RDFS.RDFSNS["Property"]:
					#~ # ok, it is a property
					#~ name = attributes.pop(RDFS.label)
					#~ print name
					#~ print attributes
				#~ else:
					#~ raise ValueError
				#~ break

		for collection_types in (NIENS["InformationElement"], NIENS["DataObject"]):
			for collection_type in self.store.subjects(RDFS.subClassOf, collection_types):
				stream.write("\n#%s\n\n" %str(collection_type).split("#")[-1])
				members = sorted(self.store.subjects(RDFS.subClassOf, collection_type))
				if members:
					collection_name = self._create_symbol_collection(stream, collection_type)
					for member in members:
						self._create_symbol(stream, member)
				else:
					self._create_symbol(stream, collection_type)
