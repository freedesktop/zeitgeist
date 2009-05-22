#! /bin/sh
# Run this to generate all the initial makefiles, etc.

srcdir=`dirname $0`
test -z "$srcdir" && srcdir=.

PKG_NAME=gnome-zeitgeist

(test -f $srcdir/zeitgeist-daemon) || {
	echo -n "**Error**: Directory "\`$srcdir\'" does not look like the"
	echo " top-level $PKG_NAME directory"
	exit 1
}

which gnome-autogen.sh || {
	echo "You need to install gnome-common from the GNOME Git Repository"
	exit 1
}

export PKG_NAME
REQUIRED_AUTOCONF_VERSION=2.57 \
REQUIRED_AUTOMAKE_VERSION=1.9 \
REQUIRED_INTLTOOL_VERSION=0.35.0 \
REQUIRED_PKG_CONFIG_VERSION=0.16.0 \
	USE_GNOME2_MACROS=1 . gnome-autogen.sh --enable-uninstalled-build "$@"

