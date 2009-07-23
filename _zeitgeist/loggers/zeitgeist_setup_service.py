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

import dbus
import dbus.service
import gobject
import gconf
import glib
import dbus.mainloop.glib
from ConfigParser import SafeConfigParser
from xdg import BaseDirectory
from StringIO import StringIO

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

class DataProviderService(dbus.service.Object):
	
	def __init__(self, datasources, mainloop=None):
		bus_name = dbus.service.BusName("org.gnome.zeitgeist.datahub", dbus.SessionBus())
		dbus.service.Object.__init__(self, bus_name, "/org/gnome/zeitgeist/datahub")
		self._mainloop = mainloop
		self.__datasources = datasources
		
	@dbus.service.method("org.gnome.zeitgeist.DataHub",
						 out_signature="as")
	def GetDataProviders(self):
		return [i.config.get_internal_name() for i in self.__datasources if i.config.has_dbus_service()]
			
	def needs_setup(self):
		return not self.__configuration.isConfigured()


class SetupService(dbus.service.Object):
	
	def __init__(self, datasource, root_config, mainloop=None):
		bus_name = dbus.service.BusName("org.gnome.zeitgeist.datahub", dbus.SessionBus())
		dbus.service.Object.__init__(self,
			bus_name, "/org/gnome/zeitgeist/datahub/dataprovider/%s" %datasource)
		self._mainloop = mainloop
		self.__configuration = root_config
		if not isinstance(self.__configuration, _Configuration):
			raise TypeError
		self.__setup_is_running = None
		
	@dbus.service.method("org.gnome.zeitgeist.DataHub",
						 in_signature="iss")
	def SetConfiguration(self, token, option, value):
		if token != self.__setup_is_running:
			raise RuntimeError("wrong client")
		self.__configuration.set_attribute(option, value)
		
	@dbus.service.signal("org.gnome.zeitgeist.DataHub")
	def NeedsSetup(self):
		pass
		
	@dbus.service.method("org.gnome.zeitgeist.DataHub",
						 in_signature="i", out_signature="b")
	def RequestSetupRun(self, token):
		if self.__setup_is_running is None:
			self.__setup_is_running = token
			return True
		else:
			raise False
		
	@dbus.service.method("org.gnome.zeitgeist.DataHub",
						 out_signature="a(sb)")
	def GetOptions(self, token):
		if token != self.__setup_is_running:
			raise RuntimeError("wrong client")
		return self.__configuration.get_options()		
			
	def needs_setup(self):
		return not self.__configuration.isConfigured()
		

class _Configuration(gobject.GObject):
	
	@staticmethod
	def like_bool(value):
		if isinstance(value, bool):
			return value
		elif value.lower() in ("true", "1", "on"):
			return True
		elif value.lower() in ("false", "0", "off"):
			return False
		else:
			raise ValueError
	
	def __init__(self, internal_name, use_dbus=True, mainloop=None):
		gobject.GObject.__init__(self)
		self.__required = set()
		self.__items = dict()
		self.__internal_name = internal_name.replace(" ", "_").lower()
		if use_dbus:
			self.__dbus_service = SetupService(self.__internal_name, self, mainloop)
		else:
			self.__dbus_service = None
			
	def has_dbus_service(self):
		return self.__dbus_service is not None
		
	def get_internal_name(self):
		return self.__internal_name
		
	def add_option(self, name, to_type=str, to_string=str, default=None,
					required=True, secret=False):
		if name in self.__items:
			raise ValueError
		if required:
			self.__required.add(name)
		if to_type is None:
			to_type = lambda x: x
		self.__items[name] = (to_type(default), (to_type, to_string), secret)
		
	def __getattr__(self, name):
		if not self.isConfigured():
			raise RuntimeError
		return self.__items[name][0]
		
	def get_as_string(self, name):
		if not self.isConfigured():
			raise RuntimeError
		try:
			value, (_, to_string), _ = self.__items[name]
		except KeyError:
			raise AttributeError
		return str(to_string(value))
		
	def set_attribute(self, name, value, check_configured=True):
		if name not in self.__items:
			raise ValueError
		_, (to_type, to_string), secret = self.__items[name]
		self.__items[name] = (to_type(value), (to_type, to_string), secret)
		if name in self.__required:
			self.remove_requirement(name)
		if check_configured and self.isConfigured():
			glib.idle_add(self.emit, "configured")
			
	def remove_requirement(self, name):
		self.__required.remove(name)
		
	def add_requirement(self, name):
		if not name in self.__items:
			raise ValueError
		self.__required.add(name)
		
	def isConfigured(self):
		return not self.__required
		
	def read_config(self, filename, section):
		config = SafeConfigParser()
		config.readfp(open(filename))
		if config.has_section(section):
			for name, value in config.items(section):
				self.set_attribute(name, value)
				
	def dump_config(self, config=None):
		section = self.get_internal_name()
		if config is None:
			config = SafeConfigParser()
		try:
			config.add_section(section)
		except ConfigParser.DuplicateSectionError:
			pass
		for key, value in self.__items.iteritems():
			value, _, secret = value
			if not secret:
				config.set(section, key, str(value))
		f = StringIO()
		config.write(f)
		return f.getvalue()
		
	def get_requirements(self):
		return self.__required
		
	def get_options(self):
		return [(str(key), key in self.__required) for key in self.__items]
			
		
gobject.signal_new("configured", _Configuration,
				   gobject.SIGNAL_RUN_LAST,
				   gobject.TYPE_NONE,
				   tuple())
				
				
class DefaultConfiguration(_Configuration):
	
	CONFIGFILE = BaseDirectory.load_first_config("zeitgeist", "dataprovider.conf")
	DEFAULTS = [
		("enabled", _Configuration.like_bool, str, True, False),
	]
	
	def __init__(self, dataprovider):
		super(DefaultConfiguration, self).__init__(dataprovider)
		for default in self.DEFAULTS:
			self.add_option(*default)
		if self.CONFIGFILE:
			self.read_config(self.CONFIGFILE, self.get_internal_name())
				
	def save_config(self):
		if self.CONFIGFILE:
			config = SafeConfigParser()
			config.readfp(open(self.CONFIGFILE))
			self.dump_config(config)
			f = StringIO()
			config.write(f)
			with open(self.CONFIGFILE, "w") as configfile:
				config.write(configfile)

if __name__ == "__main__":
	
	def test(config):
		for option, required in config.get_options():
			print option, getattr(config, option)
	
	dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
	mainloop = gobject.MainLoop()
	
	config = _Configuration("test", True, mainloop)
	config.add_option("enabled", _Configuration.like_bool, default=False)
	config.connect("configured", test)
	mainloop.run()
