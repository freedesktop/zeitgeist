NULL =

ACLOCAL_AMFLAGS = --install -I m4 ${ACLOCAL_FLAGS}

SUBDIRS = \
	libzeitgeist \
	src \
	extensions \
	data \
	python \
	test \
	examples \
	po \
	doc \
	$(NULL)

if ENABLE_DATAHUB
SUBDIRS += datahub
endif

zeitgeistdocdir = $(pkgdatadir)/doc
zeitgeistdoc_DATA = \
	AUTHORS \
	NEWS \
	README.md \
	$(NULL)

DISTCHECK_CONFIGURE_FLAGS = \
	--enable-datahub \
	--enable-fts \
	--enable-docs \
	$(NULL)

EXTRA_DIST = \
	tools \
	$(zeitgeistdoc_DATA) \
	INSTALL \
	COPYING \
	COPYING.GPL \
	ChangeLog \
	config.vapi \
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
