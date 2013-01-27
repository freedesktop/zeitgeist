include $(top_srcdir)/libzeitgeist/Makefile.decl

INCLUDES = \
  -I$(top_srcdir)/libzeitgeist -I$(top_builddir)/libzeitgeist \
  -I$(top_srcdir)/libzeitgeist/utils -I$(top_builddir)/libzeitgeist/utils \
  $(GIO_UNIX_CFLAGS) \
  $(ZEITGEIST_CFLAGS)

AM_CFLAGS = \
  -Wall  \
  -g \
  -DZEITGEIST_COMPILATION \
  -DTEST_DIR=\"$(top_srcdir)/tests\"

zeitgeist_libs = \
    $(top_builddir)/libzeitgeist/libzeitgeist-2.0.la \
    $(top_builddir)/libzeitgeist/utils/libzeitgeist-utils.la \
    $(ZEITGEIST_LIBS)

EXTRA_DIST += \
  test.desktop

helper_sources = \
  $(top_srcdir)/libzeitgeist/utils/zeitgeist-utils.h  \
  $(top_srcdir)/libzeitgeist/zeitgeist.h  \
  test.desktop

noinst_PROGRAMS = $(TEST_PROGS)

TEST_PROGS            += test-timerange
test_timerange_SOURCES = test-timerange.c $(helper_sources)
test_timerange_LDADD   = $(zeitgeist_libs)

TEST_PROGS            += test-timestamp
test_timestamp_SOURCES = test-timestamp.c $(helper_sources)
test_timestamp_LDADD   = $(zeitgeist_libs)

TEST_PROGS            += test-symbols
test_symbols_SOURCES = test-symbols.c $(helper_sources)
test_symbols_LDADD   = $(zeitgeist_libs)

TEST_PROGS          += test-monitor
test_monitor_SOURCES = test-monitor.c $(helper_sources)
test_monitor_LDADD   = $(zeitgeist_libs)

TEST_PROGS      += test-log
test_log_SOURCES = test-log.c $(helper_sources)
test_log_LDADD   = $(zeitgeist_libs)

TEST_PROGS        += test-event
test_event_SOURCES = test-event.c $(helper_sources)
test_event_LDADD   = $(zeitgeist_libs) $(GIO_UNIX_LIBS)

TEST_PROGS        += test-datasource
test_datasource_SOURCES = test-datasource.c $(helper_sources)
test_datasource_LDADD   = $(zeitgeist_libs) $(GIO_UNIX_LIBS)

TEST_PROGS            += test-mimetypes
test_mimetypes_SOURCES = test-mimetypes.c $(helper_sources)
test_mimetypes_LDADD   = $(zeitgeist_libs)

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
