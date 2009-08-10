import sys
import os

prefix = "/usr/local"
datadir = "/usr/local/share"
bindir = "/usr/local/bin"
localedir = "/usr/local/share/locale"
pkgdatadir = "/usr/local/share/zeitgeist"
datasourcedir = "/usr/local/share/zeitgeist/_zeitgeist/loggers/datasources"
libdir = "/usr/local/lib"
libexecdir = "/usr/local/libexec"
PACKAGE = "zeitgeist"
VERSION = "0.2.0"

def setup_path():
    sys.path.insert(0, os.path.join(prefix, 'share/zeitgeist'))
