# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Markus Korn <thekorn@gmx.de>
# Copyright © 2009-2010 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
# Copyright © 2009 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
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
from xdg import BaseDirectory

from zeitgeist.client import ZeitgeistDBusInterface

__all__ = [
	"log",
	"get_engine",
	"constants"
]

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("zeitgeist.engine")

_engine = None
def get_engine():
	""" Get the running engine instance or create a new one. """
	global _engine
	if _engine is None or _engine.is_closed():
		import main # _zeitgeist.engine.main
		_engine = main.ZeitgeistEngine()
	return _engine
	
def _get_extensions():
	"""looks at the `ZEITGEIST_DEFAULT_EXTENSIONS` environment variable
	to find the extensions which should be loaded on daemon startup, if
	this variable is not set the `Blacklist` and the `DataSourceRegistry`
	extension will be loaded. If this variable is set to an empty string
	no extensions are loaded by default.
	To load an extra set of extensions define the `ZEITGEIST_EXTRA_EXTENSIONS`
	variable.
	The format of these variables should just be a no-space comma
	separated list of module.class names"""
	default_extensions = os.environ.get("ZEITGEIST_DEFAULT_EXTENSIONS", None)
	if default_extensions is not None:
		extensions = default_extensions.split(",")
	else:
		extensions = [
		"_zeitgeist.engine.extensions.blacklist.Blacklist",
		"_zeitgeist.engine.extensions.datasource_registry.DataSourceRegistry",
		]
	extra_extensions = os.environ.get("ZEITGEIST_EXTRA_EXTENSIONS", None)
	if extra_extensions is not None:
		extensions += extra_extensions.split(",")
	extensions = filter(None, extensions)
	log.debug("daemon is configured to run with these extensions: %r" %extensions)
	return extensions

class _Constants:
	# Directories
	DATA_PATH = os.environ.get("ZEITGEIST_DATA_PATH",
		BaseDirectory.save_data_path("zeitgeist"))
	DATABASE_FILE = os.environ.get("ZEITGEIST_DATABASE_PATH",
		os.path.join(DATA_PATH, "activity.sqlite"))
	
	# D-Bus
	DBUS_INTERFACE = ZeitgeistDBusInterface.INTERFACE_NAME
	SIG_EVENT = "asaasay"
	
	# Extensions
	DEFAULT_EXTENSIONS = _get_extensions()

constants = _Constants()
