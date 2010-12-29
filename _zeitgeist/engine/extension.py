# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Markus Korn <thekorn@gmx.de>
# Copyright © 2010 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
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

import os
import logging
import weakref # avoid circular references as they confuse garbage collection

log = logging.getLogger("zeitgeist.extension")

import zeitgeist
from _zeitgeist.engine import constants

def safe_issubclass(obj, cls):
	try:
		return issubclass(obj, cls)
	except TypeError:
		return False
		
def get_extension_name(extension):
	""" We are using the name of the Extension-class as extension's unique
	name, later we might want to prepend modul or package names.
	"""
	if safe_issubclass(extension, Extension):
		return extension.__name__
	elif isinstance(extension, Extension):
		return extension.__class__.__name__
	else:
		raise TypeError(
			"Can't identify %r, an extension has to be a subclass or "
			"instance of extension.Extension" %extension)

class Extension(object):
	""" Base class for all extensions
	
	Every extension has to define a list of accessible methods as
	'PUBLIC_METHODS'. The constructor of an Extension object takes the
	engine object it extends as the only argument.
	
	In addition each extension has a set of hooks to control how events are
	inserted and retrieved from the log. These hooks can either block the
	event completely, modify it, or add additional metadata to it.
	"""
	PUBLIC_METHODS = []
	
	def __init__(self, engine):
		self.engine = weakref.proxy(engine)
	
	def unload(self):
		"""
		This method gets called before Zeitgeist stops.
		
		Execution of this method isn't guaranteed, and you shouldn't do
		anything slow in there.
		"""
		pass
	
	def pre_insert_event(self, event, sender):
		"""
		Hook applied to all events before they are inserted into the
		log. The returned event is progressively passed through all
		extensions before the final result is inserted.
		
		To block an event completely simply return :const:`None`.
		The event may also be modified or completely substituted for
		another event.
		
		The default implementation of this method simply returns the
		event as is.
		
		:param event: An :class:`Event <zeitgeist.datamodel.Event>`
			instance
		:param sender: The D-Bus bus name of the client
		:returns: The filtered event instance to insert into the log
		"""
		return event
	
	def post_insert_event(self, event, sender):
		"""
		Hook applied to all events after they are inserted into the
		log.
		
		:param event: An :class:`Event <zeitgeist.datamodel.Event>`
			instance
		:param sender: The D-Bus bus name of the client
		:returns: Nothing
		"""
		pass
	
	def get_event(self, event, sender):
		"""
		Hook applied to all events before they are returned to a client.
		The event returned from this method is progressively passed
		through all extensions before they final result is returned to
		the client.
		
		To prevent an event from ever leaving the server process simply
		return :const:`None`. The event may also be changed in place
		or fully substituted for another event.
		
		The default implementation of this method simply returns the
		event as is.
		
		:param event: An :class:`Event <zeitgeist.datamodel.Event>`
			instance or :const:`None`
		:param sender: The D-Bus bus name of the client
		:returns: The filtered event instance as the client
			should see it
		"""
		return event
	
	def post_delete_events(self, ids, sender):
		"""
		Hook applied after events have been deleted from the log.
		
		:param ids: A list of event ids for the events that has been deleted
		:param sender: The unique DBus name for the client triggering the delete
		:returns: Nothing
		"""
		pass
	
	def pre_delete_events(self, ids, sender):
		"""
		Hook applied before events are deleted from the log.
		
		:param ids: A list of event ids for the events requested to be deleted
		:param sender: The unique DBus name for the client triggering the delete
		:returns: The filtered list of event ids which should be deleted
		"""
		return ids


def get_extensions():
	"""looks at the `ZEITGEIST_DEFAULT_EXTENSIONS` environment variable
	to find the extensions which should be loaded on daemon startup, if
	this variable is not set the "extensiondir" variable of the configuration
	will be scanned for .py files with classes extending Extension
	If this variable is set to an empty string no extensions are loaded by
	default.
	To load an extra set of extensions define the `ZEITGEIST_EXTRA_EXTENSIONS`
	variable.
	The format of these variables should just be a no-space comma
	separated list of module.class names"""
	default_extensions = os.environ.get("ZEITGEIST_DEFAULT_EXTENSIONS")
	if default_extensions is not None:
		if default_extensions != "": 
			extensions = map(_load_class, default_extensions.split(","))
		else:
			log.debug("All default extensions disabled")
			extensions = []
	else:
		extensions = _scan_extensions()
	extra_extensions = os.environ.get("ZEITGEIST_EXTRA_EXTENSIONS")
	if extra_extensions:
		extensions += map(_load_class, extra_extensions.split(","))
	else:
		log.debug("No extra extensions")
	extensions = filter(None, extensions)
	log.debug("Found extensions: %r" %extensions)
	return extensions

def _scan_extensions():
	"""Look in zeitgeist._config.extensiondir for .py files and return
	a list of classes with all the classes that extends the Extension class"""
	config = zeitgeist._config		
	extensions = []
	
	# Find system extensions
	log.debug("Searching for system extensions in: %s" % config.extensiondir)
	sys_modules = filter(lambda m: m.endswith(".py"), os.listdir(config.extensiondir))
	sys_modules = map(lambda m: "_zeitgeist.engine.extensions." + m.rpartition(".")[0], sys_modules)
	
	# Find user extensions
	log.debug("Searching for user extensions in: %s" % constants.USER_EXTENSION_PATH)
	user_modules = []
	try:
		user_modules = filter(lambda m: m.endswith(".py"), os.listdir(os.path.expanduser(constants.USER_EXTENSION_PATH)))
		user_modules = map(lambda m: m.rpartition(".")[0], user_modules)
	except OSError:
		pass # USER_EXTENSION_PATH doesn't exist
	
	# If we have module conflicts let the user extensions win,
	# and remove the system provided extension from our list
	user_module_names = map(lambda m: os.path.basename(m), user_modules)
	for mod in list(sys_modules):
		mod_name = mod.rpartition(".")[2]
		if mod_name in user_module_names:
			log.info ("Extension %s in %s overriding system extension" %
			          (mod_name, constants.USER_EXTENSION_PATH))
			sys_modules.remove(mod)
	
	# Now load the modules already!
	for mod in user_modules + sys_modules:
		path, dot, name = mod.rpartition(".")
		if path:
			ext = __import__(mod, globals(), locals(), [name])
		else:
			ext = __import__(name)
				
		for cls in dir(ext):
			cls = getattr(ext, cls)
			if safe_issubclass(cls, Extension) and not cls is Extension:
				extensions.append(cls)
	return extensions

def _load_class(path):
	"""
	Load and return a class from a fully qualified string.
	Fx. "_zeitgeist.engine.extensions.myext.MyClass"
	"""
	module, dot, cls_name = path.rpartition(".")
	parts = module.split(".")
	module = __import__(module)
	for part in parts[1:]:
		try:
			module = getattr(module, part)
		except AttributeError:
			raise ImportError(
			  "No such submodule '%s' when loading %s" % (part, path))
	
	try:
		cls = getattr(module, cls_name)
	except AttributeError:
		raise ImportError("No such class '%s' in module %s" % (cls_name, path))
	
	return cls

class ExtensionsCollection(object):
	""" Collection to manage all extensions """
	
	def __init__(self, engine, defaults=None):
		self.__extensions = dict()
		self.__engine = engine
		self.__methods = dict()
		if defaults is not None:
			for extension in defaults:
				self.load(extension)
				
	def __repr__(self):
		return "%s(%r)" %(self.__class__.__name__, sorted(self.__methods.keys()))
			
	def load(self, extension):
		if not issubclass(extension, Extension):
			raise TypeError("Unable to load %r, all extensions must be "
				"subclasses of %r" % (extension, Extension))
		ext_name = get_extension_name(extension)
		log.debug("Loading extension '%s'" %ext_name)
		try:
			obj = extension(self.__engine)
		except Exception:
			log.exception("Failed loading the '%s' extension" %ext_name)
			return False

		for method in obj.PUBLIC_METHODS:
			self._register_method(method, getattr(obj, method))
		self.__extensions[ext_name] = obj
		
	def unload(self, extension=None):
		"""
		Unload a specified extension or unload all extensions if
		no extension is given
		"""
		if not self.__extensions:
			return
		if extension is None:
			log.debug("Unloading all extensions")
			
			# We need to clone the key list to avoid concurrent
			# modification of the extension dict
			for ext in list(self):
				self.unload(ext)
		else:
			ext_name = get_extension_name(extension)
			log.debug("Unloading extension '%s'" %ext_name)
			obj = self.__extensions[ext_name]
			for method in obj.PUBLIC_METHODS:
				del self.methods[method]
			del self.__extensions[ext_name]
	
	def apply_get_hooks(self, event, sender):
		# Apply extension filters if we have an event
		if event is None:
			return None
		
		# FIXME: We need a stable iteration order
		for ext in self.__extensions.itervalues():
			event = ext.get_event(event, sender)
			if event is None:
				# The event has been blocked by
				# the extension pretend it's
				# not there
				continue
		return event
	
	def apply_post_delete(self, ids, sender):
		# Apply extension filters if we have an event
	
		# FIXME: We need a stable iteration order
		for ext in self.__extensions.itervalues():
			event = ext.post_delete_events(ids, sender)
			
	def apply_pre_delete(self, ids, sender):
		# Apply extension filters if we have an event
	
		# FIXME: We need a stable iteration order
		for ext in self.__extensions.itervalues():
			ids = ext.pre_delete_events(ids, sender)
			
		return ids
	
	def apply_pre_insert(self, event, sender):
		# FIXME: We need a stable iteration order
		for ext in self.__extensions.itervalues():
			event = ext.pre_insert_event(event, sender)
			if event is None:
				# The event has been blocked by the extension
				return None
		return event
	
	def apply_post_insert(self, event, sender):
		# FIXME: We need a stable iteration order
		for ext in self.__extensions.itervalues():
			ext.post_insert_event(event, sender)
	
	def __len__(self):
		return len(self.__extensions)
	
	@property
	def methods(self):
		return self.__methods
		
	def _register_method(self, name, method):
		if name in self.methods:
			raise ValueError("There is already an extension which provides "
				"a method called %r" % name)
		self.methods[name] = method
		
	def __getattr__(self, name):
		try:
			return self.methods[name]
		except KeyError:
			raise AttributeError("%s instance has no attribute %r" % (
				self.__class__.__name__, name))
	
	def __iter__(self):
		return self.__extensions.itervalues()
		
	def iter_names(self):
		return self.__extensions.iterkeys()
