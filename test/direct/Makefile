# FIXME: Change this into a proper Makefile.am.

VALAFLAGS = \
	--pkg gio-2.0 \
	--target-glib=2.26 \
	--pkg sqlite3 \
	--pkg posix \
	$(NULL)

all:
	valac $(VALAFLAGS) where-clause-test.vala ../../src/where-clause.vala

run: all
	./where-clause-test
