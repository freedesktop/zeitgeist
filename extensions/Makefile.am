if HAVE_FTS
SUBDIRS = fts++
endif

NULL =

zeitgeist_libs = \
	$(top_builddir)/libzeitgeist/libzeitgeist-2.0.la \
	$(ZEITGEIST_LIBS)

#extensionsdir = $(libdir)/zeitgeist/extensions
noinst_LTLIBRARIES = ds-registry.la blacklist.la storage-monitor.la fts.la benchmark.la

AM_CPPFLAGS = \
	$(ZEITGEIST_CFLAGS) \
	-include $(CONFIG_HEADER) \
	-I $(top_srcdir)/libzeitgeist \
	-I $(top_srcdir)/src \
	-w \
	$(NULL)

VALAFLAGS = \
	--target-glib=2.26 \
	--pkg gio-2.0 \
	--pkg sqlite3 \
	--pkg gmodule-2.0 \
	$(top_srcdir)/libzeitgeist/zeitgeist-private.vapi \
	$(top_srcdir)/src/zeitgeist-engine.vapi \
	$(NULL)

ds_registry_la_SOURCES = \
	ds-registry.vala \
	$(NULL)

ds_registry_la_LDFLAGS = -module -avoid-version

ds_registry_la_LIBADD = \
	$(ZEITGEIST_LIBS) \
	$(NULL)

blacklist_la_SOURCES = \
	blacklist.vala \
	$(NULL)

blacklist_la_LDFLAGS = -module -avoid-version

blacklist_la_LIBADD = \
	$(ZEITGEIST_LIBS) \
	$(NULL)

storage_monitor_la_SOURCES = \
	storage-monitor.vala \
	$(NULL)

storage_monitor_la_LDFLAGS = -module -avoid-version

storage_monitor_la_LIBADD = \
	$(ZEITGEIST_LIBS) \
	$(NULL)
	

fts_la_SOURCES = \
	fts.vala \
	$(NULL)

fts_la_LDFLAGS = -module -avoid-version

fts_la_LIBADD = \
	$(ZEITGEIST_LIBS) \
	$(NULL)
	
benchmark_la_SOURCES = \
	benchmark.vala \
	$(NULL)

benchmark_la_LDFLAGS = -module -avoid-version

benchmark_la_LIBADD = \
	$(ZEITGEIST_LIBS) \
	$(NULL)

distclean-local:
	rm -f *.c *.o *.stamp *.~[0-9]~
