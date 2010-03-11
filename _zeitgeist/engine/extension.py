# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Markus Korn <thekorn@gmx.de>
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

import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("zeitgeist.extension")

def safe_issubclass(obj, cls):
	try:
		return issubclass(obj, cls)
	except TypeError:
		return False

class Extension(object):
	""" Base class for all extensions
	
	Every extension has to define a list of accessible methods as
	'PUBLIC_METHODS'. The constructor of an Extension object takes the
	engine object it extends as the only argument.
	
	In addition each extension has a set of hooks to control how events are
	inserted and retrieved from the log. These hooks can either block the
	event completely, modify it, or add additional metadata to it.
	"""
	PUBLIC_METHODS = None
	
	def __init__(self, engine):
		self.engine = engine
	
	def insert_event_hook(self, event, sender):
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
	
	def get_event_hook(self, event, sender):
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
			instance
		:param sender: The D-Bus bus name of the client
		:returns: The filtered event instance as the client
			should see it
		"""
		return event

def load_class(path):
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
		log.debug("Loading extension '%s'" % extension.__name__)
		if not issubclass(extension, Extension):
			raise TypeError("Unable to load %r, all extensions must be "
				"subclasses of %r" % (extension, Extension))
		if getattr(extension, "PUBLIC_METHODS", None) is None:
			raise ValueError("Unable to load %r, this extension has not "
				"defined any methods" % extension)
		obj = extension(self.__engine)
		for method in obj.PUBLIC_METHODS:
			self._register_method(method, getattr(obj, method))
		self.__extensions[obj.__class__.__name__] = obj
		
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
			for ext_name in list(self.__extensions.iterkeys()):
				self.unload(self.__extensions[ext_name])
		else:
			log.debug("Unloading extension '%s'" \
					  % extension.__class__.__name__)
			if safe_issubclass(extension, Extension):
				ext_name = extension.__name__
			elif isinstance(extension, Extension):
				ext_name = extension.__class__.__name__
			else:
				raise TypeError
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
			event = ext.get_event_hook(event, sender)
			if event is None:
				# The event has been blocked by
				# the extension pretend it's
				# not there
				continue
		return event
	
	def apply_insert_hooks(self, event, sender):
		# FIXME: We need a stable iteration order
		for ext in self.__extensions.itervalues():
			event = ext.insert_event_hook(event, sender)
			if event is None:
				# The event has been blocked by the extension
				return None
		return event
	
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
