SUBDIRS = data extra po zeitgeist doc

INTLTOOL = \
	intltool-extract.in \
	intltool-merge.in \
	intltool-update.in

bin_SCRIPTS = \
	zeitgeist-daemon \
	zeitgeist-datahub

EXTRA_DIST = \
	$(bin_SCRIPTS) \
	$(INTLTOOL)

DISTCLEANFILES = \
	intltool-extract \
	intltool-merge \
	intltool-update
