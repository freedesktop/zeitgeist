NULL =

bin_PROGRAMS = zeitgeist-daemon
noinst_LTLIBRARIES = libzeitgeist-engine.la

AM_CPPFLAGS = \
	$(ZEITGEIST_CFLAGS) \
	-include $(CONFIG_HEADER) \
	-I$(top_builddir)/libzeitgeist \
	-w \
	$(NULL)

AM_VALAFLAGS = \
	--target-glib=2.36 \
	--pkg gio-2.0 \
	--pkg sqlite3 \
	--pkg posix \
	--pkg gmodule-2.0 \
	$(top_builddir)/libzeitgeist/zeitgeist-internal.vapi \
	$(top_builddir)/libzeitgeist/zeitgeist-datamodel-2.0.vapi \
	$(top_builddir)/libzeitgeist/zeitgeist-2.0.vapi \
	$(top_srcdir)/config.vapi \
	-C \
	$(NULL)

if EXPLAIN_QUERIES
AM_VALAFLAGS += \
	-D EXPLAIN_QUERIES \
	$(NULL)
endif

BUILT_SOURCES = \
	libzeitgeist_engine_la_vala.stamp \
	extensions_vala.stamp \
	zeitgeist_daemon_vala.stamp \
	$(NULL)

# Make sure every extension has only one vala file!
extensions_VALASOURCES = \
	ext-data-source-registry.vala \
	ext-blacklist.vala \
	ext-histogram.vala \
	ext-storage-monitor.vala \
	ext-fts.vala \
	ext-benchmark.vala \
	$(NULL)

libzeitgeist_engine_la_VALASOURCES = \
	engine.vala \
	extension.vala \
	extension-collection.vala \
	extension-store.vala \
	logging.vala \
	notify.vala \
	$(NULL)

nodist_libzeitgeist_engine_la_SOURCES = \
	$(BUILT_SOURCES) \
	$(libzeitgeist_engine_la_VALASOURCES:.vala=.c) \
	$(NULL)

zeitgeist_daemon_VALASOURCES = \
	zeitgeist-daemon.vala \
	$(NULL)

nodist_zeitgeist_daemon_SOURCES = \
	$(BUILT_SOURCES) \
	$(zeitgeist_daemon_VALASOURCES:.vala=.c) \
	$(extensions_VALASOURCES:.vala=.c) \
	$(NULL)

zeitgeist_daemon_LDADD = $(builddir)/libzeitgeist-engine.la $(top_builddir)/libzeitgeist/libzeitgeist-2.0.la $(ZEITGEIST_LIBS)
zeitgeist_daemon_LDFLAGS = -export-dynamic -no-undefined

libzeitgeist_engine_la_LIBADD = $(ZEITGEIST_LIBS)
libzeitgeist_engine_la_LDFLAGS = -avoid-version -non_shared -static

libzeitgeist_engine_la_vala.stamp: $(libzeitgeist_engine_la_VALASOURCES) Makefile
	$(AM_V_VALA)$(VALAC) \
		$(AM_VALAFLAGS) \
		-H zeitgeist-engine.h \
		--vapi zeitgeist-engine.vapi \
		--library zeitgeist-engine \
		$(filter %.vala %.c,$^)
	$(AM_V_at)touch $@

extensions_vala.stamp: libzeitgeist_engine_la_vala.stamp $(extensions_VALASOURCES) Makefile
	$(AM_V_VALA)$(foreach ext_src, $(filter %.vala,$^), \
		$(VALAC) \
			$(AM_VALAFLAGS) \
			-D BUILTIN_EXTENSIONS \
			$(builddir)/zeitgeist-engine.vapi \
			$(ext_src) || exit 1;)
	$(AM_V_at)touch $@

zeitgeist_daemon_vala.stamp: libzeitgeist_engine_la_vala.stamp extensions_vala.stamp $(zeitgeist_daemon_VALASOURCES) Makefile
	$(AM_V_VALA)$(VALAC) \
		$(AM_VALAFLAGS) \
		-D BUILTIN_EXTENSIONS \
		$(builddir)/zeitgeist-engine.vapi \
		$(filter %.vala %.c,$^)
	$(AM_V_at)touch $@

EXTRA_DIST = \
	$(libzeitgeist_engine_la_VALASOURCES) \
	$(zeitgeist_daemon_VALASOURCES) \
	$(extensions_VALASOURCES) \
	$(NULL)

CLEANFILES = \
	$(nodist_libzeitgeist_engine_la_SOURCES) \
	$(nodist_zeitgeist_daemon_SOURCES) \
	zeitgeist-engine.vapi \
	zeitgeist-engine.h \
	$(NULL)

distclean-local:
	rm -f *.c *.o *.stamp *.~[0-9]~

VALA_V = $(VALA_V_$(V))
VALA_V_ = $(VALA_V_$(AM_DEFAULT_VERBOSITY))
VALA_V_0 = @echo "  VALAC " $^;
