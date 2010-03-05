from rdflib.syntax.serializers.RecursiveSerializer import RecursiveSerializer
from rdflib import RDF, RDFS
from rdflib.Namespace import Namespace

NIENS = Namespace("http://www.semanticdesktop.org/ontologies/2007/08/15/nie#")

import pprint

class PythonSerializer(RecursiveSerializer):
	
	def _create_symbol_collection(self, stream, collection_type):
		collection_name = str(collection_type).split("#")[-1]
		comments = list(self.store.objects(collection_type, RDFS.comment))
		doc = comments[0] if comments else ""
		stream.write("%s = SymbolCollection('%s', '%s')\n" %(collection_name, collection_name, doc))
		return collection_name
		
	def _create_symbol(self, stream, collection_name, member):
		name = str(member).split("#")[-1]
		comments = list(self.store.objects(member, RDFS.comment))
		doc = comments[0] if comments else ""
		labels = list(self.store.objects(member, RDFS.label))
		display_name = labels[0] if labels else name
		#TODO: displayname, how are translation handled? on trig level or on python level?
		stream.write(("register_symbol(collection=%s, name='%s',\n"
					  "\turi='%s',\n"
					  "\tdisplayname=_('%s'),\n"
					  "\tdocstring='%s')\n") %(collection_name, name, member, display_name, doc))

	def serialize(self, stream, base=None, encoding=None, **args):
		for classURI in self.topClasses:
			for resource in self.store.subjects(RDFS.subClassOf, RDFS.Resource):
				stream.write("""Class %s(RDFSResource)\n\tpass\n\n""" %str(resource).split("#")[-1])
				
				for member in self.store.subjects(RDFS.domain, resource):
					attributes = dict(self.store.predicate_objects(member))
					if attributes.pop(RDF.type) == RDFS.RDFSNS["Property"]:
						# ok, it is a property
						name = attributes.pop(RDFS.label)
						#~ print name
						#~ print attributes
					else:
						raise ValueError
					break
					
			for collection_types in (NIENS["InformationElement"], NIENS["DataObject"]):
				for collection_type in self.store.subjects(RDFS.subClassOf, collection_types):
					stream.write("\n#%s\n\n" %str(collection_type).split("#")[-1])
					collection_name = self._create_symbol_collection(stream, collection_type)
					for member in sorted(self.store.subjects(RDFS.subClassOf, collection_type)):
						self._create_symbol(stream, collection_name, member)
