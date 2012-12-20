include $(top_srcdir)/libzeitgeist/Makefile.decl

INCLUDES = \
  -I$(top_srcdir)/libzeitgeist -I$(top_builddir)/libzeitgeist \
  $(GIO_UNIX_CFLAGS) \
  $(ZEITGEIST_CFLAGS)

AM_CFLAGS = \
  -Wall  \
  -g \
  -DZEITGEIST_COMPILATION \
  -DTEST_DIR=\"$(top_srcdir)/tests\"

zeitgeist_libs = $(top_builddir)/libzeitgeist/libzeitgeist-2.0.la $(ZEITGEIST_LIBS)

EXTRA_DIST += \
  test.desktop

helper_sources = \
  $(top_srcdir)/libzeitgeist/zeitgeist.h  \
  test.desktop

noinst_PROGRAMS = \
  find-events \
  monitor-events \
  search-events \
  get-events

find_events_SOURCES = find-events.c
find_events_LDADD   = $(zeitgeist_libs)

monitor_events_SOURCES = monitor-events.c
monitor_events_LDADD   = $(zeitgeist_libs)

search_events_SOURCES = search-events.c
search_events_LDADD   = $(zeitgeist_libs)

get_events_SOURCES = get-events.c
get_events_LDADD   = $(zeitgeist_libs)
