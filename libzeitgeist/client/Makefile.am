NULL =

lib_LTLIBRARIES = libzeitgeist-client-1.0.la

AM_CPPFLAGS = \
	$(ZEITGEIST_CFLAGS) \
	-include $(CONFIG_HEADER) \
	-I $(top_srcdir)/libzeitgeist \
	-I $(top_srcdir)/src \
	-w \
	$(NULL)

AM_VALAFLAGS = \
	--target-glib=2.26 \
	--pkg gio-2.0 \
	--pkg gio-unix-2.0 \
	--pkg sqlite3 \
	$(top_srcdir)/config.vapi \
	$(top_srcdir)/libzeitgeist/zeitgeist-2.0.vapi \
	$(top_srcdir)/src/zeitgeist-db-internal.vapi \
	--vapi zeitgeist-client.vapi \
	-H zeitgeist-client.h \
	-h zeitgeist-client-private.h \
	--library=zeitgeist-client \
	--gir=ZeitgeistClient-1.0.gir \
	$(NULL)

libzeitgeist_client_1_0_la_SOURCES = \
	log.vala \
	index.vala \
	$(NULL)

libzeitgeist_client_1_0_la_LIBADD = \
    $(top_builddir)/libzeitgeist/libzeitgeist-2.0.la \
    $(top_builddir)/src/libzeitgeist-db-internal.la \
    $(ZEITGEIST_LIBS) \
    $(NULL)$
libzeitgeist_client_1_0_la_LDFLAGS = -version-info $(LIBZEITGEIST_LT_VERSION)

libzeitgeist_client_includedir=$(includedir)/zeitgeist-client/
libzeitgeist_client_include_HEADERS = \
	zeitgeist-client.h \
	$(NULL)

libzeitgeist_client_vapidir = $(datadir)/vala/vapi/
libzeitgeist_client_vapi_DATA = \
	zeitgeist-client.vapi \
	$(NULL)

DISTCLEANFILES = \
	$(NULL)

CLEANFILES =
MAINTAINERCLEANFILES =

# We have to extract our own dlname from libzeitgeist-2.0.la; see bgo#658002.
# This is what g-ir-scanner does.
libzeitgeist_client_dlname = \
	`$(SED) -n "s/^dlname='\([A-Za-z0-9.+-]\+\)'/\1/p" libzeitgeist-client-1.0.la`

-include $(INTROSPECTION_MAKEFILE)

if HAVE_INTROSPECTION
ZeitgeistClient-1.0.gir: libzeitgeist-client-1.0.la
ZeitgeistClient-1.0.typelib: ZeitgeistClient-1.0.gir
	${INTROSPECTION_COMPILER} -l ${libzeitgeist_client_dlname} --includedir ${INTROSPECTION_GIRDIR} $(top_srcdir)/libzeitgeist/Zeitgeist-2.0.gir -o $@ $^
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
