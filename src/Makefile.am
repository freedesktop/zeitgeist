NULL = 

bin_PROGRAMS = bluebird

AM_CPPFLAGS = \
	$(BLUEBIRD_CFLAGS) \
	-include $(CONFIG_HEADER) \
	$(NULL)

VALAFLAGS = \
	--pkg gio-2.0 \
	$(NULL)

bluebird_SOURCES = \
	zeitgeist-daemon.vala \
	datamodel.vala \
	engine.vala \
	extension.vala \
	notify.vala \
	sql.vala \
	$(NULL)

bluebird_LDADD = \
	$(BLUEBIRD_LIBS) \
	$(NULL)

EXTRA_DIST = \
	$(NULL)

DISTCLEANFILES = \
	$(NULL)

clean:
	rm -f *.c *.o *.stamp *.~[0-9]~
