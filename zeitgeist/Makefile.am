SUBDIRS = \
	zeitgeist_engine \
	zeitgeist_experimental \
	zeitgeist_gui \
	zeitgeist_loggers \
	zeitgeist_shared

bin_SCRIPTS = zeitgeist-daemon.py

appdir = $(pythondir)/zeitgeist/

app_PYTHON = \
	__init__.py

nodist_app_PYTHON = config.py

config.py: config.py.in
	sed						\
		-e s!\@prefix\@!$(prefix)!		\
		-e s!\@datadir\@!$(datadir)!		\
		-e s!\@pkgdatadir\@!$(pkgdatadir)!	\
		-e s!\@libexecdir\@!$(libexecdir)!	\
		-e s!\@libdir\@!$(libdir)!		\
		-e s!\@PACKAGE\@!$(PACKAGE)!		\
		-e s!\@VERSION\@!$(VERSION)!		\
		< $< > $@
config.py: Makefile

CLEANFILES = config.py
EXTRA_DIST = config.py.in

all-local: config.py

