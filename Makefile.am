SUBDIRS = data extra po zeitgeist

INTLTOOL = \
	intltool-extract.in \
	intltool-merge.in \
	intltool-update.in

bin_SCRIPTS = \
	zeitgeist-daemon \
	zeitgeist-datahub \
	zeitgeist-journal \
	zeitgeist-trayicon

man_MANS = \
	doc/zeitgeist-daemon.1 \
	doc/zeitgeist-datahub.1 \
	doc/zeitgeist-journal.1 \
	doc/zeitgeist-trayicon.1

EXTRA_DIST = \
	doc/gzg-userdocs.txt \
	doc/images/main_window_thumb.png \
	doc/images/main_window.png \
	$(bin_SCRIPTS) \
	$(man_MANS) \
	$(INTLTOOL)

DISTCLEANFILES = \
	intltool-extrac \
	intltool-merge \
	intltool-update
