@INTLTOOL_DESKTOP_RULE@

desktopdir = $(datadir)/applications
desktop_in_files = zeitgeist-journal.desktop.in zeitgeist-trayicon.desktop.in
desktop_DATA = $(desktop_in_files:.desktop.in=.desktop)

servicedir = $(datadir)/dbus-1/services
service_DATA = org.gnome.Zeitgeist.service

CLEANFILES = $(desktop_DATA)

EXTRA_DIST = test-daemon.py $(desktop_DATA) $(service_DATA)

install-data-hook: $(UPDATE_DESKTOP)

uninstall-hook: $(UPDATE_DESKTOP)

