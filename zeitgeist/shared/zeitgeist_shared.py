# -.- encoding: utf-8 -.-# -.- encoding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Seif Lotfy <seif@lotfy.com>
# Copyright © 2009 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
# Copyright © 2009 Natan Yellin <aantny@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

sig_plain_data = "(isssssssbsss)"

def plainify_dict(item_list):
	return (
		item_list["timestamp"],
		item_list["uri"],
		item_list["text"],
		item_list["source"],
		item_list["content"],
		item_list["mimetype"], 
		item_list["tags"],
		item_list["use"],
		item_list["bookmark"] if "bookmark" in item_list else False,
		item_list["icon"],
		item_list["app"],
		item_list["origin"],
		)

def dictify_data(item_list):
    return {
		"timestamp": item_list[0],
		"uri": item_list[1],
		"text": item_list[2],
		"source": item_list[3],
		"content": item_list[4],
		"mimetype": item_list[5],
		"tags": item_list[6],
		"use": item_list[7],
		"bookmark": item_list[8],
		"icon": item_list[9],
		"app": item_list[10],
		"origin": item_list[11]
		}
