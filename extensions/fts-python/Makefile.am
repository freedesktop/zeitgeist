NULL =

ftsdir = $(pkgdatadir)/fts-python
dist_fts_SCRIPTS = \
	datamodel.py \
	constants.py \
	fts.py \
	lrucache.py \
	sql.py \
	$(NULL)

servicedir = $(DBUS_SERVICES_DIR)
service_DATA = org.gnome.zeitgeist.fts.service

org.gnome.zeitgeist.fts.service: org.gnome.zeitgeist.fts.service.in
	$(AM_V_GEN)sed  -e s!\@pkgdatadir\@!$(pkgdatadir)! < $< > $@
org.gnome.zeitgeist.fts.service: Makefile

EXTRA_DIST = org.gnome.zeitgeist.fts.service.in
CLEANFILES = org.gnome.zeitgeist.fts.service
