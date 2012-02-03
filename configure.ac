AC_INIT([zeitgeist], [0.8.99~alpha2], [dev@lists.zeitgeist-project.com], [zeitgeist])
AC_CONFIG_SRCDIR([Makefile.am])
AC_CONFIG_HEADERS(config.h)
AM_INIT_AUTOMAKE([dist-bzip2 no-dist-gzip])
AM_MAINTAINER_MODE([enable])

AM_PATH_PYTHON

AC_PROG_CC
AM_PROG_CC_C_O
AC_PROG_CXX
AC_DISABLE_STATIC
AC_PROG_LIBTOOL

AM_PROG_VALAC([0.14.0])

AM_SILENT_RULES([yes])

AH_TEMPLATE([GETTEXT_PACKAGE], [Package name for gettext])
GETTEXT_PACKAGE=zeitgeist
AC_DEFINE_UNQUOTED(GETTEXT_PACKAGE, "$GETTEXT_PACKAGE")
AC_SUBST(GETTEXT_PACKAGE)
AM_GLIB_GNU_GETTEXT
IT_PROG_INTLTOOL([0.35.0])

AC_SUBST(CFLAGS)
AC_SUBST(CPPFLAGS)
AC_SUBST(LDFLAGS)

GLIB_REQUIRED=2.26.0
SQLITE_REQUIRED=3.7

ZEITGEIST_REQUIRED="glib-2.0 >= $GLIB_REQUIRED
                    gobject-2.0 >= $GLIB_REQUIRED
                    gio-unix-2.0 >= $GLIB_REQUIRED
                    sqlite3 >= $SQLITE_REQUIRED"

PKG_CHECK_MODULES(ZEITGEIST, [$ZEITGEIST_REQUIRED])
AC_SUBST(ZEITGEIST_CFLAGS)
AC_SUBST(ZEITGEIST_LIBS)

#################################################
# DBus service
#################################################

AC_ARG_WITH([session_bus_services_dir],
            AC_HELP_STRING([--with-session-bus-services-dir], [Path to DBus services directory]))

if test "x$with_session_bus_services_dir" = "x" ; then
	PKG_CHECK_MODULES(DBUS_MODULE, "dbus-1")
	services_dir="`$PKG_CONFIG --variable session_bus_services_dir dbus-1`"
else
	services_dir="$with_session_bus_services_dir"
fi

DBUS_SERVICES_DIR="$services_dir"
AC_SUBST(DBUS_SERVICES_DIR)

AC_CONFIG_FILES([
	Makefile
	src/Makefile
	extensions/Makefile
	extensions/fts-python/Makefile
	extensions/fts++/Makefile
	data/Makefile
	data/ontology/Makefile
	python/Makefile
	test/Makefile
	test/dbus/Makefile
	test/direct/Makefile
	doc/Makefile
	po/Makefile.in
])

# check for rapper
AC_CHECK_PROG(HAVE_RAPPER, rapper, yes, no)
if test "x$HAVE_RAPPER" = "xno"; then
  AC_MSG_ERROR("You need the tool `rapper' from the `raptor-utils' package in order to compile Zeitgeist")
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
