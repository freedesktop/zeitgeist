import re
import sys

RE_PREFIX = re.compile(r"^@prefix\s*(?P<name>\w+)\:\s*<(?P<url>[^>]+)>\s*\.\s*$")
RE_START_ONTOLOGY = re.compile(r"^(?P<name>\w+)\:\s*\{\s*(?:\#.*)?$")
RE_START_ELEMENT = re.compile(r"^(?:(?P<namespace>\w+)\:(?P<name>\w+))?(?:\s*a\s+(?P<base_namespace>\w+)\:(?P<base_name>\w+)\s*(?P<end>(\.|\;)))?$")
RE_ELEMENT_ATTRIBUTE = re.compile(r"^(?P<namespace>\w+)\:(?P<name>\w+)\s+(?P<content>.+)\s*(?P<end>(\.|\;))$")

class ParserError(RuntimeError):
    pass
    
class Ontology(dict):
    
    def __init__(self, name):
        self.__name = name
        
    @property
    def name(self):
        return self.__name
        
    def __hash__(self):
        return hash(self.name)
        
    def add_element(self, element):
        self[element.name] = element
        
class Element(object):
    
    def __init__(self, namespace, name):
        self.__namespace = namespace
        self.__name = name
        
    @property
    def name(self):
        return (self.__namespace, self.__name)
        
class ExtendedElement(Element):
    
    @staticmethod
    def dispatch(base_namespace, base_name):
        return False
    
    @classmethod
    def create(cls, **kwargs):
        namespace = kwargs.pop("namespace")
        name = kwargs.pop("name")
        for ncls in cls.__subclasses__():
            if ncls.dispatch(kwargs.get("base_namespace", None), kwargs.get("base_name", None)):
                return ncls(namespace, name, **kwargs)
        return cls(namespace, name, **kwargs)
    
    def __init__(self, namespace, name, **kwargs):
        super(ExtendedElement, self).__init__(namespace, name)
        if "end" in kwargs:
            del kwargs["end"]
        self.__attributes = kwargs
        
    def __getattr__(self, name):
        try:
            return self.__attributes[name]
        except KeyError:
            raise AttributeError
            
    def add_attribute(self, namespace, name, content):
        self.__attributes[name] = content
        
class ClassElement(ExtendedElement):
    
    @staticmethod
    def dispatch(base_namespace, base_name):
        return base_namespace == "rdfs" and base_name == "Class"
    
    def __init__(self, namespace, name, **kwargs):
        self.__base = (kwargs.pop("base_namespace"), kwargs.pop("base_name"))
        super(ClassElement, self).__init__(namespace, name, **kwargs)
            
class PropertyElement(ExtendedElement):
    
    @staticmethod
    def dispatch(base_namespace, base_name):
        return base_namespace == "rdf" and base_name == "Property"
    
    def __init__(self, namespace, name, **kwargs):
        self.__domain = kwargs.pop("domain", None)
        super(PropertyElement, self).__init__(namespace, name, **kwargs)        

class OntologyCollection(dict):
    
    @classmethod
    def parse(cls, filename):
        prefix_collection = dict()
        ontologies = set()
        current_ontology = None
        current_element = None
        for n, line in enumerate(open(filename)):
            stripped_line = line.strip()
            if not stripped_line:
                # empty line
                continue
            if stripped_line.startswith("#"):
                #we don't care about comments
                continue
            prefix = RE_PREFIX.match(line)
            if prefix:
                prefix = prefix.groupdict()
                prefix_collection[prefix["name"]] = prefix["url"]
            else:
                if current_ontology is None:
                    if stripped_line.startswith("<") and "metadata" in line.lower():
                        # metadata is not yet supported
                        break
                    name = RE_START_ONTOLOGY.match(line)
                    if not name:
                        raise ParserError("cannot parse '%s', line %i" %(filename, n+1))
                    current_ontology = Ontology(name.groupdict()["name"])
                else:
                    if stripped_line == "}":
                        if current_element is not None:
                            raise ParserError("did not find end of element definition, line %i" %(n+1))
                        ontologies.add(current_ontology)
                        current_ontology = None
                        assert current_element is None
                        continue
                    if not isinstance(current_element, Element):
                        element = RE_START_ELEMENT.match(stripped_line)
                        if not element:
                            split_comment = "#".join(stripped_line.split("#")[:-1])
                            element = RE_START_ELEMENT.match(split_comment.strip())
                            if not element:
                                raise ParserError("error in line %i" %(n+1))
                        if current_element is None:
                            current_element = element.groupdict()
                        else:
                            element = element.groupdict()
                            for key, value in element.iteritems():
                                if current_element.get(key, None) is None and value is not None:
                                    current_element[key] = value
                        if None in current_element.values():
                            continue
                        if current_element["end"] == ".":
                            current_ontology.add_element(ExtendedElement.create(**current_element))
                            current_element = None
                        else:
                            current_element = ExtendedElement.create(**current_element)
                    else:
                        attribute = RE_ELEMENT_ATTRIBUTE.match(stripped_line)
                        if not attribute:
                            split_comment = "#".join(stripped_line.split("#")[:-1])
                            attribute = RE_ELEMENT_ATTRIBUTE.match(split_comment.strip())
                            if not attribute:
                                raise ParserError("error parsing line %i" %(n+1))
                        attribute = attribute.groupdict()
                        current_element.add_attribute(
                            attribute["namespace"],
                            attribute["name"],
                            attribute["content"]
                        )
                        if attribute["end"] == ".":
                            current_ontology.add_element(current_element)
                            current_element = None
                        
        if current_element is not None or current_ontology is not None:
            raise ParserError("unexpected end of file")
        return cls(ontologies, prefix_collection)
                
            
        
    def __init__(self, ontologies=None, prefix=None):
        if ontologies:
            super(OntologyCollection, self).__init__(
                (o.name, o) for o in ontologies)
        else:
            super(OntologyCollection, self).__init__()
        self.__prefix = prefix or dict()
        
    @property
    def prefix(self):
        return self.__prefix
        

def main():
    assert len(sys.argv) == 2
    ontology_filename = sys.argv[1]
    ontologies = OntologyCollection.parse(ontology_filename)
    import pprint
    pprint.pprint(ontologies)
    

if __name__ == "__main__":
    sys.exit(main())

