#! /usr/bin/env python

import sys
import os
import gobject
import signal
import subprocess
import dbus.mainloop.glib
from gettext import ngettext, gettext as _

sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from zeitgeist_engine.zeitgeist_dbus import RemoteInterface
from zeitgeist_engine.zeitgeist_datasink import datasink
from zeitgeist_shared.basics import BASEDIR

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
mainloop = gobject.MainLoop()

object = RemoteInterface(mainloop = mainloop)
datasink.reload_callbacks.append(object.signal_updated)

trayicon_app = "%s/src/zeitgeist_gui/zeitgeist-trayicon.py" % BASEDIR
if not '--no-trayicon' in sys.argv and os.path.isfile(trayicon_app):
	subprocess.Popen(trayicon_app)

print _("Starting Zeitgeist service...")
mainloop.run()
