SUBDIRS = data extra po zeitgeist

INTLTOOL = 			\
	intltool-extract.in 	\
	intltool-merge.in 	\
	intltool-update.in

bin_SCRIPTS =  \
	zeitgeist-daemon.py \
	zeitgeist-datahub.py \
	zeitgeist-journal.py \
	zeitgeist-trayicon.py

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

