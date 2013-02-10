NULL =

lib_LTLIBRARIES = libzeitgeist-client.la


AM_CPPFLAGS = \
	$(ZEITGEIST_CFLAGS) \
	-include $(CONFIG_HEADER) \
	-I $(top_srcdir)/libzeitgeist \
	-I $(top_srcdir)/src/ \
	-w \
	$(NULL)

AM_VALAFLAGS = \
	--target-glib=2.26 \
	--pkg gio-2.0 \
	--pkg gio-unix-2.0 \
	--pkg sqlite3 \
	$(top_srcdir)/libzeitgeist/zeitgeist-2.0.vapi \
	$(top_srcdir)/src/zeitgeist-engine.vapi \
	$(top_srcdir)/config.vapi \
	--vapi zeitgeist-client.vapi \
	-H zeitgeist-client.h \
	-h zeitgeist-client-private.h \
	--library=zeitgeist-client \
	$(NULL)

libzeitgeist_client_la_SOURCES = \
	log.vala \
	$(NULL)

libzeitgeist_client_la_LIBADD = \
    $(top_builddir)/libzeitgeist/libzeitgeist-2.0.la \
    $(ZEITGEIST_LIBS) \
    $(NULL)$
libzeitgeist_client_la_LDFLAGS = -version-info $(LIBZEITGEIST_LT_VERSION)

libzeitgeist_client_includedir=$(includedir)/zeitgeist-client/
libzeitgeist_client_include_HEADERS = \
	zeitgeist-client.h \
	$(NULL)

libzeitgeist_client_vapidir = $(datadir)/vala/vapi/
libzeitgeist_client_vapi_DATA = \
	zeitgeist-client.vapi \
	$(NULL)

DISTCLEANFILES = \
	zeitgeist-client.vapi \
	$(NULL)

CLEANFILES =
MAINTAINERCLEANFILES =

