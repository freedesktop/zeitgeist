#! /usr/bin/env python

import sys
import os
import dbus.mainloop.glib
import gobject
from gettext import ngettext, gettext as _

sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from zeitgeist_engine.zeitgeist_dbus import RemoteInterface
from zeitgeist_engine.zeitgeist_util import ZeitgeistTrayIcon
from zeitgeist_engine.zeitgeist_datasink import datasink


if __name__ == "__main__":
	
	dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
	object = RemoteInterface()
	datasink.reload_callbacks.append(object.signal_updated)
	trayicon = ZeitgeistTrayIcon()
	
	mainloop = gobject.MainLoop()
	print _("Running Zeitgeist service.")
	mainloop.run()
