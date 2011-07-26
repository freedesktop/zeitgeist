/* zeitgeist-daemon.vala
 *
 * Copyright © 2011 Collabora Ltd.
 *             By Seif Lotfy <seif@lotfy.com>
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

public class Constants : Object {

	public string BASE_DIRECTORY = Environment.get_user_data_dir ();
	// Directories
	public string DATA_PATH = Environment.get_variable ("ZEITGEIST_DATA_PATH");
	public const string DATABASE_FILE = "";
	public const string DATABASE_FILE_BACKUP = "";
	public const string DEFAULT_LOG_PATH = "";

	// D-Bus
	public const string DBUS_INTERFACE = "";
	public const string SIG_EVENT = "asaasay";

	// Required version of DB schema
	public const string CORE_SCHEMA="core";
	public const int CORE_SCHEMA_VERSION = 4;

	public const string USER_EXTENSION_PATH = "";

	// configure runtime cache for events
	// default size is 2000
	public const string CACHE_SIZE = "";

	public Constants(){}
}

