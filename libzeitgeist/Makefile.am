NULL =

lib_LTLIBRARIES = libzeitgeist-2.0.la

ONTOLOGY = \
	$(wildcard $(top_srcdir)/data/ontology/*.trig) \
	$(NULL)

AM_CPPFLAGS = \
	$(ZEITGEIST_CFLAGS) \
	-include $(CONFIG_HEADER) \
	-include $(top_srcdir)/libzeitgeist/internal \
	-w \
	$(NULL)

AM_VALAFLAGS = \
	--target-glib=2.26 \
	--pkg gio-2.0 \
	--pkg gio-unix-2.0 \
	--pkg sqlite3 \
	$(top_srcdir)/libzeitgeist/internal/zeitgeist-internal-2.0.vapi \
	$(top_srcdir)/config.vapi \
	--vapi zeitgeist-2.0.vapi \
	-H zeitgeist.h \
	-h zeitgeist-private.h \
	--library=zeitgeist \
	--gir=Zeitgeist-2.0.gir \
	$(NULL)

libzeitgeist_2_0_la_SOURCES = \
	data-source.vala \
	data-source-registry.vala \
	mimetype.vala \
	event.vala \
	subject.vala \
	timerange.vala \
	index.vala \
	log.vala \
	monitor.vala \
	ontology-uris.vala \
	ontology.vala \
	queued-proxy-wrapper.vala \
	remote.vala \
	result-set.vala \
	simple-result-set.vala \
	$(NULL)

libzeitgeist_2_0_la_LIBADD = $(ZEITGEIST_LIBS)
libzeitgeist_2_0_la_LDFLAGS = -version-info $(LIBZEITGEIST_LT_VERSION)

pkgconfigdir = $(libdir)/pkgconfig
pkgconfig_DATA = zeitgeist-2.0.pc

libzeitgeist_includedir=$(includedir)/zeitgeist-2.0/
libzeitgeist_include_HEADERS = \
	zeitgeist.h \
	$(NULL)

libzeitgeist_vapidir = $(datadir)/vala/vapi/
libzeitgeist_vapi_DATA = \
	zeitgeist-2.0.vapi
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

# We have to extract our own dlname from libzeitgeist-2.0.la; see bgo#658002.
# This is what g-ir-scanner does.
libzeitgeist_dlname = \
	`$(SED) -n "s/^dlname='\([A-Za-z0-9.+-]\+\)'/\1/p" libzeitgeist-2.0.la`

-include $(INTROSPECTION_MAKEFILE)
INTROSPECTION_GIRS =
INTROSPECTION_SCANNER_ARGS =
INTROSPECTION_COMPILER_ARGS = -l $(libzeitgeist_dlname)

if HAVE_INTROSPECTION
Zeitgeist-2.0.gir: libzeitgeist-2.0.la
GIRS = Zeitgeist-2.0.gir

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


ontology_vala.stamp: ontology.vala.in ontology-uris.vala.in \
		$(ONTOLOGY) $(top_srcdir)/data/ontology2code
	$(AM_V_GEN)$(top_srcdir)/data/ontology2code --vala
	@touch "$@"

ontology.vala ontology-uris.vala: ontology_vala.stamp

distclean-local:
	rm -f *.c *.o *.stamp *.~[0-9]~
