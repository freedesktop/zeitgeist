SUBDIRS = test
NULL = 

noinst_LTLIBRARIES = libzeitgeist-internal.la
libexec_PROGRAMS = zeitgeist-fts

servicedir = $(DBUS_SERVICES_DIR)
service_DATA = org.gnome.zeitgeist.fts.service

org.gnome.zeitgeist.fts.service: org.gnome.zeitgeist.fts.service.in
	$(AM_V_GEN)sed  -e s!\@libexecdir\@!$(libexecdir)! < $< > $@
org.gnome.zeitgeist.fts.service: Makefile

AM_CPPFLAGS = \
	$(ZEITGEIST_CFLAGS) \
	$(XAPIAN_CXXFLAGS) \
	-include $(CONFIG_HEADER) \
	-w \
	$(NULL)

AM_VALAFLAGS = \
	--target-glib=2.26 \
	--pkg gio-2.0 \
	--pkg sqlite3 \
	--pkg posix \
	--pkg gmodule-2.0 \
	$(top_srcdir)/config.vapi \
	$(NULL)

libzeitgeist_internal_la_VALASOURCES = \
	../../libzeitgeist/datamodel.vala \
	../../libzeitgeist/ontology-uris.vala \
	../../libzeitgeist/ontology.vala \
	../../libzeitgeist/utils.vala \
	db-reader.vala \
	engine.vala \
	sql.vala \
	../../libzeitgeist/remote.vala \
	errors.vala \
	table-lookup.vala \
	sql-schema.vala \
	where-clause.vala \
	../../libzeitgeist/mimetype.vala \
	ext-dummies.vala \
	$(NULL)

libzeitgeist_internal_la_SOURCES = \
	zeitgeist-internal.stamp \
	$(libzeitgeist_internal_la_VALASOURCES:.vala=.c) \
	$(NULL)

libzeitgeist_internal_la_LIBADD = \
	$(ZEITGEIST_LIBS) \
	$(NULL)

zeitgeist_fts_VALASOURCES = \
	zeitgeist-fts.vala \
	$(NULL)

zeitgeist_fts_SOURCES = \
	zeitgeist-fts_vala.stamp \
	$(zeitgeist_fts_VALASOURCES:.vala=.c) \
	controller.cpp \
	controller.h \
	fts.cpp \
	fts.h \
	indexer.cpp \
	indexer.h \
	task.cpp \
	task.h \
	stringutils.cpp \
	stringutils.h \
	$(NULL)

zeitgeist_fts_LDADD = \
	$(builddir)/libzeitgeist-internal.la \
	$(XAPIAN_LIBS) \
	$(NULL)

if HAVE_DEE_ICU
AM_CPPFLAGS += $(DEE_ICU_CFLAGS)
zeitgeist_fts_LDADD += $(DEE_ICU_LIBS)
endif

BUILT_SOURCES = \
	zeitgeist-internal.stamp \
	zeitgeist-fts_vala.stamp \
	$(NULL)

zeitgeist-internal.stamp: $(libzeitgeist_internal_la_VALASOURCES)
	$(VALA_V)$(VALAC) $(AM_VALAFLAGS) $(VALAFLAGS) -C -H zeitgeist-internal.h --library zeitgeist-internal $^
	@touch "$@"

zeitgeist-fts_vala.stamp: $(zeitgeist_fts_VALASOURCES)
	$(VALA_V)$(VALAC) $(AM_VALAFLAGS) $(VALAFLAGS) \
	$(srcdir)/zeitgeist-internal.vapi $(srcdir)/fts.vapi -C $^
	@touch "$@"

EXTRA_DIST = \
	$(libzeitgeist_internal_la_VALASOURCES) \
	$(zeitgeist_fts_VALASOURCES) \
	zeitgeist-fts_vala.stamp \
	zeitgeist-internal.h \
	zeitgeist-internal.vapi \
	org.gnome.zeitgeist.fts.service.in \
	$(NULL)

CLEANFILES = org.gnome.zeitgeist.fts.service

DISTCLEANFILES = \
	$(NULL)

distclean-local:
	rm -f *.c *.o *.stamp *.~[0-9]~

VALA_V = $(VALA_V_$(V))
VALA_V_ = $(VALA_V_$(AM_DEFAULT_VERBOSITY))
VALA_V_0 = @echo "  VALAC " $^;

