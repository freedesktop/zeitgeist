#! /bin/sh
# Run this to generate all the initial makefiles, etc.

srcdir=`dirname $0`
test -z "$srcdir" && srcdir=.

PKG_NAME=zeitgeist

(test -f $srcdir/zeitgeist-daemon.py) || {
	echo -n "**Error**: Directory "\`$srcdir\'" does not look like the"
	echo " top-level $PKG_NAME directory"
	exit 1
}

which rapper || {
	echo "You need to install raptor-utils"
	exit 1
}

export PKG_NAME

if which gnome-autogen.sh ; then
  REQUIRED_AUTOMAKE_VERSION=1.11
  REQUIRED_AUTOCONF_VERSION=2.57 \
  REQUIRED_AUTOMAKE_VERSION=1.9 \
  REQUIRED_INTLTOOL_VERSION=0.35.0 \
  REQUIRED_PKG_CONFIG_VERSION=0.16.0 \
	    USE_GNOME2_MACROS=1 . gnome-autogen.sh --enable-uninstalled-build "$@"
else
  if which intltoolize && which autoreconf ; then
    intltoolize --copy --force --automake || \
      (echo "There was an error in running intltoolize." > /dev/stderr;
       exit 1)
    autoreconf --force --install || \
      (echo "There was an error in running autoreconf." > /dev/stderr;
       exit 1)
  else
    echo "No build script available.  You have two choices:"
    echo "1. You need to install the gnome-common module and make"
    echo "   sure the gnome-autogen.sh script is in your \$PATH."
    echo "2. You need to install the following scripts:"
    echo "   * intltool"
    echo "   * libtool"
    echo "   * automake"
    echo "   * autoconf"
    echo "   Additionally, you need to make"
    echo "   sure that they are in your \$PATH."
    exit 1
  fi
fi