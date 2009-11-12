# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Alexander Gabriel <einalex@mayanna.org>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sqlite3
from time import time

from _zeitgeist.engine import DB_PATH
from _zeitgeist.engine.dbutils import EntityTable
