NULL =

lib_LTLIBRARIES = libzeitgeistclient-1.0.la

AM_CPPFLAGS = \
	$(ZEITGEIST_CFLAGS) \
	-include $(CONFIG_HEADER) \
	-I $(top_srcdir)/libzeitgeist \
	-w \
	$(NULL)

AM_VALAFLAGS = \
	--target-glib=2.26 \
	--pkg gio-2.0 \
	--pkg gio-unix-2.0 \
	--pkg sqlite3 \
	$(top_srcdir)/config.vapi \
	$(top_srcdir)/libzeitgeist/zeitgeist-2.0.vapi \
	--vapi zeitgeistclient.vapi \
	-H zeitgeistclient.h \
	-h zeitgeistclient-private.h \
	--library=zeitgeistclient \
	--gir=ZeitgeistClient-1.0.gir \
	$(NULL)

libzeitgeistclient_1_0_la_SOURCES = \
	log.vala \
	$(NULL)

libzeitgeistclient_1_0_la_LIBADD = \
    $(top_builddir)/libzeitgeist/libzeitgeist-2.0.la \
    $(ZEITGEIST_LIBS) \
    $(NULL)$
libzeitgeistclient_1_0_la_LDFLAGS = -version-info $(LIBZEITGEIST_LT_VERSION)

libzeitgeistclient_includedir=$(includedir)/zeitgeistclient/
libzeitgeistclient_include_HEADERS = \
	zeitgeistclient.h \
	$(NULL)

libzeitgeistclient_vapidir = $(datadir)/vala/vapi/
libzeitgeistclient_vapi_DATA = \
	zeitgeistclient.vapi \
	$(NULL)

DISTCLEANFILES = \
	log.vala \
	zeitgeistclient.vapi \
	$(NULL)

CLEANFILES =
MAINTAINERCLEANFILES =

# We have to extract our own dlname from libzeitgeist-2.0.la; see bgo#658002.
# This is what g-ir-scanner does.
libzeitgeistclient_dlname = \
	`$(SED) -n "s/^dlname='\([A-Za-z0-9.+-]\+\)'/\1/p" libzeitgeistclient-1.0.la`

-include $(INTROSPECTION_MAKEFILE)
INTROSPECTION_GIRS =
INTROSPECTION_SCANNER_ARGS =
INTROSPECTION_COMPILER_ARGS = -l $(libzeitgeistclient_dlname)

if HAVE_INTROSPECTION
ZeitgeistClient-1.0.gir: libzeitgeistclient-1.0.la
GIRS = ZeitgeistClient-1.0.gir

girdir = $(datadir)/gir-1.0
dist_gir_DATA = $(GIRS)

MAINTAINERCLEANFILES += $(dist_gir_DATA)

typelibdir = $(libdir)/girepository-1.0
nodist_typelib_DATA = $(GIRS:.gir=.typelib)

CLEANFILES += $(nodist_typelib_DATA)
endif

MAINTAINERCLEANFILES += \
	$(BUILT_SOURCES) \
	$(NULL)
