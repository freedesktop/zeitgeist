#! /bin/sh
set -e

BRANCH="$(basename `pwd`)"
SRCDIR="$(pwd)/../$BRANCH"
DEBDIR="$(pwd)/extra/packaging/debian"
TMPDIR="/tmp/zg-snapshot/"

if [ ! -d "extra/packaging/debian" ]; then
	echo "Wrong working directory; expected source root directory."
	exit 1
fi

if [ -e "$TMPDIR" ]; then
	echo "Temporary directory already exists; please delete it first."
	echo "fakeroot rm -rf $TMPDIR"
	exit 1
fi

mkdir -p "$TMPDIR"
cp -R "$SRCDIR" "$TMPDIR"

cd "$TMPDIR/$BRANCH"
bzr clean-tree --force --unknown --ignored

VERSION=`cat VERSION | tr -d "\n"`
#REVISION=`cat .bzr/branch/last-revision | cut -d' ' -f1`
REVISION=`date +"%Y%m%d"`
FULLVERSION="${VERSION}+bzr${REVISION}"
sed -i "s/$VERSION/$FULLVERSION/" VERSION configure.ac

./autogen.sh
make distcheck

ln -s "$BRANCH/zeitgeist-$FULLVERSION.tar.gz" \
	"../zeitgeist_$FULLVERSION.orig.tar.gz"
cd ..
tar -xzvf "zeitgeist_$FULLVERSION.orig.tar.gz"
cd "zeitgeist-$FULLVERSION"
cp -R "$DEBDIR" .
sed -i "1s/$VERSION/$FULLVERSION/" debian/changelog
sed -i "1s/UNRELEASED/karmic/" debian/changelog
fakeroot rm -rf debian/.svn
debuild -S -sa

echo
echo "Files generated in $TMPDIR."
echo "cd $TMPDIR"
echo "dput ppa:zeitgeist zeitgeist_*_source.changes"
