NULL =

SUBDIRS = test

pkglibexec_PROGRAMS = zeitgeist-fts

servicedir = $(datadir)/dbus-1/services
nodist_service_DATA = org.gnome.zeitgeist.SimpleIndexer.service

systemd_userdir = $(prefix)/lib/systemd/user
nodist_systemd_user_DATA = zeitgeist-fts.service

%.service: %.service.in
	$(AM_V_GEN)sed -e "s|@pkglibexecdir[@]|$(pkglibexecdir)|" $< > $@

AM_CPPFLAGS = \
	$(ZEITGEIST_CFLAGS) \
	$(XAPIAN_CXXFLAGS) \
	-include $(CONFIG_HEADER) \
	-I $(top_builddir)/libzeitgeist \
	-I $(top_builddir)/src \
	-w \
	$(NULL)

AM_VALAFLAGS = \
	--target-glib=2.36 \
	--pkg gio-2.0 \
	--pkg sqlite3 \
	--pkg posix \
	--pkg gmodule-2.0 \
	$(top_builddir)/libzeitgeist/zeitgeist-datamodel-2.0.vapi \
	$(top_builddir)/libzeitgeist/zeitgeist-2.0.vapi \
	$(top_builddir)/libzeitgeist/zeitgeist-internal.vapi \
	$(top_builddir)/src/zeitgeist-engine.vapi \
	$(srcdir)/fts.vapi \
	$(top_srcdir)/config.vapi \
	-C \
	$(NULL)

zeitgeist_fts_VALASOURCES = \
	zeitgeist-fts.vala \
	$(NULL)

zeitgeist_fts_CSOURCES = \
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

nodist_zeitgeist_fts_SOURCES = \
	$(BUILT_SOURCES) \
	$(zeitgeist_fts_CSOURCES) \
	$(zeitgeist_fts_VALASOURCES:.vala=.c) \
	$(NULL)

zeitgeist_fts_LDADD = \
	$(top_builddir)/libzeitgeist/libzeitgeist-2.0.la \
	$(top_builddir)/libzeitgeist/libzeitgeist-internal.la \
	$(top_builddir)/src/libzeitgeist-engine.la \
	$(XAPIAN_LIBS) \
	$(NULL)

zeitgeist_fts_LDFLAGS = -export-dynamic -no-undefined

if HAVE_DEE_ICU
AM_CPPFLAGS += $(DEE_ICU_CFLAGS)
zeitgeist_fts_LDADD += $(DEE_ICU_LIBS)
endif

BUILT_SOURCES = \
	zeitgeist-fts_vala.stamp \
	$(NULL)

zeitgeist-fts_vala.stamp: $(engine_VALASOURCES) $(zeitgeist_fts_VALASOURCES) Makefile
	$(AM_V_VALA)$(VALAC) \
		$(AM_VALAFLAGS) \
		$(filter %.vala %.c,$^)
	$(AM_V_at)touch $@

EXTRA_DIST = \
	$(zeitgeist_fts_VALASOURCES) \
	$(zeitgeist_fts_CSOURCES) \
	org.gnome.zeitgeist.SimpleIndexer.service.in \
	fts.vapi \
	zeitgeist-fts.service.in \
	$(NULL)

CLEANFILES = \
	$(BUILT_SOURCES) \
	$(zeitgeist_fts_VALASOURCES:.vala=.c) \
	org.gnome.zeitgeist.SimpleIndexer.service \
	zeitgeist-fts.service \
	$(NULL)

DISTCLEANFILES = \
	$(NULL)

distclean-local:
	rm -f *.c *.o *.stamp *.~[0-9]~

VALA_V = $(VALA_V_$(V))
VALA_V_ = $(VALA_V_$(AM_DEFAULT_VERBOSITY))
VALA_V_0 = @echo "  VALAC " $^;

