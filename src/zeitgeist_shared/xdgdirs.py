# -.- encoding: utf-8 -.-

import os
import re

"""
	This module gives paths according to the FreeDesktop.org Base
	Directory specification.
	
	http://standards.freedesktop.org/basedir-spec/
	
	It is based upon code from LottaNZB, branch:
		lp:~lottanzb/lottanzb/xdg-location
"""

CONFIG_HOME = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser('~/.config'))
CACHE_HOME = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cachee"))
DATA_HOME = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))

if os.path.isfile(os.path.join(CONFIG_HOME, "user-dirs.dirs")):
	user_dirs_file = open(os.path.join(CONFIG_HOME, "user-dirs.dirs"))
	pattern = re.compile("^(?P<key>[A-Z_]+)=\s*\"(?P<value>.+)\"\s*$")
	
	_USER_DIRS = {}
	for line in user_dirs_file:
		match = pattern.match(line)
		if match:
			_USER_DIRS[match.group("key")] = os.path.expandvars(match.group("value"))
	
	for key in _USER_DIRS:
		_USER_DIRS[key] = os.environ.get(key, _USER_DIRS[key])
	
def xdg_directory(name, default='~/'):
	xdgstring = "XDG_%s_DIR" % name.upper()
	return _USER_DIRS[xdgstring] if xdgstring in _USER_DIRS else \
		os.path.expanduser(default)
