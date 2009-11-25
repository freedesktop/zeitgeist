appdir = $(pythondir)/zeitgeist/

app_PYTHON = \
	__init__.py \
	datamodel.py \
	client.py

nodist_app_PYTHON = _config.py

_config.py: _config.py.in
	sed						\
		-e s!\@prefix\@!$(prefix)!		\
		-e s!\@datadir\@!$(datadir)!		\
		-e s!\@pkgdatadir\@!$(pkgdatadir)!	\
		-e s!\@libexecdir\@!$(libexecdir)!	\
		-e s!\@libdir\@!$(libdir)!		\
		-e s!\@PACKAGE\@!$(PACKAGE)!		\
		-e s!\@VERSION\@!$(VERSION)!		\
		< $< > $@
_config.py: Makefile

CLEANFILES = _config.py
EXTRA_DIST = _config.py.in

all-local: _config.py
