NULL = 

#Build in these directories:

SUBDIRS = \
	src \
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

EXTRA_DIST = \
	$(bluebirddoc_DATA) \
	intltool-extract.in \
	intltool-merge.in \
	intltool-update.in \
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
