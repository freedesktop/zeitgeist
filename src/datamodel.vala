/* zeitgeist-daemon.vala
 *
 * Copyright © 2011 Collabora Ltd.
 *             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
 * 			 © Manish Sinha <manishsinha@ubuntu.com>
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

public class Event : Object {

	public uint32?   id { get; set; }
	public int64     timestamp { get; set; }
	public string    interpretation { get; set; }
	public string    manifestation { get; set; }
	public string    actor { get; set; }
	public string    origin { get; set; }
	
	public Subject[] subjects { get; set; }
	public uint8[]   payload { get; set; }

	public Event.from_variant (Variant event_variant) {
		stdout.printf("VAR: %u\n\n", event_variant.get_uint32());
	}

}

public class Subject : Object {
	public string uri { get; set; }
	public string interpretation { get; set; }
	public string manifestation { get; set; }
	public string mimetype { get; set; }
	public string origin { get; set; }
	public string text { get; set; }
	public string storage { get; set; }
}
