# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Markus Korn <thekorn@gmx.de>
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

try:
	#rdflib2
	from rdflib.syntax.serializers.RecursiveSerializer import RecursiveSerializer
	from rdflib.Namespace import Namespace
except ImportError:
	#rdflib3 (LP: #626224)
	from rdflib.plugins.serializers.turtle import RecursiveSerializer
	from rdflib.namespace import Namespace

from rdflib import RDF, RDFS

NIENS = Namespace("http://www.semanticdesktop.org/ontologies/2007/01/19/nie#")

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

def case_conv(name):
	"""
	Converts CamelCase to CAMEL_CASE
	"""
	result = ""
	for i in range(len(name) - 1) :
		if name[i].islower() and name[i+1].isupper():
			result += name[i].upper() + "_"
		else:
			result += name[i].upper()
	result += name[-1].upper()
	return result

class PythonSerializer(RecursiveSerializer):
		
	def _get_all_subclasses(self, *super_classes):
		for cls in super_classes:
			for subclass in self.store.subjects(RDFS.subClassOf, cls):
				yield subclass
				for x in self._get_all_subclasses(subclass):
					yield x
					
	def _create_symbol(self, stream, symbol, all_symbols):
		name = case_conv(str(symbol).split("#")[-1])
		comments = list(self.store.objects(symbol, RDFS.comment))
		doc = escape_chars(comments[0] if comments else "")
		labels = list(self.store.objects(symbol, RDFS.label))
		display_name = escape_chars(labels[0] if labels else name)
		root_type = set(self.store.objects(symbol, RDFS.subClassOf)).intersection(all_symbols)
		root_type = set(map(str, root_type))
		replace_items(root_type,
			{str(NIENS["InformationElement"]): "Interpretation", str(NIENS["DataObject"]): "Manifestation"})
		assert root_type
		#TODO: displayname, how are translation handled? on trig level or on python level?
		stream.write(
			"Symbol('%s', parent=%r, uri='%s', display_name='%s', doc='%s', auto_resolve=False)\n" %(name, 
				root_type, symbol, display_name, doc)
		)
		

	def serialize(self, stream, base=None, encoding=None, **args):
		symbol_classes = set(self._get_all_subclasses(NIENS["InformationElement"], NIENS["DataObject"]))
		
		for symbol in sorted(symbol_classes):
			self._create_symbol(
				stream, symbol, symbol_classes.union(set([NIENS["InformationElement"], NIENS["DataObject"]]))
			)
