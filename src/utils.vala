/* utils.vala
 *
 * Copyright © 2011 Collabora Ltd.
 *             By Seif Lotfy <seif@lotfy.com>
 *             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
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
    namespace Utils
    {
        // Paths
        private static string DATA_PATH;
        private static string DATABASE_FILE_PATH;
        private static string DATABASE_FILE_BACKUP_PATH;
        private static string LOCAL_EXTENSIONS_PATH;

        public const string ZEITGEIST_DATA_FOLDER = "bluebird";
        public const string USER_EXTENSION_PATH = "";

        // D-Bus
        public const string DBUS_INTERFACE = "";

        // Required version of DB schema
        public const string CORE_SCHEMA = "core";
        public const int CORE_SCHEMA_VERSION = 4;

        // configure runtime cache for events
        // default size is 2000
        public const uint CACHE_SIZE = 0;

        public unowned string get_data_path ()
        {
            if (DATA_PATH != null) return DATA_PATH;

            DATA_PATH = Environment.get_variable ("ZEITGEIST_DATA_PATH") ??
                Path.build_filename (Environment.get_user_data_dir (),
                    ZEITGEIST_DATA_FOLDER);

            if (!FileUtils.test (DATA_PATH, FileTest.IS_DIR))
            {
                 DirUtils.create_with_parents (DATA_PATH, 0755);
            }

            debug ("DATA_PATH = %s", DATA_PATH);

            return DATA_PATH;
        }

        public unowned string get_database_file_path ()
        {
            if (DATABASE_FILE_PATH != null) return DATABASE_FILE_PATH;

            DATABASE_FILE_PATH =
                Environment.get_variable ("ZEITGEIST_DATABASE_PATH") ??
                Path.build_filename (get_data_path (), "activity.sqlite");

            debug ("DATABASE_FILE_PATH = %s", DATABASE_FILE_PATH);

            return DATABASE_FILE_PATH;
        }

        public unowned string get_database_file_backup_path ()
        {
            if (DATABASE_FILE_BACKUP_PATH != null)
                return DATABASE_FILE_BACKUP_PATH;

            DATABASE_FILE_BACKUP_PATH =
                Environment.get_variable ("ZEITGEIST_DATABASE_BACKUP_PATH") ??
                Path.build_filename (get_data_path (), "activity.sqlite.bck");

            debug ("DATABASE_FILE_BACKUP_PATH = %s", DATABASE_FILE_BACKUP_PATH);

            return DATABASE_FILE_BACKUP_PATH;
        }

        public unowned string get_local_extensions_path ()
        {
            if (LOCAL_EXTENSIONS_PATH != null) return LOCAL_EXTENSIONS_PATH;

            LOCAL_EXTENSIONS_PATH = Path.build_filename (get_data_path (),
                "extensions");

            debug ("LOCAL_EXTENSIONS_PATH = %s", LOCAL_EXTENSIONS_PATH);

            return LOCAL_EXTENSIONS_PATH;
        }
    }
}

// vim:expandtab:ts=4:sw=4
