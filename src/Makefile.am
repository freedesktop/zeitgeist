NULL = 

bin_PROGRAMS = bluebird

AM_CPPFLAGS = \
	$(BLUEBIRD_CFLAGS) \
	-include $(CONFIG_HEADER) \
	$(NULL)

VALAFLAGS = \
	--target-glib=2.26 \
	-D BUILTIN_EXTENSIONS \
	--pkg gio-2.0 \
	--pkg sqlite3 \
	--pkg posix \
	--pkg gmodule-2.0 \
	$(NULL)


extensions_VALASOURCES = \
	ext-data-source-registry.vala \
	$(NULL)

bluebird_VALASOURCES = \
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

bluebird_SOURCES = \
	zeitgeist-engine_vala.stamp \
	$(bluebird_VALASOURCES:.vala=.c) \
	$(extensions_VALASOURCES:.vala=.c) \
	$(NULL)

bluebird_LDADD = \
	$(BLUEBIRD_LIBS) \
	$(NULL)

bluebird_LDFLAGS = -export-dynamic -no-undefined

BUILT_SOURCES = zeitgeist-engine_vala.stamp extensions_vala.stamp

zeitgeist-engine_vala.stamp zeitgeist-engine.vapi: $(bluebird_VALASOURCES)
	$(VALAC) $(VALAFLAGS) -C -H zeitgeist-engine.h --library zeitgeist-engine $^
	touch "$@"

extensions_vala.stamp: zeitgeist-engine.vapi $(extensions_VALASOURCES)
	$(VALAC) $(VALAFLAGS) $(EXT_FLAGS) -C $(filter %.vala %.vapi,$^)
	touch "$@"

# FIXME: can we make this depend on $(ontology_trig_DATA)?
ontology_vala.stamp: ontology.vala.in ontology-uris.vala.in
	$(top_srcdir)/extra/ontology2code --vala
	touch "$@"

ontology.vala ontology-uris.vala: ontology_vala.stamp

EXTRA_DIST = \
	$(bluebird_VALASOURCES) \
	ontology_vala.stamp \
	ontology.vala.in \
	ontology-uris.vala.in \
	zeitgeist-engine.h \
	zeitgeist-engine.vapi \
	zeitgeist-engine_vala.stamp \
	extensions_vala.stamp \
	$(NULL)

DISTCLEANFILES = \
	ontology.vala \
	ontology-uris.vala \
	$(NULL)

distclean-local:
	rm -f *.c *.o *.stamp *.~[0-9]~
