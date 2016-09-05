NULL =

if HAVE_FTS
SUBDIRS = fts++
endif

#extensionsdir = $(libdir)/zeitgeist/extensions
noinst_LTLIBRARIES = \
	benchmark.la \
	blacklist.la \
	ds-registry.la \
	fts.la \
	histogram.la \
	storage-monitor.la \
	$(NULL)


AM_CPPFLAGS = \
	$(ZEITGEIST_CFLAGS) \
	-include $(CONFIG_HEADER) \
	-I $(top_builddir)/libzeitgeist \
	-I $(top_builddir)/src \
	-w \
	$(NULL)

AM_VALAFLAGS = \
	--target-glib=2.36 \
	--pkg gio-2.0 \
	--pkg sqlite3 \
	--pkg gmodule-2.0 \
	$(top_builddir)/libzeitgeist/zeitgeist-datamodel-2.0.vapi \
	$(top_builddir)/libzeitgeist/zeitgeist-2.0.vapi \
	$(top_builddir)/libzeitgeist/zeitgeist-internal.vapi \
	$(top_builddir)/src/zeitgeist-engine.vapi \
	$(NULL)

AM_LDFLAGS = \
	-module -avoid-version \
	$(ZEITGEIST_LIBS) \
	$(top_builddir)/libzeitgeist/libzeitgeist-2.0.la \
	$(top_builddir)/libzeitgeist/libzeitgeist-internal.la \
	$(top_builddir)/src/libzeitgeist-engine.la \
	$(NULL)

benchmark_la_SOURCES = benchmark.vala
blacklist_la_SOURCES = blacklist.vala
ds_registry_la_SOURCES = ds-registry.vala
fts_la_SOURCES = fts.vala
histogram_la_SOURCES = histogram.vala
storage_monitor_la_SOURCES = storage-monitor.vala

distclean-local:
	rm -f *.c *.o *.stamp *.~[0-9]~
