NULL = 

AM_CPPFLAGS = \
	$(BLUEBIRD_CFLAGS) \
	-include $(CONFIG_HEADER) \
	$(NULL)

bin_PROGRAMS = bluebird

bluebird_SOURCES = \
	zeitgeist-daemon.vala \
	datamodel.vala \
	engine.vala \
	extension.vala \
	notify.vala \
	remote.vala \
	sql.vala \
	$(NULL)

bluebird_LDADD = \
	$(BLUEBIRD_LIBS) \
	$(NULL)

EXTRA_DIST = \
	$(NULL)

DISTCLEANFILES = \
	$(NULL)

