SUBDIRS = data extra po zeitgeist

INTLTOOL = 			\
	intltool-extract.in 	\
	intltool-merge.in 	\
	intltool-update.in

bin_SCRIPTS =  \
	zeitgeist-daemon \
	zeitgeist-datahub \
	zeitgeist-journal \
	zeitgeist-trayicon

EXTRA_DIST = \
	doc/gzg-userdocs.txt \
	doc/images/main_window_thumb.png \
	doc/images/main_window.png \
	$(bin_SCRIPTS) \
	$(INTLTOOL)

DISTCLEANFILES = 		\
	intltool-extract 	\
	intltool-merge 		\
	intltool-update

