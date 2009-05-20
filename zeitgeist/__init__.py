try:
    import config

except ImportError:
    # No config module, this is straight from the repository
    class MockConfig:
        __file__ = __file__
        prefix = ""
        datadir = ""
        bindir = "."
        localedir = "/usr/share/locale"
        pkgdatadir = "./data/"
        libdir = ""
        libexecdir = ""
        PACKAGE = "gnome-zeitgeist"
        VERSION = "bzr"
    config = MockConfig()
