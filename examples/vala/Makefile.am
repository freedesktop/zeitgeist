NULL =

AM_CPPFLAGS = \
	$(ZEITGEIST_CFLAGS) \
	-include $(CONFIG_HEADER) \
	-I $(top_builddir)/libzeitgeist/ \
	-w \
	$(NULL)

AM_VALAFLAGS = \
	--target-glib=2.36 \
	--pkg gio-2.0 \
	$(top_builddir)/libzeitgeist/zeitgeist-datamodel-2.0.vapi \
	$(top_builddir)/libzeitgeist/zeitgeist-2.0.vapi \
	$(top_srcdir)/config.vapi \
	$(NULL)

AM_LDFLAGS = \
	$(ZEITGEIST_LIBS) \
	$(top_builddir)/libzeitgeist/libzeitgeist-2.0.la \
	$(NULL)

noinst_PROGRAMS = \
	data-source-stuff \
	get-events-with-id \
	monitor-events \
	most-recent-events \
	insert-events \
	$(NULL)

data_source_stuff_SOURCES = data-source-stuff.vala
get_events_with_id_SOURCES = get-events-with-id.vala
monitor_events_SOURCES = monitor-events.vala
most_recent_events_SOURCES = most-recent-events.vala
insert_events_SOURCES = insert-events.vala

distclean-local:
	rm -f *.c *.o *.~[0-9]~
