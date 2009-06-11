AC_INIT([zeitgeist], [0.0.8])
AC_CONFIG_SRCDIR(zeitgeist-daemon)
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
	data/Makefile
	doc/Makefile
	extra/Makefile
	extra/epiphany/Makefile
	po/Makefile.in
	zeitgeist/Makefile
	zeitgeist/shared/Makefile
	zeitgeist/loggers/datasources/Makefile
	zeitgeist/loggers/Makefile
	zeitgeist/engine/Makefile
])
AC_OUTPUT
