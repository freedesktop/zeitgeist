AC_INIT([zeitgeist], [0.9.5], [dev@lists.zeitgeist-project.com], [zeitgeist])
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

AM_PROG_VALAC([0.18.0])
AS_IF([test -z "$VALAC"], [AC_MSG_ERROR(["No Vala compiler found."])])

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
SQLITE_REQUIRED=3.7.11
VALADOC_REQUIRED=0.2

ZEITGEIST_REQUIRED="glib-2.0 >= $GLIB_REQUIRED
                    gobject-2.0 >= $GLIB_REQUIRED
                    gmodule-2.0 >= $GLIB_REQUIRED
                    gio-unix-2.0 >= $GLIB_REQUIRED
                    sqlite3 >= $SQLITE_REQUIRED"

PKG_CHECK_MODULES(ZEITGEIST, [$ZEITGEIST_REQUIRED])
AC_SUBST(ZEITGEIST_CFLAGS)
AC_SUBST(ZEITGEIST_LIBS)

AC_CONFIG_FILES([
	Makefile
	src/Makefile
	libzeitgeist/utils/Makefile
	libzeitgeist/Makefile
	libzeitgeist/zeitgeist-2.0.pc
	extensions/Makefile
	extensions/fts++/Makefile
	extensions/fts++/test/Makefile
	data/Makefile
	data/ontology/Makefile
	python/Makefile
	test/Makefile
	test/dbus/Makefile
	test/direct/Makefile
	test/c/Makefile
	test/data/Makefile
	examples/Makefile
	examples/c/Makefile
	examples/vala/Makefile
	doc/Makefile
	doc/libzeitgeist/Makefile
	po/Makefile.in
])

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

#################################################
# Configure option: --enable-explain-queries
#################################################

AC_ARG_ENABLE([explain-queries],
            AS_HELP_STRING([--enable-explain-queries], [Enable SQL debugging]),
            [explain_queries=$enableval],[explain_queries="no"])

AM_CONDITIONAL(EXPLAIN_QUERIES, test "x$explain_queries" = "xyes")

#################################################
# Configure option: --disable-fts
#################################################

AC_ARG_ENABLE([fts],
            AS_HELP_STRING([--disable-fts], [Build without FTS++ extension]),
            [enable_fts=$enableval],[enable_fts="yes"])

AM_CONDITIONAL(HAVE_FTS, test "x$enable_fts" != "xno")

if test "x$enable_fts" != "xno"; then
    # check for Xapian
    AC_CHECK_PROG(HAVE_XAPIAN, xapian-config, yes, no)
    if test "x$HAVE_XAPIAN" = "xno"; then
      AC_MSG_ERROR("You need the Xapian development files in order to compile Zeitgeist")
    fi
    XAPIAN_LIBS=`xapian-config --libs`
    XAPIAN_CXXFLAGS=`xapian-config --cxxflags`
    AC_SUBST(XAPIAN_LIBS)
    AC_SUBST(XAPIAN_CXXFLAGS)
fi

#################################################
# Libzeitgeist 2.0
#################################################

LIBZEITGEIST_VERSION_MAJOR="2"
LIBZEITGEIST_VERSION_MINOR="0"
LIBZEITGEIST_VERSION_PATCH="0"
LIBZEITGEIST_VERSION="$LIBZEITGEIST_VERSION_MAJOR.$LIBZEITGEIST_VERSION_MINOR.$LIBZEITGEIST_VERSION_PATCH"
AC_SUBST(LIBZEITGEIST_VERSION_MAJOR)
AC_SUBST(LIBZEITGEIST_VERSION_MINOR)
AC_SUBST(LIBZEITGEIST_VERSION_PATCH)
AC_SUBST(LIBZEITGEIST_VERSION)

# Before making a release, the ZEITGEIST_LT_VERSION string should be updated.
# The string is of the form C:R:A.
# - If interfaces have been changed or added, but binary compatibility has
#   been preserved, change to C+1:0:A+1
# - If binary compatibility has been broken (eg removed or changed interfaces)
#   change to C+1:0:0
# - If the interface is the same as the previous version, change to C:R+1:A
LIBZEITGEIST_LT_CURRENT=1
LIBZEITGEIST_LT_REV=0
LIBZEITGEIST_LG_AGE=0
LIBZEITGEIST_LT_VERSION="$LIBZEITGEIST_LT_CURRENT:$LIBZEITGEIST_LT_REV:$LIBZEITGEIST_LT_AGE"
AC_SUBST(LIBZEITGEIST_LT_VERSION)

#################################################
# Docs
#################################################

AC_ARG_ENABLE([docs],
    AS_HELP_STRING([--enable-docs], [Enable documentation generation]),
    [enable_docs=$enableval], [enable_docs="yes"]) # FIXME: change to no

found_valadoc=no
AS_IF([test "x$enable_docs" != "xno"], [
    AC_PATH_PROG(VALADOC, valadoc, :)
    AS_IF([test -x "$VALADOC"], [
        found_valadoc=yes
        AC_SUBST(VALADOC)
    ], [
        AS_IF([test "x$enable_docs" == "xyes"], AC_MSG_ERROR([Unable to find valadoc]))
    ])
])

AM_CONDITIONAL(ENABLE_DOCS, test "x$found_valadoc" = "xyes")


AM_CONDITIONAL([HAVE_INTROSPECTION], [test "x$enable_vala" = "xyes"])
# this will set HAVE_INTROSPECTION
GOBJECT_INTROSPECTION_REQUIRE([1.30])

#################################################
# Ontology parsing dependencies
#################################################

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

#################################################
# Summary
#################################################

AC_OUTPUT

cat <<EOF

${PACKAGE}-${VERSION}

  Build environment
    Install Prefix:     ${prefix}

  Optional dependencies
    fts++:              ${enable_fts}
    dee-icu:            ${with_dee_icu}

  Other build options:
    SQL debugging:      ${explain_queries}
    libzeitgeist docs:  ${enable_docs}

EOF
