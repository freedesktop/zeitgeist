NULL =

lib_LTLIBRARIES = libzeitgeist-utils.la

ONTOLOGY = \
	$(wildcard $(top_srcdir)/data/ontology/*.trig) \
	$(NULL)

AM_CPPFLAGS = \
	$(ZEITGEIST_CFLAGS) \
	-include $(CONFIG_HEADER) \
	-w \
	$(NULL)

AM_VALAFLAGS = \
	--target-glib=2.26 \
	--pkg gio-2.0 \
	--pkg gio-unix-2.0 \
	--pkg sqlite3 \
	$(top_srcdir)/config.vapi \
	--vapi zeitgeist-utils.vapi \
	-H zeitgeist-utils.h \
	-h zeitgeist-utils-private.h \
	--library=zeitgeist-utils \
	$(NULL)

libzeitgeist_utils_la_SOURCES = \
	errors.vala \
	sql-schema.vala \
	sql.vala \
	table-lookup.vala \
	timestamp.vala \
	utils.vala \
	where-clause.vala \
	$(NULL)

libzeitgeist_utils_la_LIBADD = $(ZEITGEIST_LIBS)
libzeitgeist_utils_la_LDFLAGS = -version-info $(LIBZEITGEIST_LT_VERSION)

libzeitgeist_utils_includedir=$(includedir)/zeitgeist-utils/
libzeitgeist_utils_include_HEADERS = \
	zeitgeist-utils.h \
	$(NULL)

libzeitgeist_utils_vapidir = $(datadir)/vala/vapi/
libzeitgeist_utils_vapi_DATA = \
	zeitgeist-utils.vapi
	$(NULL)

EXTRA_DIST = \
	ontology.vala.in \
	ontology-uris.vala.in \
	$(NULL)

DISTCLEANFILES = \
	ontology.vala \
	ontology-uris.vala \
	zeitgeist-utils.vapi
	$(NULL)

CLEANFILES =
MAINTAINERCLEANFILES =

