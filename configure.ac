AC_INIT([zeitgeist], [0.3.3.1])
AC_CONFIG_SRCDIR(zeitgeist-daemon.py)
AM_INIT_AUTOMAKE([1.9 foreign])
GNOME_COMMON_INIT
AM_MAINTAINER_MODE

AM_PATH_PYTHON

# i18n
GETTEXT_PACKAGE="zeitgeist"
AC_SUBST([GETTEXT_PACKAGE])
AC_DEFINE_UNQUOTED([GETTEXT_PACKAGE], "$GETTEXT_PACKAGE", [Gettext package])
AM_GLIB_GNU_GETTEXT
IT_PROG_INTLTOOL([0.35.0])

AC_CONFIG_FILES([
	Makefile
	doc/Makefile
	extra/Makefile
	extra/ontology/Makefile
	po/Makefile.in
	zeitgeist/Makefile
	_zeitgeist/Makefile
	_zeitgeist/loggers/Makefile
	_zeitgeist/loggers/datasources/Makefile
	_zeitgeist/engine/Makefile
	_zeitgeist/engine/extensions/Makefile
	_zeitgeist/engine/upgrades/Makefile
])
AC_OUTPUT
