NULL =

lib_LTLIBRARIES = libzeitgeist-2.0.la
noinst_LTLIBRARIES = libzeitgeist-datamodel-2.0.la libzeitgeist-internal.la

BUILT_SOURCES = \
	libzeitgeist_datamodel_2_0_la_vala.stamp \
	libzeitgeist_2_0_la_vala.stamp \
	libzeitgeist_internal_la_vala.stamp \
	zeitgeist.h \
	zeitgeist-2.0.vapi \
	zeitgeist-datamodel.h \
	zeitgeist-datamodel-2.0.vapi \
	zeitgeist-internal.h \
	zeitgeist-internal.vapi \
	$(NULL)

ONTOLOGY = \
	$(wildcard $(top_srcdir)/data/ontology/*.trig) \
	$(NULL)

AM_CPPFLAGS = \
	$(ZEITGEIST_CFLAGS) \
	-include $(CONFIG_HEADER) \
	-I $(builddir) \
	-w \
	$(NULL)

AM_VALAFLAGS = \
	--target-glib=2.36 \
	--pkg gio-2.0 \
	--pkg gio-unix-2.0 \
	--pkg sqlite3 \
	$(top_srcdir)/config.vapi \
	-C \
	$(NULL)

if EXPLAIN_QUERIES
AM_VALAFLAGS += \
	-D EXPLAIN_QUERIES \
	$(NULL)
endif

libzeitgeist_internal_la_VALAFLAGS = \
	$(builddir)/zeitgeist-datamodel-2.0.vapi \
	--vapi zeitgeist-internal.vapi \
	-H zeitgeist-internal.h \
	$(NULL)

libzeitgeist_internal_la_CFLAGS = -fPIC
libzeitgeist_internal_la_LIBADD = $(ZEITGEIST_LIBS)
libzeitgeist_internal_la_LDFLAGS = -avoid-version -non_shared -static

libzeitgeist_datamodel_2_0_la_VALAFLAGS = \
	--vapi zeitgeist-datamodel-2.0.vapi \
	-H zeitgeist-datamodel.h \
	--library zeitgeist-2.0 \
	$(NULL)

libzeitgeist_datamodel_2_0_la_CFLAGS = -fPIC
libzeitgeist_datamodel_2_0_la_LIBADD = $(ZEITGEIST_LIBS)
libzeitgeist_datamodel_2_0_la_LDFLAGS = -avoid-version -non_shared -static

libzeitgeist_2_0_la_VALAFLAGS = \
	$(builddir)/zeitgeist-datamodel-2.0.vapi \
	$(builddir)/zeitgeist-internal.vapi \
	--vapi zeitgeist-2.0.vapi \
	-H zeitgeist.h \
	--library zeitgeist-2.0 \
	$(NULL)

libzeitgeist_2_0_la_LIBADD = $(builddir)/libzeitgeist-datamodel-2.0.la $(builddir)/libzeitgeist-internal.la $(ZEITGEIST_LIBS)
libzeitgeist_2_0_la_LDFLAGS = -version-info $(LIBZEITGEIST_LT_VERSION)

libzeitgeist_internal_la_VALASOURCES = \
	db-reader.vala \
	sql.vala \
	sql-schema.vala \
	table-lookup.vala \
	where-clause.vala \
	$(NULL)

nodist_libzeitgeist_internal_la_SOURCES = \
	$(BUILT_SOURCES) \
	$(libzeitgeist_internal_la_VALASOURCES:.vala=.c) \
	$(NULL)

libzeitgeist_2_0_la_VALASOURCES = \
	data-source-registry.vala \
	index.vala \
	log.vala \
	monitor.vala \
	queued-proxy-wrapper.vala \
	remote.vala \
	$(NULL)

nodist_libzeitgeist_2_0_la_SOURCES = \
	$(BUILT_SOURCES) \
	$(libzeitgeist_2_0_la_VALASOURCES:.vala=.c) \
	$(NULL)

libzeitgeist_datamodel_2_0_la_VALASOURCES = \
	data-source.vala \
	errors.vala \
	mimetype.vala \
	enumerations.vala \
	event.vala \
	subject.vala \
	timerange.vala \
	timestamp.vala \
	ontology-uris.vala \
	ontology.vala \
	result-set.vala \
	simple-result-set.vala \
	utils.vala \
	$(NULL)

nodist_libzeitgeist_datamodel_2_0_la_SOURCES = \
	$(BUILT_SOURCES) \
	$(libzeitgeist_datamodel_2_0_la_VALASOURCES:.vala=.c) \
	$(NULL)

zeitgeist-internal.h zeitgeist-internal.vapi: libzeitgeist_internal_la_vala.stamp

libzeitgeist_internal_la_vala.stamp: libzeitgeist_datamodel_2_0_la_vala.stamp $(libzeitgeist_internal_la_VALASOURCES) Makefile
	$(AM_V_VALA)$(VALAC) \
		$(AM_VALAFLAGS) $(libzeitgeist_internal_la_VALAFLAGS) \
		$(filter %.vala %.c,$^)
	$(AM_V_at)touch $@

zeitgeist-datamodel.h zeitgeist-datamodel-2.0.vapi: libzeitgeist_datamodel_2_0_la_vala.stamp

libzeitgeist_datamodel_2_0_la_vala.stamp: $(libzeitgeist_datamodel_2_0_la_VALASOURCES) Makefile
	$(AM_V_VALA)$(VALAC) \
		$(AM_VALAFLAGS) $(libzeitgeist_datamodel_2_0_la_VALAFLAGS) \
		$(filter %.vala %.c,$^)
	$(AM_V_at)touch $@

zeitgeist.h zeitgeist-2.0.vapi: libzeitgeist_2_0_la_vala.stamp

libzeitgeist_2_0_la_vala.stamp: libzeitgeist_datamodel_2_0_la_vala.stamp libzeitgeist_internal_la_vala.stamp $(libzeitgeist_2_0_la_VALASOURCES) Makefile
	$(AM_V_VALA)$(VALAC) \
		$(AM_VALAFLAGS) $(libzeitgeist_2_0_la_VALAFLAGS) \
		$(filter %.vala %.c,$^)
	$(AM_V_at)touch $@

pkgconfigdir = $(libdir)/pkgconfig
pkgconfig_DATA = zeitgeist-2.0.pc

libzeitgeist_includedir=$(includedir)/zeitgeist-2.0/
nodist_libzeitgeist_include_HEADERS = \
	zeitgeist.h \
	zeitgeist-datamodel.h \
	$(NULL)

libzeitgeist_vapidir = $(datadir)/vala/vapi/
nodist_libzeitgeist_vapi_DATA = \
	zeitgeist-2.0.vapi \
	zeitgeist-2.0.deps \
	zeitgeist-datamodel-2.0.vapi \
	$(NULL)

EXTRA_DIST = \
	$(libzeitgeist_2_0_la_VALASOURCES) \
	$(libzeitgeist_datamodel_2_0_la_VALASOURCES) \
	$(libzeitgeist_internal_la_VALASOURCES) \
	zeitgeist-2.0.deps \
	ontology.vala.in \
	ontology-uris.vala.in \
	$(NULL)

CLEANFILES = \
	$(nodist_libzeitgeist_2_0_la_SOURCES) \
	$(nodist_libzeitgeist_datamodel_2_0_la_SOURCES) \
	$(nodist_libzeitgeist_internal_la_SOURCES) \
	zeitgeist.h \
	zeitgeist-2.0.vapi \
	Zeitgeist-2.0.gir \
	zeitgeist-datamodel.h \
	zeitgeist-datamodel-2.0.vapi \
	zeitgeist-internal.h \
	zeitgeist-internal.vapi \
	$(NULL)

MAINTAINERCLEANFILES =

# We have to extract our own dlname from libzeitgeist-2.0.la; see bgo#658002.
# This is what g-ir-scanner does.
libzeitgeist_dlname = \
	`$(SED) -n "s/^dlname='\([A-Za-z0-9.+-]\{1,\}\)'/\1/p" libzeitgeist-2.0.la`

if HAVE_INTROSPECTION
libzeitgeist_2_0_gir_VALASOURCES = \
	$(libzeitgeist_2_0_la_VALASOURCES) \
	$(libzeitgeist_datamodel_2_0_la_VALASOURCES) \
	$(NULL)

.gir/Zeitgeist-2.0.gir: $(libzeitgeist_2_0_gir_VALASOURCES) Makefile
	$(AM_V_VALA)$(VALAC) \
		$(AM_VALAFLAGS) \
		-H $(builddir)/.gir/zeitgeist.h \
		--library zeitgeist-2.0 \
		--gir Zeitgeist-2.0.gir \
		--basedir $(builddir)/.gir \
		--directory $(builddir)/.gir \
		$(builddir)/zeitgeist-internal.vapi \
		$(filter %.vala %.c,$^)

Zeitgeist-2.0.gir: $(builddir)/.gir/Zeitgeist-2.0.gir
	$(AM_V_at)cp $(builddir)/.gir/Zeitgeist-2.0.gir $(builddir)

Zeitgeist-2.0.typelib: libzeitgeist-2.0.la
Zeitgeist-2.0.typelib: Zeitgeist-2.0.gir
	${INTROSPECTION_COMPILER} -l ${libzeitgeist_dlname} --includedir ${INTROSPECTION_GIRDIR} -o $@ $^

GIRS = Zeitgeist-2.0.gir

girdir = $(datadir)/gir-1.0
nodist_gir_DATA = $(GIRS)

typelibdir = $(libdir)/girepository-1.0
nodist_typelib_DATA = $(GIRS:.gir=.typelib)

CLEANFILES += \
	$(nodist_gir_DATA) \
	$(nodist_typelib_DATA) \
	$(NULL)
endif

ontology.vala ontology-uris.vala: ontology.vala.in ontology-uris.vala.in \
		$(ONTOLOGY) $(top_srcdir)/data/ontology2code
	$(AM_V_GEN)$(PYTHON) $(top_srcdir)/data/ontology2code --vala $(top_srcdir)/libzeitgeist/ontology-uris.vala.in $(top_srcdir)/libzeitgeist/ontology.vala.in ontology-uris.vala ontology.vala

distclean-local:
	rm -f *.c *.o *.stamp *.~[0-9]~

clean-local:
	rm -rf .gir

VALA_V = $(VALA_V_$(V))
VALA_V_ = $(VALA_V_$(AM_DEFAULT_VERBOSITY))
VALA_V_0 = @echo "  VALAC " $^;
