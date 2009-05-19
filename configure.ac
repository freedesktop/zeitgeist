AC_INIT([gnome-zeitgeist], [0.0.6])
AC_CONFIG_SRCDIR(src/zeitgeist-daemon.py)
AM_INIT_AUTOMAKE([1.9 foreign])
GNOME_COMMON_INIT
AM_MAINTAINER_MODE

AM_PATH_PYTHON

# i18n
GETTEXT_PACKAGE="gnome-zeitgeist"
AC_SUBST([GETTEXT_PACKAGE])
AC_DEFINE_UNQUOTED([GETTEXT_PACKAGE], "$GETTEXT_PACKAGE", [Gettext package])
AM_GLIB_GNU_GETTEXT
IT_PROG_INTLTOOL([0.35.0])

AC_CONFIG_FILES([
	Makefile
	data/Makefile
	data/logo/Makefile
	data/logo/22x22/apps/Makefile
	data/logo/22x22/Makefile
	data/logo/24x24/apps/Makefile
	data/logo/24x24/Makefile
	data/logo/32x32/apps/Makefile
	data/logo/32x32/Makefile
	data/logo/scalable/apps/Makefile
	data/logo/scalable/Makefile
	extra/Makefile
	po/Makefile.in
	src/Makefile
	src/zeitgeist_shared/Makefile
	src/zeitgeist_loggers/datasources/Makefile
	src/zeitgeist_loggers/Makefile
	src/zeitgeist_gui/Makefile
	src/zeitgeist_experimental/Makefile
	src/zeitgeist_engine/Makefile
])
AC_OUTPUT
