NULL =

EXTRA_DIST = \
	test.desktop

AM_CFLAGS = \
	-Wall  \
	-g \
	-DTEST_DIR=\"$(abs_srcdir)\" \
	$(GIO_UNIX_CFLAGS) \
	$(ZEITGEIST_CFLAGS) \
	-I $(top_builddir)/libzeitgeist \
	-include $(top_builddir)/libzeitgeist/zeitgeist-datamodel.h \
	-include $(top_builddir)/libzeitgeist/zeitgeist.h \
	$(NULL)

AM_LDFLAGS = \
	$(top_builddir)/libzeitgeist/libzeitgeist-datamodel-2.0.la \
	$(top_builddir)/libzeitgeist/libzeitgeist-2.0.la \
	$(GIO_UNIX_LIBS) \
	$(ZEITGEIST_LIBS) \
	$(NULL)

check_PROGRAMS = \
	test-timerange \
	test-timestamp \
	test-symbols \
	test-monitor \
	test-log \
	test-event \
	test-datasource \
	test-mimetypes \
	$(NULL)

TESTS = $(check_PROGRAMS)

test_timerange_SOURCES = test-timerange.c
test_timestamp_SOURCES = test-timestamp.c
test_symbols_SOURCES = test-symbols.c
test_monitor_SOURCES = test-monitor.c
test_log_SOURCES = test-log.c
test_event_SOURCES = test-event.c
test_datasource_SOURCES = test-datasource.c
test_mimetypes_SOURCES = test-mimetypes.c

# HEADLESS CHECKS
# Start up a new Zeitgeist on a private bus using only a
# memory backed log database. We also need a fake X server
# because dbus-launch requires an X server...
check-headless:
	export ZEITGEIST_DATABASE_PATH=":memory:"; \
	export DISPLAY=":1"; \
	Xvfb :1 -screen 0 1024x768x8 & \
	dbus-launch > _sessionbus.sh; \
	source _sessionbus.sh; \
	cat _sessionbus.sh; \
	zeitgeist-daemon --quit; \
	zeitgeist-daemon --no-datahub & \
	make check; \
	zeitgeist-daemon --quit; \
	kill `grep DBUS_SESSION_BUS_PID _sessionbus.sh | grep -oE '[0-9]+'`; \
	pkill Xvfb; \
	rm _sessionbus.sh
