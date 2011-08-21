VALAFLAGS = \
	--pkg gio-2.0 \
	--target-glib=2.26 \
	--pkg sqlite3 \
	--pkg posix \
	--pkg gmodule-2.0 \
	$(srcdir)/assertions.vapi \
	--Xcc=-w \
	$(NULL)

TESTS = \
	marshalling \
	query-operators-test \
	where-clause-test \
	$(NULL)

SRC_FILES = \
	$(top_srcdir)/src/engine.vala \
	$(top_srcdir)/src/utils.vala \
	$(top_srcdir)/src/notify.vala \
	$(top_srcdir)/src/table-lookup.vala \
	$(top_srcdir)/src/datamodel.vala  \
	$(top_srcdir)/src/where-clause.vala \
	$(top_srcdir)/src/remote.vala \
	$(top_srcdir)/src/errors.vala \
	$(top_srcdir)/src/sql-schema.vala \
	$(top_srcdir)/src/extension.vala \
	$(top_srcdir)/src/sql.vala \
	$(top_srcdir)/src/ontology.vala \
	$(top_srcdir)/src/ontology-uris.vala \
	$(NULL)

marshalling: marshalling.vala $(top_srcdir)/src/datamodel.vala
	$(VALAC) $(VALAFLAGS) -o $@ $^

query-operators-test: query-operators-test.vala $(SRC_FILES)
	$(VALAC) $(VALAFLAGS) -o $@ $^

where-clause-test: where-clause-test.vala $(SRC_FILES)
	$(VALAC) $(VALAFLAGS) -o $@ $^

clean-local:
	rm -f *.~[0-9]~

EXTRA_DIST = \
	marshalling.vala \
	query-operators-test.vala \
	where-clause-test.vala \
	assertions.vapi \
	$(NULL)

