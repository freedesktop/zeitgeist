NULL = 

lib_LTLIBRARIES = libzeitgeist-2.0.la

AM_CPPFLAGS = \
	$(ZEITGEIST_CFLAGS) \
	-include $(CONFIG_HEADER) \
	-w \
	$(NULL)

AM_VALAFLAGS = \
	--target-glib=2.26 \
	--pkg gio-2.0 \
	--pkg sqlite3 \
	$(top_srcdir)/config.vapi \
	--vapi zeitgeist.vapi \
	-H zeitgeist.h \
	--internal-vapi zeitgeist-private.vapi \
	-h zeitgeist-private.h \
	--library=zeitgeist \
	$(NULL)

libzeitgeist_2_0_la_SOURCES = \
	data-source.vala \
	data-source-registry.vala \
	datamodel.vala \
	index.vala \
	log.vala \
	mimetype.vala \
	monitor.vala \
	ontology-uris.vala \
	ontology.vala \
	queued-proxy-wrapper.vala \
	remote.vala \
	result-set.vala \
	simple-result-set.vala \
	utils.vala \
	$(NULL)

libzeitgeist_2_0_la_LDFLAGS = -version-info $(LIBZEITGEIST_LT_VERSION)

pkgconfigdir = $(libdir)/pkgconfig
pkgconfig_DATA = zeitgeist-2.0.pc

libzeitgeist_includedir=$(includedir)/libzeitgeist-2.0/zeitgeist/
libzeitgeist_include_HEADERS = \
	zeitgeist.h \
	$(NULL)

libzeitgeist_vapidir = $(datadir)/vala/vapi/
libzeitgeist_vapi_DATA = \
	zeitgeist.vapi
	$(NULL)

EXTRA_DIST = \
	ontology.vala.in \
	ontology-uris.vala.in \
	$(NULL)

DISTCLEANFILES = \
	ontology.vala \
	ontology-uris.vala \
	zeitgeist.vapi \
	zeitgeist-private.vapi \
	$(NULL)

# FIXME: can we make this depend on $(ontology_trig_DATA)?
ontology_vala.stamp: ontology.vala.in ontology-uris.vala.in
	$(AM_V_GEN)$(top_srcdir)/data/ontology2code --vala
	@touch "$@"

ontology.vala ontology-uris.vala: ontology_vala.stamp

distclean-local:
	rm -f *.c *.o *.stamp *.~[0-9]~
