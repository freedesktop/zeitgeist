NULL = 


lib_LTLIBRARIES = libzeitgeist.la

AM_CPPFLAGS = \
	$(ZEITGEIST_CFLAGS) \
	-include $(CONFIG_HEADER) \
	-w \
	$(NULL)

AM_VALAFLAGS = \
	--target-glib=2.26 \
	-D BUILTIN_EXTENSIONS \
	$(top_srcdir)/config.vapi \
	$(NULL)

libzeitgeist_la_SOURCES = \
	log.vala \
	datamodel.vala \
	ontology.vala \
	ontology-uris.vala \
	$(NULL)

EXTRA_DIST = \
	ontology.vala.in \
	ontology-uris.vala.in \
	$(NULL)

DISTCLEANFILES = \
	ontology.vala \
	ontology-uris.vala \
	$(NULL)

ontology.vala ontology-uris.vala: ontology_vala.stamp

ontology_vala.stamp: ontology.vala.in ontology-uris.vala.in
	$(AM_V_GEN)$(top_srcdir)/data/ontology2code --vala
