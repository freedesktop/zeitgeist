try:
    import config
except ImportError:
    # no config module, this is straight from repository
    class MockConfig:
        __file__ = __file__
        prefix=""
        datadir=""
        bindir="."
        localedir="/usr/share/locale"
        pkgdatadir="./data/"
        libdir=""
        libexecdir=""
        PACKAGE="gnome-zeitgeist"
        VERSION="bzr"
    config = MockConfig()
