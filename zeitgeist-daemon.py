#! /usr/bin/env python
# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
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

import sys
import os
import gobject
import signal
import subprocess
import dbus.mainloop.glib
import gettext
import logging

from zeitgeist import _config
_config.setup_path()

gettext.install("zeitgeist", _config.localedir, unicode=1)
logging.basicConfig(level=logging.DEBUG)

arg1 = sys.argv[1].strip("-") if len(sys.argv) == 2 else None
if arg1 == "version":
	print "Zeitgeist %s" % _config.VERSION
	sys.exit(0)
elif arg1 == "rocks":
	print "Deine Mudda rocks!"
	sys.exit(0)
elif arg1 == "help":
	print "Please see \"man zeitgeist-daemon\"."
	sys.exit(0)

from _zeitgeist.engine.remote import RemoteInterface

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
mainloop = gobject.MainLoop()

try:
	RemoteInterface(mainloop = mainloop)
except RuntimeError, e:
	logging.error(str(e))
	sys.exit(1)

passive_loggers = "%s/zeitgeist-datahub.py" % _config.bindir
if arg1 != "no-passive-loggers":
	if os.path.isfile(passive_loggers):
		subprocess.Popen(passive_loggers)
	else:
		logging.warning("%s not found, not starting datahub" % passive_loggers)

logging.info(_(u"Starting Zeitgeist service..."))
mainloop.run()
