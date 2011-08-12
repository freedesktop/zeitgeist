AC_INIT([bluebird], [0.1.0], [dev@lists.zeitgeist-project.com], [bluebird])
AC_CONFIG_SRCDIR([Makefile.am])
AC_CONFIG_HEADERS(config.h)
AM_INIT_AUTOMAKE([dist-bzip2])
AM_MAINTAINER_MODE

AC_PROG_CC
AM_PROG_CC_C_O
AC_DISABLE_STATIC
AC_PROG_LIBTOOL

AM_PROG_VALAC([0.12.1])

AH_TEMPLATE([GETTEXT_PACKAGE], [Package name for gettext])
GETTEXT_PACKAGE=bluebird
AC_DEFINE_UNQUOTED(GETTEXT_PACKAGE, "$GETTEXT_PACKAGE")
AC_SUBST(GETTEXT_PACKAGE)
AM_GLIB_GNU_GETTEXT
IT_PROG_INTLTOOL([0.35.0])

AC_SUBST(CFLAGS)
AC_SUBST(CPPFLAGS)
AC_SUBST(LDFLAGS)

GLIB_REQUIRED=2.26.0

BLUEBIRD_REQUIRED="glib-2.0 >= $GLIB_REQUIRED
                   gobject-2.0 >= $GLIB_REQUIRED
                   gio-unix-2.0 >= $GLIB_REQUIRED
                   sqlite3"

PKG_CHECK_MODULES(BLUEBIRD, [$BLUEBIRD_REQUIRED])
AC_SUBST(BLUEBIRD_CFLAGS)
AC_SUBST(BLUEBIRD_LIBS)

AC_CONFIG_FILES([
	Makefile
	src/Makefile
	extra/Makefile
	extra/ontology/Makefile
	test/Makefile
	test/dbus/Makefile
	test/direct/Makefile
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
