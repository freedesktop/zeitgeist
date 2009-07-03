SUBDIRS = epiphany

servicedir = $(datadir)/dbus-1/services
nodist_service_DATA = org.gnome.zeitgeist.service

org.gnome.zeitgeist.service: org.gnome.zeitgeist.service.in
	sed	-e s!\@prefix\@!$(prefix)! < $< > $@
org.gnome.zeitgeist.service: Makefile

CLEANFILES = org.gnome.zeitgeist.service
EXTRA_DIST = org.gnome.zeitgeist.service.in

all-local: org.gnome.zeitgeist.service
