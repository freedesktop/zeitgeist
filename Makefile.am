NULL = 

SUBDIRS = \
	src \
	extensions \
	extra \
	test \
	po \
	$(NULL)

bluebirddocdir = ${prefix}/doc/bluebird
bluebirddoc_DATA = \
	ChangeLog \
	README \
	COPYING \
	AUTHORS \
	INSTALL \
	NEWS \
	$(NULL)

DISTCHECK_CONFIGURE_FLAGS = --with-session-bus-services-dir="\$(datadir)"/dbus-1/services

EXTRA_DIST = \
	$(bluebirddoc_DATA) \
	intltool-extract.in \
	intltool-merge.in \
	intltool-update.in \
	config.vapi \
	$(NULL)

DISTCLEANFILES = \
	intltool-extract \
	intltool-merge \
	intltool-update \
	po/.intltool-merge-cache \
	$(NULL)

run: all
	./src/bluebird

debug: all
	gdb ./src/bluebird

test: all
	./test/dbus/run-all-tests.py

test-direct: all
	cd ./test/direct/ && make run;
