SUBDIRS = extra po zeitgeist _zeitgeist doc

INTLTOOL = \
	intltool-extract.in \
	intltool-merge.in \
	intltool-update.in

bin_SCRIPTS = \
	zeitgeist-daemon \
	zeitgeist-datahub

EXTRA_DIST = \
	$(bin_SCRIPTS) \
	$(INTLTOOL) \
	COPYING.GPL \
	COPYRIGHT \
	zeitgeist-daemon.py \
	zeitgeist-datahub.py

DISTCLEANFILES = \
	intltool-extract \
	intltool-merge \
	intltool-update

CLEANFILES = \
	zeitgeist-daemon \
	zeitgeist-datahub

zeitgeist-daemon: zeitgeist-daemon.py
	sed \
		-e "s!\/usr\/bin\/env python!$(PYTHON)!" \
		-e "s!zeitgeist-datahub\.py!zeitgeist-datahub!" \
		< $< > $@
	chmod +x zeitgeist-daemon
zeitgeist-daemon.py: Makefile

zeitgeist-datahub: zeitgeist-datahub.py
	sed \
		-e "s!\/usr\/bin\/env python!$(PYTHON)!" \
		< $< > $@
	chmod +x zeitgeist-datahub
zeitgeist-datahub.py: Makefile

all-local: zeitgeist-daemon zeitgeist-datahub.py
