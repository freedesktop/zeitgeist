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
	DEFAULT_EXTENSIONS = [
		"_zeitgeist.engine.extensions.blacklist.Blacklist",
		"_zeitgeist.engine.extensions.datasource_registry.DataSourceRegistry",
		]

constants = _Constants()
