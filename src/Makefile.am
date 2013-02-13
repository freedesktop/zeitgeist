NULL = 

AM_CPPFLAGS = \
	$(ZEITGEIST_CFLAGS) \
	-include $(CONFIG_HEADER) \
	-I $(top_srcdir)/libzeitgeist \
	-w \
	$(NULL)
	
AM_VALAFLAGS = \
	--target-glib=2.26 \
	-D BUILTIN_EXTENSIONS \
	--pkg gio-2.0 \
	--pkg sqlite3 \
	--pkg posix \
	--pkg gmodule-2.0 \
	$(top_srcdir)/libzeitgeist/zeitgeist-2.0.vapi \
	$(top_srcdir)/config.vapi \
	$(NULL)

if EXPLAIN_QUERIES
AM_VALAFLAGS += \
	-D EXPLAIN_QUERIES \
	$(NULL)
endif

#######################################################################################
#                                   DB INTERNAL LIBRARY                               #
#######################################################################################

noinst_lib_LTLIBRARIES = libzeitgeist-db-internal.la 
noinst_libdir = $(abs_builddir)

libzeitgeist_db_internal_la_LDFLAGS = \
	-avoid-version \
	-non_shared \
	-static \
	$(NULL)

libzeitgeist_db_internal_la_LIBADD = \
    $(top_builddir)/libzeitgeist/libzeitgeist-2.0.la \
    $(ZEITGEIST_LIBS) \
	$(NULL)


libzeitgeist_db_internal_la_VALASOURCES = \
	errors.vala \
	db-reader.vala \
	table-lookup.vala \
	sql-schema.vala \
	where-clause.vala \
	sql.vala \
	$(NULL)

nodist_libzeitgeist_db_internal_la_SOURCES = \
	$(libzeitgeist_db_internal_la_VALASOURCES:.vala=.c) \
	$(NULL)

zeitgeist-db-internal.h zeitgeist-db-internal.vapi: libzeitgeist_db_internal_vala.stamp

libzeitgeist_db_internal_vala.stamp: $(libzeitgeist_db_internal_la_VALASOURCES) Makefile
	$(AM_V_VALA)$(VALAC) \
		$(AM_VALAFLAGS) \
		-C -H zeitgeist-db-internal.h \
		--library zeitgeist-db-internal \
		--vapi zeitgeist-db-internal.vapi \
		$(filter %.vala %.c,$^)
	$(AM_V_at)touch $@

#######################################################################################
#                                      DAEMON                                         #
#######################################################################################

bin_PROGRAMS = zeitgeist-daemon

# Make sure every extension has only one vala file!
extensions_VALASOURCES = \
	ext-data-source-registry.vala \
	ext-blacklist.vala \
	ext-histogram.vala \
	ext-storage-monitor.vala \
	ext-fts.vala \
	ext-benchmark.vala \
	$(NULL)

zeitgeist_daemon_VALASOURCES = \
	zeitgeist-daemon.vala \
	engine.vala \
	extension.vala \
	extension-collection.vala \
	extension-store.vala \
	logging.vala \
	notify.vala \
	$(NULL)

zeitgeist_daemon_VALAFLAGS = \
	--vapidir $(builddir) \
	--pkg zeitgeist-db-private \
	$(NULL)

zeitgeist_daemon_SOURCES = \
	zeitgeist-engine_vala.stamp \
	$(zeitgeist_daemon_VALASOURCES:.vala=.c) \
	$(extensions_VALASOURCES:.vala=.c) \
	$(NULL)

zeitgeist_daemon_LDADD = \
	$(ZEITGEIST_LIBS) \
	$(top_builddir)/libzeitgeist/libzeitgeist-2.0.la \
	$(builddir)/libzeitgeist-db-internal.la \
	$(NULL)

zeitgeist_daemon_LDFLAGS = -export-dynamic -no-undefined

BUILT_SOURCES = libzeitgeist_db_internal_vala.stamp zeitgeist-engine_vala.stamp extensions_vala.stamp

zeitgeist-engine_vala.stamp: $(zeitgeist_daemon_VALASOURCES)
	$(VALA_V)$(VALAC) $(AM_VALAFLAGS) $(VALAFLAGS) -C -H zeitgeist-engine.h zeitgeist-db-internal.vapi --library zeitgeist-engine $^
	@touch "$@"

extensions_vala.stamp: zeitgeist-engine_vala.stamp $(extensions_VALASOURCES)
	$(AM_V_GEN)$(foreach ext_src,$(filter %.vala,$^),\
		$(VALAC) $(AM_VALAFLAGS) $(VALAFLAGS) $(EXT_FLAGS) -C zeitgeist-db-internal.vapi zeitgeist-engine.vapi $(ext_src) || exit 1;)
	@touch "$@"

EXTRA_DIST = \
	$(zeitgeist_daemon_VALASOURCES) \
	$(extensions_VALASOURCES) \
	zeitgeist-engine.h \
	zeitgeist-engine.vapi \
	zeitgeist-engine_vala.stamp \
	extensions_vala.stamp \
	$(NULL)

DISTCLEANFILES = \
	$(NULL)

distclean-local:
	rm -f *.c *.o *.stamp *.~[0-9]~

VALA_V = $(VALA_V_$(V))
VALA_V_ = $(VALA_V_$(AM_DEFAULT_VERBOSITY))
VALA_V_0 = @echo "  VALAC " $^;

