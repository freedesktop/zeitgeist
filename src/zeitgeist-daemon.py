#! /usr/bin/env python
# -.- encoding: utf-8 -.-

import sys
import os
import gobject
import signal
import subprocess
import dbus.mainloop.glib
import gettext

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
gettext.install('gnome-zeitgeist', '/usr/share/locale', unicode=1)

from zeitgeist_engine.zeitgeist_dbus import RemoteInterface
from zeitgeist_engine.zeitgeist_datasink import datasink
from zeitgeist_shared.basics import BASEDIR

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
mainloop = gobject.MainLoop()

object = RemoteInterface(mainloop = mainloop)
datasink.reload_callback = object.signal_updated

trayicon_app = "%s/src/zeitgeist_gui/zeitgeist-trayicon.py" % BASEDIR
if not '--no-trayicon' in sys.argv and os.path.isfile(trayicon_app):
	subprocess.Popen(trayicon_app)

passive_loggers = "%s/src/zeitgeist_loggers/zeitgeist-datahub.py" % BASEDIR
print passive_loggers
if not '--no-passive-loggers' in sys.argv and os.path.isfile(passive_loggers):
	subprocess.Popen(passive_loggers)

print _("Starting Zeitgeist service...")
mainloop.run()
