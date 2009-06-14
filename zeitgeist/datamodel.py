class Category:
	CACHE = {}
	
	def __init__ (self, url, display_name=None, name=None):
		if self.__class__ == Category:
			raise ValueError("Category is an abstract class")
		self.url = url
		
		if name : self.name = name
		else: self.name = url.split("#")[1]
		
		if display_name : self.display_name = display_name
		else: self.display_name = self.name
		
		self.__class__.CACHE[url] = self

	@classmethod
	def get(klass, url):
		if not url in klass.CACHE:
			this = klass(url)
			klass.CACHE[url] = this
		return klass.CACHE[url]

class Content(Category):
	def __init__ (self, url, display_name=None, name=None):
		super(Content, self).__init__(url, displayName, name)

class Source(Category):
	def __init__ (self, url, display_name=None, name=None):
		super(Source, self).__init__(url, displayName, name)
