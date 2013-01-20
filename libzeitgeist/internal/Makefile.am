NULL =

lib_LTLIBRARIES = libzeitgeist-internal-2.0.la

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
	--vapi zeitgeist-internal-2.0.vapi \
	-H zeitgeist-internal.h \
	-h zeitgeist-internal-private.h \
	--library=zeitgeist-internal \
	$(NULL)

libzeitgeist_internal_2_0_la_SOURCES = \
	enumerations.vala \
	errors.vala \
	sql-schema.vala \
	sql.vala \
	table-lookup.vala \
	timestamp.vala \
	utils.vala \
	where-clause.vala \
	$(NULL)

libzeitgeist_internal_2_0_la_LIBADD = $(ZEITGEIST_LIBS)
libzeitgeist_internal_2_0_la_LDFLAGS = -version-info $(LIBZEITGEIST_LT_VERSION)

libzeitgeist_internal_includedir=$(includedir)/zeitgeist-internal-2.0/
libzeitgeist_internal_include_HEADERS = \
	zeitgeist-internal.h \
	$(NULL)

libzeitgeist_internal_vapidir = $(datadir)/vala/vapi/
libzeitgeist_internal_vapi_DATA = \
	zeitgeist-internal-2.0.vapi
	$(NULL)

EXTRA_DIST = \
	ontology.vala.in \
	ontology-uris.vala.in \
	$(NULL)

DISTCLEANFILES = \
	ontology.vala \
	ontology-uris.vala \
	zeitgeist-2.0.vapi \
	$(NULL)


CLEANFILES =
MAINTAINERCLEANFILES =

