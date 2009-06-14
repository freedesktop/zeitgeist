def _(s) : return s

class Category:
	CACHE = {}
	
	def __init__ (self, uri, display_name=None, name=None):
		if self.__class__ == Category:
			raise ValueError("Category is an abstract class")
		self.uri = uri
		
		if name : self.name = name
		else: self.name = uri.split("#")[1]
		
		if display_name : self.display_name = display_name
		else: self.display_name = self.name
		
		self.__class__.CACHE[uri] = self

	@classmethod
	def get(klass, uri):
		if not uri in klass.CACHE:
			this = klass(uri)
			klass.CACHE[uri] = this
		return klass.CACHE[uri]

class Content(Category):
	def __init__ (self, url, display_name=None, name=None):
		Category.__init__(self, url, display_name, name)

class Source(Category):
	def __init__ (self, url, display_name=None, name=None):
		Category.__init__(self, url, display_name, name)

Content.TAG = Content("http://freedesktop.org/standards/xesam/1.0/core#Tag",
					  display_name=_("Tags"))
Content.BOOKMARK = Content("http://freedesktop.org/standards/xesam/1.0/core#Bookmark",
						   display_name=_("Bookmarks"))
"""Content.COMMENT = Symbol(Content, "http://gnome.org/zeitgeist/schema/1.0/core#Comment")
Content.DOCUMENT = Symbol(Content, "http://freedesktop.org/standards/xesam/1.0/core#Document")
Content.CREATE_EVENT = Symbol(Content, "http://gnome.org/zeitgeist/schema/1.0/core#CreateEvent")
Content.MODIFY_EVENT = Symbol(Content, "http://gnome.org/zeitgeist/schema/1.0/core#ModifyEvent")
Content.VISIT_EVENT = Symbol(Content, "http://gnome.org/zeitgeist/schema/1.0/core#VisitEvent")
Content.LINK_EVENT = Symbol(Content, "http://gnome.org/zeitgeist/schema/1.0/core#LinkEvent")
Content.SEND_EVENT = Symbol(Content, "http://gnome.org/zeitgeist/schema/1.0/core#SendEvent")
Content.RECEIVE_EVENT = Symbol(Content, "http://gnome.org/zeitgeist/schema/1.0/core#ReceiveEvent")
Content.WARN_EVENT = Symbol(Content, "http://gnome.org/zeitgeist/schema/1.0/core#WarnEvent")
Content.ERROR_EVENT = Symbol(Content, "http://gnome.org/zeitgeist/schema/1.0/core#ErrorEvent")
Source.WEB_HISTORY = Symbol(Source, "http://gnome.org/zeitgeist/schema/1.0/core#WebHistory")
Source.USER_ACTIVITY = Symbol(Source, "http://gnome.org/zeitgeist/schema/1.0/core#UserActivity")
Source.USER_NOTIFICATION = Symbol(Source, "http://gnome.org/zeitgeist/schema/1.0/core#UserNotification")
Source.APPLICATION = Symbol(Source, "http://gnome.org/zeitgeist/schema/1.0/core#Application")
"""
