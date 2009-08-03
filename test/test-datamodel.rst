Category - base class for Contnet and Source
********************************************

	>>> from zeitgeist.datamodel import Category
	>>> Category("http://zeitgeist.org/boo")
	Traceback (most recent call last):
	  ...
	ValueError: Category is an abstract class

Create a new Category
*********************

	>>> class Content(Category):
	... 	pass
	>>> print Content
	<Symbol 'Content'>
	
	>>> Content.TAG
	Traceback (most recent call last):
	  ...
	AttributeError: Object 'Content' has no attribute 'TAG'
	
	>>> Content.register(
	... 	"TAG",
	... 	u"http://freedesktop.org/standards/xesam/1.0/core#Tag",
	... 	display_name="Tags",
	... 	doc="User provided tags. The same tag may refer multiple items"
	... )
	>>> Content.register(
	... 	"BOOKMARK",
	... 	u"http://freedesktop.org/standards/xesam/1.0/core#Bookmark",
	... 	display_name="Bookmarks",
	... 	doc="A user defined bookmark. The same bookmark may only refer exectly one item"
	... )
	>>> Content.TAG
	<Content u'http://freedesktop.org/standards/xesam/1.0/core#Tag'>
	>>> print Content.TAG.uri
	http://freedesktop.org/standards/xesam/1.0/core#Tag
	>>> print Content.TAG.name
	Tag
	>>> print Content.TAG.__doc__
	User provided tags. The same tag may refer multiple items
	>>> print Content.TAG.display_name
	Tags
	
	>>> tag = Content.get(Content.TAG.uri)
	>>> tag is Content.TAG
	True
	
	>>> tag.id
	Traceback (most recent call last):
	  ...
	RuntimeError: Cannot get 'id', object is not bound to a database
	
	>>> from zeitgeist.datamodel import DictCache
	>>> class DatabaseCls(object):
	... 	__metaclass__ = DictCache
	...
	... 	@classmethod
	... 	def lookup_or_create(cls, uri):
	... 		return cls._CACHE.setdefault(uri, cls(uri))
	...
	... 	def __init__(self, uri):
	... 		self.value = uri
	... 		self.id = len(self.__class__._CACHE) + 1
	>>> Content.bind_database(DatabaseCls)
	>>> Content.TAG.id
	1
	>>> Content.BOOKMARK.id
	2
	
	>>> boo = Content.get("boo")
	>>> boo.id
	3
	>>> boo is Content.get("boo")
	True
	>>> Content.get("boo").id
	3
	>>> Content._clear_cache()
	>>> Content.needs_lookup(Content.BOOKMARK.uri)
	True
	>>> Content.BOOKMARK.id
	1
	>>> Content.needs_lookup(Content.BOOKMARK.uri)
	False
	>>> Content.needs_lookup(Content.TAG.uri)
	True
	
	>>> Content.register(
	... 	"TAG",
	... 	u"http://freedesktop.org/standards/xesam/1.0/core#Tag",
	... 	display_name="Tags",
	... 	doc="User provided tags. The same tag may refer multiple items"
	... )
	Traceback (most recent call last):
	  ...
	ValueError: Can't register Content object for u'http://freedesktop.org/standards/xesam/1.0/core#Tag', Content has already an attribute called 'TAG'


Use default Content and Source symbols
**************************************
	
	>>> from zeitgeist.datamodel import Content, Source
	>>> print sorted(Source._ATTRIBUTES.keys())
	['FILE', 'SYSTEM_RESOURCE', 'USER_ACTIVITY', 'USER_NOTIFICATION', 'WEB_HISTORY']
	>>> print sorted(Content._ATTRIBUTES.keys()) #doctest: +NORMALIZE_WHITESPACE
	['APPLICATION', 'BOOKMARK', 'BROADCAST_MESSAGE', 'COMMENT', 'CREATE_EVENT',
	 'DOCUMENT', 'EMAIL', 'ERROR_EVENT', 'IMAGE', 'IM_MESSAGE', 'MODIFY_EVENT',
	 'MUSIC', 'RECEIVE_EVENT', 'RSS_MESSAGE', 'SEND_EVENT', 'TAG', 'VIDEO',
	 'VISIT_EVENT', 'WARN_EVENT']
	
