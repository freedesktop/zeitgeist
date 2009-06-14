# FIXME: gettext support
def _(s) : return s

class Category:
	CACHE = {}
	
	def __init__ (self, uri, display_name=None, name=None, doc=None):
		if self.__class__ == Category:
			raise ValueError("Category is an abstract class")
		self.uri = uri
		
		if name : self.name = name
		else: self.name = uri.split("#")[1]
		
		if display_name : self.display_name = display_name
		else: self.display_name = self.name
		
		self.doc = doc if doc else ""
		
		self.__class__.CACHE[uri] = self

	@classmethod
	def get(klass, uri):
		if not uri in klass.CACHE:
			this = klass(uri)
			klass.CACHE[uri] = this
		return klass.CACHE[uri]

class Content(Category):
	def __init__ (self, url, display_name=None, name=None, doc=None):
		Category.__init__(self, url, display_name, name, doc)

class Source(Category):
	def __init__ (self, url, display_name=None, name=None, doc=None):
		Category.__init__(self, url, display_name, name, doc)

#
# Content categories
#
Content.TAG = Content("http://freedesktop.org/standards/xesam/1.0/core#Tag",
					  display_name=_("Tags"),
					  doc="User provided tags. The same tag may refer multiple items"
)
Content.BOOKMARK = Content("http://freedesktop.org/standards/xesam/1.0/core#Bookmark",
						   display_name=_("Bookmarks"),
						   doc="A user defined bookmark. The same bookmark may only refer exectly one item"
)
Content.COMMENT = Content("http://gnome.org/zeitgeist/schema/1.0/core#Comment",
						   display_name=_("Comments"),
						   doc="User provided comment"
)
Content.DOCUMENT = Content("http://freedesktop.org/standards/xesam/1.0/core#Document",
						   display_name=_("Documents"),
						   doc="A document, presentation, spreadsheet, or other content centric item"
)
Content.CREATE_EVENT = Content("http://gnome.org/zeitgeist/schema/1.0/core#CreateEvent",
						   display_name=_("Created"),
						   doc="Event type triggered when an item is created"
)
Content.MODIFY_EVENT = Content("http://gnome.org/zeitgeist/schema/1.0/core#ModifyEvent",
						   display_name=_("Modified"),
						   doc="Event type triggered when an item is modified"
)
Content.VISIT_EVENT = Content("http://gnome.org/zeitgeist/schema/1.0/core#VisitEvent",
						   display_name=_("Visited"),
						   doc="Event type triggered when an item is visited or opened"
)
Content.SEND_EVENT = Content("http://gnome.org/zeitgeist/schema/1.0/core#SendEvent",
						   display_name=_("Send"),
						   doc="Event type triggered when the user sends/emails an item or message to a remote host"
)
Content.RECEIVE_EVENT = Content("http://gnome.org/zeitgeist/schema/1.0/core#ReceiveEvent",
						   display_name=_("Received"),
						   doc="Event type triggered when the user has received an item from a remote host"
)
Content.WARN_EVENT = Content("http://gnome.org/zeitgeist/schema/1.0/core#WarnEvent",
						   display_name=_("Warnings"),
						   doc="Event type triggered when the user is warned about something"
)
Content.ERROR_EVENT = Content("http://gnome.org/zeitgeist/schema/1.0/core#ErrorEvent",
						   display_name=_("Errors"),
						   doc="Event type triggered when the user has encountered an error"
)
Content.APPLICATION = Source("http://gnome.org/zeitgeist/schema/1.0/core#Application",
						   display_name=_("Applications"),
						   doc="An item that is a launchable application. The item's URI must point to the relevant .desktop file"
)

#
# Source categories
#
Source.WEB_HISTORY = Source("http://gnome.org/zeitgeist/schema/1.0/core#WebHistory",
						   display_name=_("Web History"),
						   doc="An item that has been extracted from the user's browsing history"
)
Source.USER_ACTIVITY = Source("http://gnome.org/zeitgeist/schema/1.0/core#UserActivity",
						   display_name=_("Activities"),
						   doc="An item that has been created solely on the basis of user actions and is not otherwise stored in some physical location"
)
Source.USER_NOTIFICATION = Source("http://gnome.org/zeitgeist/schema/1.0/core#UserNotification",
						   display_name=_("Notifications"),
						   doc="An item that has been send as a notification to the user"
)
Source.FILE = Source("http://freedesktop.org/standards/xesam/1.0/core#File",
						   display_name=_("Files"),
						   doc="An item stored on the local filesystem"
)
Source.SYSTEM_RESOURCE = Source("http://freedesktop.org/standards/xesam/1.0/core#File",
						   display_name=_("System Resources"),
						   doc="An item available through the host operating system, such as an installed application or manual page"
)


