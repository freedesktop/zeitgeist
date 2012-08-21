include $(top_srcdir)/Makefile.decl

INCLUDES = \
  -I$(top_srcdir)/src -I$(top_builddir)/src \
  $(GIO_UNIX_CFLAGS) \
  $(SQLITE_CFLAGS) \
  $(ZEITGEIST_CFLAGS)

AM_CFLAGS = \
  -Wall  \
  -g \
  -DZEITGEIST_COMPILATION \
  -DTEST_DIR=\"$(top_srcdir)/tests\"

zeitgeist_libs = $(top_builddir)/src/libzeitgeist-2.0.la $(ZEITGEIST_LIBS)

EXTRA_DIST += \
  test.desktop

SRC_FILES = \
  $(top_srcdir)/src/mimetype.c \
  $(top_srcdir)/src/mimetype.h  \
  test.desktop

noinst_PROGRAMS = $(TEST_PROGS)

test-monitor: test-monitor.c $(SRC_FILES)
	$(CC) $(CFLAGS) -o $@ $^

TESTS = \
	test-monitor \
	$(NULL)


clean-local:
	rm -f *.~[0-9]~

CLEANFILES = \
	datamodel-test \
	datasource-test \
	event-test \
	log-test \
	marshalling-test \
	mimetype-test \
	query-operators-test \
	table-lookup-test \
	where-clause-test \
	$(NULL)


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
