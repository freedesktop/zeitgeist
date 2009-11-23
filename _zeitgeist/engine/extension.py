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

class Extension(object):
	""" Base class for all extensions
	
	Every extension has to define a list of accessible methods as
	'PUBLIC_METHODS'. The constructor of an Extension object takes the
	engine object it extends as the only argument
	"""
	PUBLIC_METHODS = None
	
	def __init__(self, engine):
		self.engine = engine
	
	
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
			raise TypeError(
				"Unable to load %r, all extensions have to be subclasses of %r" %(extension, Extension)
			)
		if getattr(extension, "PUBLIC_METHODS", None) is None:
			raise ValueError("Unable to load %r, this extension has not defined any methods" %extension)
		obj = extension(self.__engine)
		for method in obj.PUBLIC_METHODS:
			self._register_method(method, getattr(obj, method))
		self.__extensions[obj.__class__.__name__] = obj
		
	def unload(self, extension):
		obj = self.__extensions[extension.__name__]
		for method in obj.PUBLIC_METHODS:
			del self.methods[method]
		del self.__extensions[extension.__name__]
		
	def __len__(self):
		return len(self.__extensions)
		
	@property
	def methods(self):
		return self.__methods
		
	def _register_method(self, name, method):
		if name in self.methods:
			raise ValueError("There is already an extension which provides a method called %r" %name)
		self.methods[name] = method
		
	def __getattr__(self, name):
		try:
			return self.methods[name]
		except KeyError:
			raise AttributeError("%s instance has no attribute %r" %(self.__class__.__name__, name))
	
