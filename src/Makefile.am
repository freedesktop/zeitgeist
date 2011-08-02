NULL = 

bin_PROGRAMS = bluebird

AM_CPPFLAGS = \
	$(BLUEBIRD_CFLAGS) \
	-include $(CONFIG_HEADER) \
	$(NULL)

VALAFLAGS = \
	--pkg gio-2.0 \
	--target-glib=2.26 \
	--pkg sqlite3 \
	--pkg posix \
	$(NULL)

bluebird_SOURCES = \
	zeitgeist-daemon.vala \
	datamodel.vala \
	engine.vala \
	remote.vala \
	extension.vala \
	notify.vala \
	sql.vala \
	constants.vala \
	errors.vala \
	table-lookup.vala \
	sql-schema.vala \
	where-clause.vala \
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
