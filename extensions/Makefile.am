NULL =

#extensionsdir = $(libdir)/zeitgeist/extensions
noinst_LTLIBRARIES = ds-registry.la blacklist.la storage-monitor.la fts.la

AM_CPPFLAGS = \
	$(BLUEBIRD_CFLAGS) \
	-include $(CONFIG_HEADER) \
	-I $(top_srcdir)/src \
	-w \
	$(NULL)

VALAFLAGS = \
	--target-glib=2.26 \
	--pkg gio-2.0 \
	--pkg sqlite3 \
	--pkg gmodule-2.0 \
	$(top_srcdir)/src/zeitgeist-engine.vapi \
	$(NULL)

ds_registry_la_SOURCES = \
	ds-registry.vala \
	$(NULL)

ds_registry_la_LDFLAGS = -module -avoid-version

ds_registry_la_LIBADD = \
	$(BLUEBIRD_LIBS) \
	$(NULL)

blacklist_la_SOURCES = \
	blacklist.vala \
	$(NULL)

blacklist_la_LDFLAGS = -module -avoid-version

blacklist_la_LIBADD = \
	$(BLUEBIRD_LIBS) \
	$(NULL)

storage_monitor_la_SOURCES = \
	storage-monitor.la \
	$(NULL)

storage_monitor_la_LDFLAGS = -module -avoid-version

storage_monitor_la_LIBADD = \
	$(BLUEBIRD_LIBS) \
	$(NULL)
	

fts_la_SOURCES = \
	storage-monitor.la \
	$(NULL)

fts_la_LDFLAGS = -module -avoid-version

fts_la_LIBADD = \
	$(BLUEBIRD_LIBS) \
	$(NULL)
