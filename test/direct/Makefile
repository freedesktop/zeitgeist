# FIXME: Change this into a proper Makefile.am.

VALAFLAGS = \
	--pkg gio-2.0 \
	--target-glib=2.26 \
	--pkg sqlite3 \
	--pkg posix \
	$(NULL)

SRC_FILES = \
	../../src/engine.vala \
	../../src/constants.vala \
	../../src/notify.vala \
	../../src/table-lookup.vala \
	../../src/datamodel.vala  \
	../../src/ontology.vala \
	../../src/where-clause.vala \
	../../src/remote.vala \
	../../src/errors.vala \
	../../src/sql-schema.vala \
	../../src/extension.vala \
	../../src/sql.vala \
	$(NULL)

all:
	#valac $(VALAFLAGS) where-clause-test.vala $(SRC_FILES)
	valac $(VALAFLAGS) query-operators-test.vala $(SRC_FILES)

run: all
	#./where-clause-test
	./query-operators-test
