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
	--pkg gmodule-2.0 \
	$(NULL)

bluebird_SOURCES = \
	zeitgeist-daemon.vala \
	datamodel.vala \
	engine.vala \
	remote.vala \
	extension.vala \
	extension-collection.vala \
	notify.vala \
	sql.vala \
	utils.vala \
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
ontology.vala.stamp: ontology.vala.in ontology-uris.vala.in
	$(top_srcdir)/extra/ontology2code --vala
	touch "$@"

ontology.vala ontology-uris.vala: ontology.vala.stamp

clean:
	rm -f ontology.vala ontology-uris.vala *.c *.o *.stamp *.~[0-9]~
