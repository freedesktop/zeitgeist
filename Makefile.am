NULL = 

SUBDIRS = \
	libzeitgeist \
	src \
	libzeitgeist/client \
	extensions \
	data \
	python \
	test \
	examples \
	po \
	doc \
	$(NULL)

zeitgeistdocdir = ${prefix}/doc/zeitgeist
zeitgeistdoc_DATA = \
	AUTHORS \
	NEWS \
	$(NULL)

DISTCHECK_CONFIGURE_FLAGS = \
	--with-session-bus-services-dir="\$(datadir)"/dbus-1/services \
	--enable-gtk-doc

EXTRA_DIST = \
	$(zeitgeistdoc_DATA) \
	INSTALL \
	COPYING \
	COPYING.GPL \
	ChangeLog \
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
	./src/zeitgeist-daemon

debug: all
	gdb ./src/zeitgeist-daemon

test-dbus: all
	./test/dbus/run-all-tests.py

test-direct: all
	cd ./test/direct/ && make run;

test-c: all
	cd ./test/c/ && make run;
