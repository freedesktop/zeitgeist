#! /usr/bin/env python
# -.- encoding: utf-8 -.-

import sys
import os
import gobject
import signal
import subprocess
import dbus.mainloop.glib
import gettext

from zeitgeist import config

gettext.install('gnome-zeitgeist', config.localedir, unicode=1)

from zeitgeist.engine.zeitgeist_dbus import RemoteInterface
from zeitgeist.engine.zeitgeist_datasink import datasink

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
mainloop = gobject.MainLoop()

object = RemoteInterface(mainloop = mainloop)
datasink.reload_callback = object.signal_updated

trayicon_app = "%s/bin/zeitgeist-trayicon.py" % config.prefix
if not '--no-trayicon' in sys.argv:
	subprocess.Popen(trayicon_app)

passive_loggers = "%s/bin/zeitgeist-datahub.py" % config.prefix
print passive_loggers
if not '--no-passive-loggers' in sys.argv and os.path.isfile(passive_loggers):
	subprocess.Popen(passive_loggers)

print _("Starting Zeitgeist service...")
mainloop.run()
