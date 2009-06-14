SUBDIRS = engine loggers

appdir = $(pythondir)/zeitgeist/

app_PYTHON = \
	__init__.py		\
	datamodel.py	\
	dbusutils.py

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
