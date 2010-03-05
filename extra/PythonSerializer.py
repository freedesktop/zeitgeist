from rdflib.syntax.serializers.RecursiveSerializer import RecursiveSerializer
from rdflib import RDF, RDFS
from rdflib.Namespace import Namespace

NIENS = Namespace("http://www.semanticdesktop.org/ontologies/2007/08/15/nie#")

import pprint

class PythonSerializer(RecursiveSerializer):

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
				
			stream.write("\n#Event interpretations\n\n")
				
			for interpretation in self.store.subjects(RDFS.subClassOf, NIENS["InformationElement"]):
				# interpretations
				collection_name = str(interpretation).split("#")[-1]
				comments = list(self.store.objects(interpretation, RDFS.comment))
				doc = comments[0] if comments else ""
				stream.write("%s = SymbolCollection('%s', '%s')\n" %(collection_name, collection_name, doc))
				#~ pprint.pprint(list(self.store.subjects(RDFS.subClassOf, interpretation)))
				for member in self.store.subjects(RDFS.subClassOf, interpretation):
					name = str(member).split("#")[-1]
					#TODO: displayname, doc
					stream.write("register_symbol(%s, '%s', '%s', '', '')\n" %(collection_name, name, member))
					
			stream.write("\n#Event manifestations\n\n")
					
			for manifestation in self.store.subjects(RDFS.subClassOf, NIENS["DataObject"]):
				# manifestation
				collection_name = str(manifestation).split("#")[-1]
				comments = list(self.store.objects(manifestation, RDFS.comment))
				doc = comments[0] if comments else ""
				stream.write("%s = SymbolCollection('%s', '%s')\n" %(collection_name, collection_name, doc))
				#~ pprint.pprint(list(self.store.subjects(RDFS.subClassOf, interpretation)))
				for member in self.store.subjects(RDFS.subClassOf, manifestation):
					name = str(member).split("#")[-1]
					#TODO: displayname, doc
					stream.write("register_symbol(%s, '%s', '%s', '', '')\n" %(collection_name, name, member))
