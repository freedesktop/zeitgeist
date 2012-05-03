NULL = 

lib_LTLIBRARIES = libzeitgeist.la

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
	$(NULL)

libzeitgeist_la_SOURCES = \
	log.vala \
	datamodel.vala \
	ontology.vala \
	ontology-uris.vala \
	utils.vala \
	$(NULL)

EXTRA_DIST = \
	ontology.vala.in \
	ontology-uris.vala.in \
	$(NULL)

DISTCLEANFILES = \
	ontology.vala \
	ontology-uris.vala \
	$(NULL)

# FIXME: can we make this depend on $(ontology_trig_DATA)?
ontology_vala.stamp: ontology.vala.in ontology-uris.vala.in
	$(AM_V_GEN)$(top_srcdir)/data/ontology2code --vala
	@touch "$@"

ontology.vala ontology-uris.vala: ontology_vala.stamp

distclean-local:
	rm -f *.c *.o *.stamp *.~[0-9]~
