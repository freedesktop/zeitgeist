import os.path

if not os.path.isfile(os.path.join(os.path.dirname(__file__), '_config.py.in')):
    import _config

else:
    # This is straight from the repository.
    # We check for the presence of the .in file instead of trying to import
    # and catching the error so that this still works after running "make".
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
        PACKAGE = "zeitgeist"
        VERSION = "bzr"
        
        def setup_path(self):
            sys.path.insert(0, self.bindir)
    
    _config = MockConfig()
