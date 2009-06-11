try:
    import config

except ImportError:
    # No config module, this is straight from the repository
    
    import os
    
    class MockConfig:
        __file__ = __file__
        prefix = ""
        datadir = ""
        bindir = os.path.join(os.path.dirname(__file__), "..")
        localedir = "/usr/share/locale"
        pkgdatadir = os.path.join(bindir, "data")
        libdir = ""
        libexecdir = ""
        PACKAGE = "gnome-zeitgeist"  # TODO: change this
        VERSION = "bzr"
    
    config = MockConfig()
