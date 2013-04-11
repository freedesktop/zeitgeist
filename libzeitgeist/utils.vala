/* utils.vala
 *
 * Copyright © 2011 Collabora Ltd.
 *             By Seif Lotfy <seif@lotfy.com>
 *             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
 * Copyright © 2011 Michal Hruby <michal.mhr@gmail.com>
 * Copyright © 2011 Manish Sinha <manishsinha@ubuntu.com>
 * Copyright © 2013 Seif Lotfy <seif@lotfy.com>
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
    /**
     * Utility functions. FOR INTERNAL USE ONLY
     * 
     * A set of funtions that if used would only affect libzeitgeist in the
     * code it is used in.
     */
    namespace Utils
    {
        // Paths
        private static string DATA_PATH;
        private static string DATABASE_FILE_PATH;
        private static string DATABASE_FILE_BACKUP_PATH;
        private static string LOCAL_EXTENSIONS_PATH;

        private const string DATA_FOLDER = "zeitgeist";
        private const string DATABASE_BASENAME = "activity.sqlite";
        private const string USER_EXTENSION_PATH = "";

        // D-Bus
        public const string ENGINE_DBUS_NAME = "org.gnome.zeitgeist.Engine";
        public const string ENGINE_DBUS_PATH = "/org/gnome/zeitgeist/log/activity";
        public const string SIG_EVENT = "asaasay";
        public const size_t MAX_DBUS_RESULT_SIZE = 4 * 1024 * 1024; // 4MiB

        // configure runtime cache for events
        // default size is 2000
        public const uint CACHE_SIZE = 0;

        public unowned string get_data_path ()
        {
            if (DATA_PATH != null) return DATA_PATH;

            DATA_PATH = Environment.get_variable ("ZEITGEIST_DATA_PATH") ??
                get_default_data_path ();

            if (!FileUtils.test (DATA_PATH, FileTest.IS_DIR))
            {
                 DirUtils.create_with_parents (DATA_PATH, 0755);
            }

            debug ("DATA_PATH = %s", DATA_PATH);

            return DATA_PATH;
        }

        public string get_default_data_path ()
        {
            return Path.build_filename (Environment.get_user_data_dir (),
                DATA_FOLDER);
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

        /**
         * Sets the filepath of the database.
         * @param path a {@link string}
         */
        public void set_database_file_path (string path) {
            DATABASE_FILE_PATH = path;
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

        /**
         * @return Whether a in-memory SQLite database is in use (vs.
         *         a file-based one).
         */
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

            message ("Backing up database to \"%s\" for schema upgrade...",
                get_database_file_backup_path ());
            original.copy (destination, FileCopyFlags.OVERWRITE, null, null);
        }

        /**
         * Check if the value starts with the negation operator. If it does,
         * remove the operator from the value and return true. Otherwise,
         * return false.
         *
         * @param val value to check
         */
        public bool parse_negation (ref string val)
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
         *
         * @param val value to check
         */
        public bool parse_noexpand (ref string val)
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
         *
         * @param val value to check
         */
        public bool parse_wildcard (ref string val)
        {
            if (!val.has_suffix ("*"))
                return false;
            unowned uint8[] val_data = val.data;
            val_data[val_data.length-1] = '\0';
            return true;
        }

        /**
         * Return true if a string is empty (null or containing just a null
         * byte).
         *
         * @param s string to check
         */
        public bool is_empty_string (string? s)
        {
            return s == null || s == "";
        }

        internal void assert_sig (bool condition, string error_message)
        throws DataModelError
        {
            if (unlikely (!condition))
                throw new DataModelError.INVALID_SIGNATURE (error_message);
        }

        /**
         * @return True if direct reading of the DB is enabled for Log, default is True.
         */
        public bool log_may_read_directly ()
        {
            var env_var = Environment.get_variable ("ZEITGEIST_LOG_DIRECT_READ");
            if (env_var == null)
                return true;
            return (int.parse (env_var) != 0);
        }
    }
}

// vim:expandtab:ts=4:sw=4
