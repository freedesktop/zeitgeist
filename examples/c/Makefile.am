NULL =

AM_CFLAGS = \
	-Wall  \
	-g \
	$(GIO_UNIX_CFLAGS) \
	$(ZEITGEIST_CFLAGS) \
	-I $(top_builddir)/libzeitgeist \
	-include $(top_builddir)/libzeitgeist/zeitgeist-datamodel.h \
	-include $(top_builddir)/libzeitgeist/zeitgeist.h \
	$(NULL)

AM_LDFLAGS = \
	$(ZEITGEIST_LIBS) \
	$(top_builddir)/libzeitgeist/libzeitgeist-2.0.la \
	$(NULL)

noinst_PROGRAMS = \
	find-events \
	monitor-events \
	search-events \
	$(NULL)

find_events_SOURCES = find-events.c
monitor_events_SOURCES = monitor-events.c
search_events_SOURCES = search-events.c
