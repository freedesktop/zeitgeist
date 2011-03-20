AC_INIT([zeitgeist], [0.7.1])
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

# Expand variables needed for config.py
AS_AC_EXPAND(DATADIR, $datarootdir)
AC_SUBST(DATADIR)

AC_CONFIG_FILES([
	Makefile
	doc/Makefile
	extra/Makefile
	extra/ontology/Makefile
	po/Makefile.in
	zeitgeist-daemon.pc	
	zeitgeist/Makefile
	_zeitgeist/Makefile
	_zeitgeist/engine/Makefile
	_zeitgeist/engine/extensions/Makefile
	_zeitgeist/engine/upgrades/Makefile
])

# check for rapper
AC_CHECK_PROG(HAVE_RAPPER, rapper, yes, no)
if test "x$HAVE_RAPPER" = "xno"; then
  AC_MSG_ERROR(You need the tool `rapper' from the `raptor-utils' package in order to compile Zeitgeist)
fi

# check for python-rdflib
AC_MSG_CHECKING([for python-rdflib])
echo "import rdflib" | python - 2>/dev/null
if test $? -ne 0 ; then
  AC_MSG_FAILURE([failed.  Please install the python-rdflib package.])
else
  AC_MSG_RESULT([yes])
fi

AC_OUTPUT
