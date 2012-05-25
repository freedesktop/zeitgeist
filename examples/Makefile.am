NULL =

AM_CPPFLAGS = \
	$(ZEITGEIST_CFLAGS) \
	-include $(CONFIG_HEADER) \
	-I $(top_srcdir)/libzeitgeist/ \
	-w \
	$(NULL)

AM_VALAFLAGS = \
	--target-glib=2.26 \
	--pkg gio-2.0 \
	$(top_srcdir)/libzeitgeist/zeitgeist.vapi \
	$(top_srcdir)/config.vapi \
	$(NULL)

zeitgeist_libs = \
	$(top_builddir)/libzeitgeist/libzeitgeist-2.0.la \
	$(ZEITGEIST_LIBS)

noinst_PROGRAMS = \
	get-events-with-id \
	monitor-events \
	most-recent-events \
	$(NULL)

get_events_with_id_SOURCES	= get-events-with-id.vala
get_events_with_id_LDADD	= $(zeitgeist_libs)

monitor_events_SOURCES		= monitor-events.vala
monitor_events_LDADD		= $(zeitgeist_libs)

most_recent_events_SOURCES	= most-recent-events.vala
most_recent_events_LDADD	= $(zeitgeist_libs)

distclean-local:
	rm -f *.c *.o *.~[0-9]~
