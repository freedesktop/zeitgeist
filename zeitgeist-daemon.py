#! /usr/bin/env python
# -.- encoding: utf-8 -.-

import sys
import atexit
import os
import gobject
import signal
import subprocess
import dbus.mainloop.glib
import gettext

from zeitgeist import config

gettext.install('gnome-zeitgeist', config.localedir, unicode=1)

from zeitgeist.engine.engine import engine
from zeitgeist.engine.remote import RemoteInterface

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
mainloop = gobject.MainLoop()

object = RemoteInterface(mainloop = mainloop)
engine.reload_callback = object.signal_updated

trayicon_app = "%s/zeitgeist-trayicon.py" % config.bindir
if not '--no-trayicon' in sys.argv:
	subprocess.Popen(trayicon_app)


def cleanup():
	p.kill() # supported from python 2.6
	print 'cleaned up!'


passive_loggers = "%s/zeitgeist-datahub.py" % config.bindir
print passive_loggers
p = None
if not '--no-passive-loggers' in sys.argv and os.path.isfile(passive_loggers):
	p =	subprocess.Popen(passive_loggers)

if p:
	atexit.register(cleanup)
	
	
print _("Starting Zeitgeist service...")
mainloop.run()
