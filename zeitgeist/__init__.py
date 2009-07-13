try:
    import _config

except ImportError:
    # No config module, this is straight from the repository
    
    import os
    import sys
    
    class MockConfig:
        __file__ = __file__
        prefix = ""
        datadir = ""
        bindir = os.path.join(os.path.dirname(__file__), "..")
        localedir = "/usr/share/locale"
        pkgdatadir = os.path.join(bindir, "data")
        datasourcedir = os.path.join(bindir, "_zeitgeist/loggers/datasources")
        libdir = ""
        libexecdir = ""
        PACKAGE = "gnome-zeitgeist"  # TODO: change this
        VERSION = "bzr"
        
        def setup_path(self):
            sys.path.insert(0, self.bindir)
    
    _config = MockConfig()
