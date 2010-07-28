import sys
import os

runpath = os.path.dirname(__file__)

if not os.path.isfile(os.path.join(runpath, '_config.py.in')):
    import _config as _install_config
    del runpath

else:
    # This is straight from the repository.
    # We check for the presence of the .in file instead of trying to import
    # and catching the error so that this still works after running "make".
    import os
    import sys
    
    class RepositoryConfig:
        __file__ = __file__
        prefix = ""
        datadir = ""
        bindir = os.path.join(os.path.dirname(__file__), "..")
        localedir = "/usr/share/locale"
        pkgdatadir = os.path.join(bindir, "data")
        privatepythondir = bindir
        datasourcedir = os.path.normpath(os.path.join(bindir, "_zeitgeist/loggers/datasources"))
        extensiondir = os.path.normpath(os.path.join(bindir, "_zeitgeist/engine/extensions"))
        libdir = ""
        libexecdir = ""
        PACKAGE = "zeitgeist"
        
        @property
        def VERSION(self):
            try:
                return 'bzr (rev %s)' % open(os.path.join(runpath,
                    '../.bzr/branch/last-revision')).read().split()[0]
            except (IOError, IndexError):
                return "bzr"
    
    _install_config = RepositoryConfig()

class Config:
    
    # This class can be (ab)used to store additional data which needs to be
    # globally available to all files of a Zeitgeist process.
    #
    # For example, the arguments with which zeitgeist-daemon is called, as
    # they affect many separate parts of the code.
    
    def __getattr__(self, name):
        return getattr(_install_config, name)
    
    def setup_path(self):
        sys.path.insert(0, self.privatepythondir)

_config = Config()
