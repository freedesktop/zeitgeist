
class Extension(object):
	__public_methods__ = None
	
	def __init__(self, engine):
		self.engine = engine
	
	
class ExtensionsCollection(object):
	
	def __init__(self, engine, defaults=None):
		self.__extensions = dict()
		self.__engine = engine
		self.__methods = dict()
		if defaults is not None:
			for extension in defaults:
				self.load(extension)
				
	def __repr__(self):
		return "%s(%r)" %(self.__class__.__name__, self.__methods.keys())
			
	def load(self, extension):
		if not issubclass(extension, Extension):
			raise TypeError
		if getattr(extension, "__public_methods__", None) is None:
			raise ValueError
		obj = extension(self.__engine)
		for method in obj.__public_methods__:
			self.__engine._register_method(method, getattr(obj, method))
		self.__extensions[obj.__class__.__name__] = obj
		
	def unload(self, extension):
		del self.__extensions[extension.__name__]
		
	def __len__(self):
		return len(self.__extensions)
		
	@property
	def methods(self):
		return self.__methods
	
