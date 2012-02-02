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

        public const string DATA_FOLDER = "zeitgeist";
        public const string DATABASE_BASENAME = "activity.sqlite";
        public const string USER_EXTENSION_PATH = "";

        // D-Bus
        public const string DBUS_INTERFACE = "";
        public const string SIG_EVENT = "asaasay";

        // configure runtime cache for events
        // default size is 2000
        public const uint CACHE_SIZE = 0;

        public unowned string get_data_path ()
        {
            if (DATA_PATH != null) return DATA_PATH;

            DATA_PATH = Environment.get_variable ("ZEITGEIST_DATA_PATH") ??
                Path.build_filename (Environment.get_user_data_dir (),
                    DATA_FOLDER);

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
                Path.build_filename (get_data_path (), DATABASE_BASENAME);

            debug ("DATABASE_FILE_PATH = %s", DATABASE_FILE_PATH);

            return DATABASE_FILE_PATH;
        }

        public unowned string get_database_file_backup_path ()
        {
            if (DATABASE_FILE_BACKUP_PATH != null)
                return DATABASE_FILE_BACKUP_PATH;

            DATABASE_FILE_BACKUP_PATH =
                Environment.get_variable ("ZEITGEIST_DATABASE_BACKUP_PATH") ??
                Path.build_filename (get_data_path (),
                    DATABASE_BASENAME + ".bck");

            debug ("DATABASE_FILE_BACKUP_PATH = %s", DATABASE_FILE_BACKUP_PATH);

            return DATABASE_FILE_BACKUP_PATH;
        }

        public string get_database_file_retire_name ()
        {
            return DATABASE_BASENAME + ".%s.bck".printf (
                new DateTime.now_local ().format ("%Y%m%d-%H%M%S"));
        }

        public unowned string get_local_extensions_path ()
        {
            if (LOCAL_EXTENSIONS_PATH != null) return LOCAL_EXTENSIONS_PATH;

            LOCAL_EXTENSIONS_PATH = Path.build_filename (get_data_path (),
                "extensions");

            debug ("LOCAL_EXTENSIONS_PATH = %s", LOCAL_EXTENSIONS_PATH);

            return LOCAL_EXTENSIONS_PATH;
        }

        public bool using_in_memory_database ()
        {
            return get_database_file_path () == ":memory:";
        }

        public void backup_database () throws Error
        {
            File original;
            File destination;
            original = File.new_for_path (get_database_file_path ());
            destination = File.new_for_path (get_database_file_backup_path ());

            original.copy (destination, FileCopyFlags.OVERWRITE, null, null);
        }

        public void retire_database () throws Error
        {
            File dbfile = File.new_for_path (get_database_file_path ());
            dbfile.set_display_name (get_database_file_retire_name ());
        }

        /**
         * Check if the value starts with the negation operator. If it does,
         * remove the operator from the value and return true. Otherwise,
         * return false.
         */
        public static bool parse_negation (ref string val)
        {
            if (!val.has_prefix ("!"))
                return false;
            val = val.substring (1);
            return true;
        }

        /**
         * Check if the value starts with the noexpand operator. If it does,
         * remove the operator from the value and return true. Otherwise,
         * return false.
         *
         * Check for the negation operator before calling this function.
         */
        public static bool parse_noexpand (ref string val)
        {
            if (!val.has_prefix ("+"))
                return false;
            val = val.substring (1);
            return true;
        }


        /**
         * Check if the value ends with the wildcard character. If it does,
         * remove the wildcard character from the value and return true.
         * Otherwise, return false.
         */
        public static bool parse_wildcard (ref string val)
        {
            if (!val.has_suffix ("*"))
                return false;
            unowned uint8[] val_data = val.data;
            val_data[val_data.length-1] = '\0';
            return true;
        }

    }
}

// vim:expandtab:ts=4:sw=4
