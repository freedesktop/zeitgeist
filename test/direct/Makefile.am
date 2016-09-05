NULL =

EXTRA_DIST = \
	assertions.vapi \
	test.desktop \
	tests.h \
	tests.vapi \
	$(NULL)

AM_VALAFLAGS = \
	--target-glib=2.36 \
	--pkg gio-2.0 \
	--pkg gio-unix-2.0 \
	--pkg sqlite3 \
	--pkg posix \
	--pkg gmodule-2.0 \
	$(srcdir)/assertions.vapi \
	$(srcdir)/tests.vapi \
	$(top_builddir)/libzeitgeist/zeitgeist-datamodel-2.0.vapi \
	$(top_builddir)/libzeitgeist/zeitgeist-2.0.vapi \
	$(top_builddir)/libzeitgeist/zeitgeist-internal.vapi \
	$(top_builddir)/src/zeitgeist-engine.vapi \
	-g \
	$(NULL)

AM_CPPFLAGS = \
	-Wall  \
	-g \
	-DTEST_DIR=\"$(abs_srcdir)\" \
	$(ZEITGEIST_CFLAGS) \
	-include $(CONFIG_HEADER) \
	-I $(srcdir) \
	-I $(top_builddir)/libzeitgeist \
	-I $(top_builddir)/src \
	-w \
	$(NULL)

AM_LDFLAGS = \
	-export-dynamic -no-undefined \
	$(top_builddir)/libzeitgeist/libzeitgeist-datamodel-2.0.la \
	$(top_builddir)/libzeitgeist/libzeitgeist-2.0.la \
	$(top_builddir)/libzeitgeist/libzeitgeist-internal.la \
	$(top_builddir)/src/libzeitgeist-engine.la \
	$(NULL)

check_PROGRAMS = \
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

TESTS = $(check_PROGRAMS)

datamodel_test_SOURCES = datamodel-test.vala
datasource_test_SOURCES = datasource-test.vala
event_test_SOURCES = event-test.vala
log_test_SOURCES = log-test.vala
marshalling_test_SOURCES = marshalling-test.vala
query_operators_test_SOURCES = query-operators-test.vala
symbol_test_SOURCES = symbol-test.vala
where_clause_test_SOURCES = where-clause-test.vala
table_lookup_test_SOURCES = table-lookup-test.vala
mimetype_test_SOURCES = mimetype-test.vala
monitor_test_SOURCES = monitor-test.vala

clean-local:
	rm -f *.~[0-9]~

VALA_V = $(VALA_V_$(V))
VALA_V_ = $(VALA_V_$(AM_DEFAULT_VERBOSITY))
VALA_V_0 = @echo "  VALAC " $@;
