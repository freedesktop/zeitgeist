VALAFLAGS = \
	--pkg gio-2.0 \
	--target-glib=2.26 \
	--pkg sqlite3 \
	--pkg posix \
	--pkg gmodule-2.0 \
	$(srcdir)/assertions.vapi \
	--Xcc=-w \
	-g \
	$(NULL)

TESTS = \
	datamodel-test \
	marshalling-test \
	mimetype-test \
	query-operators-test \
	table-lookup-test \
	where-clause-test \
	$(NULL)

SRC_FILES = \
	$(top_srcdir)/src/db-reader.vala \
	$(top_srcdir)/src/engine.vala \
	$(top_srcdir)/libzeitgeist/utils.vala \
	$(top_srcdir)/src/errors.vala \
	$(top_srcdir)/src/extension-store.vala \
	$(top_srcdir)/src/notify.vala \
	$(top_srcdir)/src/table-lookup.vala \
	$(top_srcdir)/libzeitgeist/datamodel.vala  \
	$(top_srcdir)/src/where-clause.vala \
	$(top_srcdir)/libzeitgeist/remote.vala \
	$(top_srcdir)/libzeitgeist/timestamp.vala \
	$(top_srcdir)/src/sql-schema.vala \
	$(top_srcdir)/src/extension.vala \
	$(top_srcdir)/src/extension-collection.vala \
	$(top_srcdir)/src/sql.vala \
	$(top_srcdir)/libzeitgeist/ontology.vala \
	$(top_srcdir)/libzeitgeist/ontology-uris.vala \
	$(top_srcdir)/libzeitgeist/mimetype.vala \
	$(NULL)

datamodel-test: datamodel-test.vala $(SRC_FILES)
	$(VALA_V)$(VALAC) $(VALAFLAGS) -o $@ $^

marshalling-test: marshalling-test.vala $(SRC_FILES)
	$(VALA_V)$(VALAC) $(VALAFLAGS) -o $@ $^

query-operators-test: query-operators-test.vala $(SRC_FILES)
	$(VALA_V)$(VALAC) $(VALAFLAGS) -o $@ $^

where-clause-test: where-clause-test.vala $(SRC_FILES)
	$(VALA_V)$(VALAC) $(VALAFLAGS) -o $@ $^

table-lookup-test: table-lookup-test.vala $(SRC_FILES)
	$(VALA_V)$(VALAC) $(VALAFLAGS) -o $@ $^

mimetype-test: mimetype-test.vala $(SRC_FILES)
	$(VALA_V)$(VALAC) $(VALAFLAGS) -o $@ $^

clean-local:
	rm -f *.~[0-9]~

CLEANFILES = \
	datamodel-test \
	marshalling-test \
	mimetype-test \
	query-operators-test \
	table-lookup-test \
	where-clause-test \
	$(NULL)

EXTRA_DIST = \
	assertions.vapi \
	datamodel-test.vala \
	marshalling-test.vala \
	mimetype-test.vala \
	query-operators-test.vala \
	table-lookup-test.vala \
	where-clause-test.vala \
	$(NULL)

VALA_V = $(VALA_V_$(V))
VALA_V_ = $(VALA_V_$(AM_DEFAULT_VERBOSITY))
VALA_V_0 = @echo "  VALAC " $@;
