SUBDIRS = extra po zeitgeist doc

INTLTOOL = \
	intltool-extract.in \
	intltool-merge.in \
	intltool-update.in

bin_SCRIPTS = \
	zeitgeist-daemon \
	zeitgeist-datahub \
	COPYING.GPL

EXTRA_DIST = \
	$(bin_SCRIPTS) \
	$(INTLTOOL)

DISTCLEANFILES = \
	intltool-extract \
	intltool-merge \
	intltool-update
