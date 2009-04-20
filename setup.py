#!/usr/bin/env python

import os
import glob

from distutils.core import setup

setup(
	name			= "gnome-zeitgeist",
	version			= "0.0.4",
	description		= "file usage journal",
	author			= "The Zeitgeist Team",
	license			= "GPLv3+",
	url				= "http://live.gnome.org/GnomeZeitgeist",
	download_url	= "https://launchpad.net/gnome-zeitgeist/+download",
	
	data_files		= [
		("share/gnome-zeitgeist/src", glob.glob("src/*")),
		("share/gnome-zeitgeist/data", glob.glob("data/*")),
		("share/applications", ["data/extra/zeitgeist-journal.desktop"]),
		("share/dbus-1/services", ["data/extra/org.gnome.Zeitgeist.service"]),
		("share/doc/gnome-zeitgeist", ["AUTHORS", "MAINTAINERS", "TODO"]),
		],
	
	classifiers		= [
		"License :: OSI-Approved :: GNU General Public License (GPL)",
		"Intended Audience :: End Users/Desktop",
		"Development Status :: 3 - Alpha",
		"Topic :: Desktop Environment :: GNOME",
		"Programming Language :: Python",
		],
)
