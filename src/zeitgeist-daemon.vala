/* zeitgeist-daemon.vala
 *
 * Copyright (C) 2011  Seif Lotfy <seif@lotfy.com>
 * 
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 2 of the License, or
 * (at your option) any later version.
 *  
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *  
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

using GLib;

public class Zeitgeist : Object {
	public Zeitgeist () {
	}

	public void run () {
	}

	static int main (string[] args) {
		var zeitgeist = new Zeitgeist ();
		zeitgeist.run ();
		return 0;
	}

}
