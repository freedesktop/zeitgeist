NULL = 

bin_PROGRAMS = bluebird

AM_CPPFLAGS = \
	$(BLUEBIRD_CFLAGS) \
	-include $(CONFIG_HEADER) \
	-w \
	$(NULL)

VALAFLAGS = \
	--target-glib=2.26 \
	-D BUILTIN_EXTENSIONS \
	--pkg gio-2.0 \
	--pkg sqlite3 \
	--pkg posix \
	--pkg gmodule-2.0 \
	$(NULL)

# Make sure every extension has only one vala file!
extensions_VALASOURCES = \
	ext-data-source-registry.vala \
	ext-blacklist.vala \
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

zeitgeist-engine_vala.stamp: $(bluebird_VALASOURCES)
	$(VALA_V)$(VALAC) $(VALAFLAGS) -C -H zeitgeist-engine.h --library zeitgeist-engine $^
	touch "$@"

extensions_vala.stamp: zeitgeist-engine.vapi $(extensions_VALASOURCES)
	$(foreach ext_src,$(filter %.vala,$^),\
		$(VALAC) $(VALAFLAGS) $(EXT_FLAGS) -C zeitgeist-engine.vapi $(ext_src) || exit 1;)
	touch "$@"

# FIXME: can we make this depend on $(ontology_trig_DATA)?
ontology_vala.stamp: ontology.vala.in ontology-uris.vala.in
	$(top_srcdir)/extra/ontology2code --vala
	touch "$@"

ontology.vala ontology-uris.vala: ontology_vala.stamp

EXTRA_DIST = \
	$(bluebird_VALASOURCES) \
	$(extensions_VALASOURCES) \
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

VALA_V = $(VALA_V_$(V))
VALA_V_ = $(VALA_V_$(AM_DEFAULT_VERBOSITY))
VALA_V_0 = @echo "  VALAC " $^;

