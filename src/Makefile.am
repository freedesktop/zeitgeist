NULL = 

bin_PROGRAMS = bluebird

AM_CPPFLAGS = \
	$(BLUEBIRD_CFLAGS) \
	-include $(CONFIG_HEADER) \
	$(NULL)

VALAFLAGS = \
	--pkg gio-2.0 \
	--target-glib=2.26 \
	--pkg sqlite3 \
	--pkg posix \
	$(NULL)

bluebird_SOURCES = \
	zeitgeist-daemon.vala \
	datamodel.vala \
	engine.vala \
	remote.vala \
	extension.vala \
	notify.vala \
	sql.vala \
	constants.vala \
	errors.vala \
	table-lookup.vala \
	sql-schema.vala \
	where-clause.vala \
	ontology.vala \
	ontology-uris.vala \
	$(NULL)

bluebird_LDADD = \
	$(BLUEBIRD_LIBS) \
	$(NULL)

EXTRA_DIST = \
	$(NULL)

DISTCLEANFILES = \
	$(NULL)

# FIXME: can we make this depend on $(ontology_trig_DATA)?
generate-ontology:
	$(top_srcdir)/extra/ontology2code --vala

ontology.vala: generate-ontology
ontology-uris.vala: generate-ontology

clean:
	rm -f ontology.vala ontology-uris.vala *.c *.o *.stamp *.~[0-9]~
