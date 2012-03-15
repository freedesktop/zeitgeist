AC_INIT([zeitgeist], [0.8.99~alpha3], [dev@lists.zeitgeist-project.com], [zeitgeist])
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
# Dee-ICU check
#################################################
DEE_ICU_REQUIRED=1.0.2

AC_ARG_WITH([dee-icu],
	AS_HELP_STRING([--with-dee-icu[=@<:@no/auto/yes@:>@]],
		[Build the FTS extension with dee-icu]),
	[with_dee_icu=$withval],
	[with_dee_icu="auto"])

if test "x$with_dee_icu" = "xauto" ; then
	PKG_CHECK_EXISTS([dee-icu-1.0 >= $DEE_ICU_REQUIRED],
		with_dee_icu="yes",
		with_dee_icu="no")
fi

if test "x$with_dee_icu" = "xyes" ; then
	PKG_CHECK_MODULES(DEE_ICU, dee-icu-1.0 >= $DEE_ICU_REQUIRED)
	AC_DEFINE(HAVE_DEE_ICU, 1, [Have dee-icu])
fi

AM_CONDITIONAL(HAVE_DEE_ICU, test "x$with_dee_icu" = "xyes")

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

# Configure options: --enable-fts[=no].
AC_ARG_ENABLE([fts],
            [AS_HELP_STRING([--enable-fts],
                [Build with FTS++ extension])],
            [fts="$withval"], [fts=no])
AM_CONDITIONAL(HAVE_FTS, test "x$fts" = "xyes")

AC_CONFIG_FILES([
	Makefile
	src/Makefile
	extensions/Makefile
	extensions/fts++/Makefile
	extensions/fts++/test/Makefile
	data/Makefile
	data/ontology/Makefile
	python/Makefile
	test/Makefile
	test/dbus/Makefile
	test/direct/Makefile
	doc/Makefile
	po/Makefile.in
])

# check for Xapian
AC_CHECK_PROG(HAVE_XAPIAN, xapian-config, yes, no)
if test "x$HAVE_XAPIAN" = "xno"; then
  AC_MSG_ERROR("You need the Xapian development files in order to compile Zeitgeist")
fi
XAPIAN_LIBS=`xapian-config --libs`
XAPIAN_CXXFLAGS=`xapian-config --cxxflags`
AC_SUBST(XAPIAN_LIBS)
AC_SUBST(XAPIAN_CXXFLAGS)

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

cat <<EOF

${PACKAGE}-${VERSION}

  Build Environment
    Install Prefix:     ${prefix}

  Optional dependencies
    fts++:              ${fts}
    dee-icu:            ${with_dee_icu}

EOF

