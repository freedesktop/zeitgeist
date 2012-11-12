VALAFLAGS = \
	--target-glib=2.26 \
	--pkg gio-2.0 \
	--pkg gio-unix-2.0 \
	--pkg sqlite3 \
	--pkg posix \
	--pkg gmodule-2.0 \
	$(srcdir)/assertions.vapi \
	--Xcc=-w \
	-g \
	$(NULL)

TESTS = \
	datamodel-test \
	datasource-test \
	event-test \
	log-test \
	marshalling-test \
	mimetype-test \
	monitor-test \
	query-operators-test \
	symbol-test \
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
	$(top_srcdir)/libzeitgeist/data-source.vala \
	$(top_srcdir)/libzeitgeist/enumerations.vala \
	$(top_srcdir)/libzeitgeist/event.vala \
	$(top_srcdir)/libzeitgeist/subject.vala \
	$(top_srcdir)/libzeitgeist/timerange.vala \
	$(top_srcdir)/libzeitgeist/timestamp.vala \
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
	$(top_srcdir)/libzeitgeist/log.vala \
	$(top_srcdir)/libzeitgeist/result-set.vala \
	$(top_srcdir)/libzeitgeist/simple-result-set.vala \
	$(top_srcdir)/libzeitgeist/monitor.vala \
	$(top_srcdir)/libzeitgeist/queued-proxy-wrapper.vala \
	$(top_srcdir)/libzeitgeist/result-set.vala \
	$(top_srcdir)/libzeitgeist/simple-result-set.vala \
	$(NULL)

datamodel-test: datamodel-test.vala $(SRC_FILES)
	$(VALA_V)$(VALAC) $(VALAFLAGS) -o $@ $^

datasource-test: datasource-test.vala $(SRC_FILES)
	$(VALA_V)$(VALAC) $(VALAFLAGS) -o $@ $^

event-test: event-test.vala $(SRC_FILES)
	$(VALA_V)$(VALAC) $(VALAFLAGS) -o $@ $^

log-test: log-test.vala $(SRC_FILES)
	$(VALA_V)$(VALAC) $(VALAFLAGS) -o $@ $^

marshalling-test: marshalling-test.vala $(SRC_FILES)
	$(VALA_V)$(VALAC) $(VALAFLAGS) -o $@ $^

query-operators-test: query-operators-test.vala $(SRC_FILES)
	$(VALA_V)$(VALAC) $(VALAFLAGS) -o $@ $^

symbol-test: symbol-test.vala $(SRC_FILES)
	$(VALA_V)$(VALAC) $(VALAFLAGS) -o $@ $^

where-clause-test: where-clause-test.vala $(SRC_FILES)
	$(VALA_V)$(VALAC) $(VALAFLAGS) -o $@ $^

table-lookup-test: table-lookup-test.vala $(SRC_FILES)
	$(VALA_V)$(VALAC) $(VALAFLAGS) -o $@ $^

mimetype-test: mimetype-test.vala $(SRC_FILES)
	$(VALA_V)$(VALAC) $(VALAFLAGS) -o $@ $^

monitor-test: monitor-test.vala $(SRC_FILES)
	$(VALA_V)$(VALAC) $(VALAFLAGS) -o $@ $^

clean-local:
	rm -f *.~[0-9]~

CLEANFILES = \
	datamodel-test \
	datasource-test \
	event-test \
	log-test \
	marshalling-test \
	mimetype-test \
	monitor-test \
	query-operators-test \
	symbol-test \
	table-lookup-test \
	where-clause-test \
	$(NULL)

EXTRA_DIST = \
	assertions.vapi \
	datamodel-test.vala \
	datasource-test.vala \
	event-test.vala \
	log-test.vala \
	marshalling-test.vala \
	mimetype-test.vala \
	monitor-test.vala \
	query-operators-test.vala \
	symbol-test.vala \
	table-lookup-test.vala \
	where-clause-test.vala \
	$(NULL)

VALA_V = $(VALA_V_$(V))
VALA_V_ = $(VALA_V_$(AM_DEFAULT_VERBOSITY))
VALA_V_0 = @echo "  VALAC " $@;
