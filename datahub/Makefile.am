NULL =

bin_PROGRAMS = zeitgeist-datahub

AM_CPPFLAGS = \
	$(ZEITGEIST_DATAHUB_CFLAGS) \
	-include $(CONFIG_HEADER) \
	-I$(top_builddir)/libzeitgeist \
	-w \
	$(NULL)

AM_VALAFLAGS = \
	--target-glib=2.36 \
	--pkg gio-2.0 \
	--pkg gio-unix-2.0 \
	--pkg gtk+-3.0 \
	--pkg json-glib-1.0 \
	$(top_builddir)/libzeitgeist/zeitgeist-datamodel-2.0.vapi \
	$(top_builddir)/libzeitgeist/zeitgeist-2.0.vapi \
	$(top_srcdir)/config.vapi \
	-C \
	$(NULL)

BUILT_SOURCES = \
	zeitgeist_datahub_vala.stamp \
	$(NULL)

zeitgeist_datahub_VALASOURCES = \
	data-provider.vala \
	desktop-launch-listener.vala \
	kde-recent-document-provider.vala \
	recent-manager-provider.vala \
	utils.vala \
	zeitgeist-datahub.vala \
	$(NULL)

if ENABLE_TELEPATHY
AM_VALAFLAGS += --define ENABLE_TELEPATHY --pkg telepathy-glib
zeitgeist_datahub_VALASOURCES += telepathy-observer.vala
endif

if ENABLE_DOWNLOADS_MONITOR
AM_VALAFLAGS += --define ENABLE_DOWNLOADS_MONITOR
zeitgeist_datahub_VALASOURCES += downloads-directory-provider.vala
endif

nodist_zeitgeist_datahub_SOURCES = \
	$(BUILT_SOURCES) \
	$(zeitgeist_datahub_VALASOURCES:.vala=.c) \
	$(NULL)

zeitgeist_datahub_LDADD = $(top_builddir)/libzeitgeist/libzeitgeist-2.0.la $(ZEITGEIST_DATAHUB_LIBS)
zeitgeist_datahub_LDFLAGS = -export-dynamic -no-undefined

zeitgeist_datahub_vala.stamp: $(zeitgeist_datahub_VALASOURCES) Makefile
	$(AM_V_VALA)$(VALAC) \
		$(AM_VALAFLAGS) \
		$(filter %.vala %.c,$^)
	$(AM_V_at)touch $@

EXTRA_DIST = \
	$(zeitgeist_datahub_VALASOURCES) \
	$(NULL)

CLEANFILES = \
	$(nodist_zeitgeist_datahub_SOURCES) \
	$(NULL)

distclean-local:
	rm -f *.c *.o *.stamp *.~[0-9]~

VALA_V = $(VALA_V_$(V))
VALA_V_ = $(VALA_V_$(AM_DEFAULT_VERBOSITY))
VALA_V_0 = @echo "  VALAC " $^;
