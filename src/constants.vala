/* constants.vala
 *
 * Copyright © 2011 Collabora Ltd.
 *             By Seif Lotfy <seif@lotfy.com>
 * Copyright © 2011 Michal Hruby <michal.mhr@gmail.com>
 * Copyright © 2011 Manish Sinha <manishsinha@ubuntu.com>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, either version 2.1 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

namespace Zeitgeist
{
    namespace Constants
    {
        public static string BASE_DIRECTORY;
        public static string DATA_PATH;

        // Directories
        public const string DATABASE_FILE = "";
        public const string DATABASE_FILE_BACKUP = "";
        public const string DEFAULT_LOG_PATH = "";

        // D-Bus
        public const string DBUS_INTERFACE = "";
        public const string SIG_EVENT = "asaasay";

        // Required version of DB schema
        public const string CORE_SCHEMA = "core";
        public const int CORE_SCHEMA_VERSION = 4;

        public const string USER_EXTENSION_PATH = "";

        // configure runtime cache for events
        // default size is 2000
        public const uint CACHE_SIZE = 0;

        public const string ZEITGEIST_DATA_FOLDER = "zeitgeist";
        public const string ZEITGEIST_DATABASE_FILENAME = "activity.sqlite";

        public void initialize ()
        {
            // FIXME: append "/zeitgeist"
            BASE_DIRECTORY = Path.build_filename(Environment.get_user_data_dir (), ZEITGEIST_DATA_FOLDER);
            // If directory does not exist create directory
            if (!FileUtils.test (BASE_DIRECTORY, FileTest.IS_DIR)){
                File.new_for_path (BASE_DIRECTORY).make_directory ();
            }
            DATA_PATH = Environment.get_variable ("ZEITGEIST_DATA_PATH");
            
            stdout.printf("BASE_DIRECTORY = %s\n", BASE_DIRECTORY);
            stdout.printf("DATA_PATH = %s\n", DATA_PATH);
        }
    }
}

// vim:expandtab:ts=4:sw=4
