#! /usr/bin/env python

import sys
import os
import dbus.mainloop.glib
import gobject
from gettext import ngettext, gettext as _

sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from zeitgeist_engine.zeitgeist_dbus import RemoteInterface
from zeitgeist_engine.zeitgeist_datasink import datasink

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
object = RemoteInterface()
datasink.reload_callbacks.append(object.signal_updated)

mainloop = gobject.MainLoop()

if not '--no-trayicon' in sys.argv:
	from zeitgeist_engine.zeitgeist_trayicon import ZeitgeistTrayIcon
	trayicon = ZeitgeistTrayIcon(mainloop)

print _("Starting Zeitgeist service...")
mainloop.run()
