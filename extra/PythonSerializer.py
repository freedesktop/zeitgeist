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

def make_symbol_name(name):
	def _iter_chars(text):
		yield text[0]
		for s in text[1:]:
			if s.isupper():
				yield "_"
			yield s
	name = "".join(_iter_chars(name))
	return name.upper()
	
def escape_chars(text, strip=True):
	text = text.replace("'", "\\'")
	text = text.replace('"', '\\"')
	if strip:
		text = text.strip()
	return text

class PythonSerializer(RecursiveSerializer):

	def _create_symbol_collection(self, stream, collection_type):
		collection_name = escape_chars(str(collection_type).split("#")[-1])
		comments = list(self.store.objects(collection_type, RDFS.comment))
		doc = escape_chars(comments[0] if comments else "")
		labels = list(self.store.objects(collection_type, RDFS.label))
		display_name = escape_chars(labels[0] if labels else collection_name)
		root_type = list(self.store.objects(collection_type, RDFS.subClassOf))
		root_type = root_type[0] if root_type else None
		if root_type == NIENS["InformationElement"]:
			stream.write(
				#TBD: not sure ?!
				"%s = Symbol('%s', parent=Interpretation, uri='%s', doc='%s')\n" %(collection_name,
					display_name, collection_type, doc)
			)
		elif root_type == NIENS["DataObject"]:
			stream.write(
				#TBD: not sure ?!
				"%s = Symbol('%s', parent=Manifestation, uri='%s', doc='%s')\n" %(collection_name,
					display_name, collection_type, doc)
			)
		else:
			stream.write(
				#TBD: not sure ?!
				"%s = Symbol('%s', uri='%s', doc='%s')\n" %(collection_name, display_name, collection_type, doc)
			)
		return collection_name

	def _create_symbol(self, stream, collection_name, member):
		name = str(member).split("#")[-1]
		comments = list(self.store.objects(member, RDFS.comment))
		doc = escape_chars(comments[0] if comments else "")
		labels = list(self.store.objects(member, RDFS.label))
		display_name = escape_chars(labels[0] if labels else name)
		if collection_name is None:
			root_type = list(self.store.objects(member, RDFS.subClassOf))
			root_type = root_type[0] if root_type else None
			if root_type == NIENS["InformationElement"]:
				collection_name = "Interpretation"
			elif root_type == NIENS["DataObject"]:
				collection_name = "Manifestation"
		#TODO: displayname, how are translation handled? on trig level or on python level?
		stream.write(
			"Symbol('%s', parent=%s, uri='%s', display_name='%s', doc='%s')\n" %(make_symbol_name(name), 
				collection_name, member, display_name, doc)
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
						self._create_symbol(stream, collection_name, member)
				else:
					self._create_symbol(stream, None, collection_type)
