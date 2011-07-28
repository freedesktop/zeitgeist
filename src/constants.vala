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
        public static string DATA_PATH;
        // Paths
        public static string DATABASE_FILE_PATH;
        public static string DATABASE_FILE_BACKUP_PATH;
        public static string DEFAULT_LOG_PATH;
        public static string LOCAL_EXTENSIONS_PATH;

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

        public const string ZEITGEIST_DATA_FOLDER = "bluebird";

        public void initialize ()
        {
            // Get the value of the ZEITGEIST_DATA_PATH environment variable. 
            // If it isn't set, then set it tothe value of XDG Data Path + /zeitgeist/
            // but first makes sure the directory exists
            DATA_PATH = Environment.get_variable ("ZEITGEIST_DATA_PATH");
            if (DATA_PATH == null)
            {
                DATA_PATH = Path.build_filename (Environment.get_user_data_dir (), ZEITGEIST_DATA_FOLDER);
                // If directory does not exist create directory
                if (!FileUtils.test (DATA_PATH , FileTest.IS_DIR))
                {
                     DirUtils.create (DATA_PATH , 0755);
                }
            }
            else
            {
                if (!FileUtils.test (DATA_PATH , FileTest.IS_DIR)){
                    // FIXME throw error here
                    stdout.printf("ERROR: %s does not exist \n", DATA_PATH);
                }
            }
            stdout.printf("DATA_PATH = %s\n", DATA_PATH);
            
            
            DATABASE_FILE_PATH = Environment.get_variable ("ZEITGEIST_DATABASE_PATH");
            if (DATABASE_FILE_PATH == null)
            {
                DATABASE_FILE_PATH = Path.build_filename (DATA_PATH, "activity.sqlite");
            }
            stdout.printf("DATABASE_FILE_PATH = %s\n", DATABASE_FILE_PATH);
            
            
            DATABASE_FILE_BACKUP_PATH = Environment.get_variable ("ZEITGEIST_DATABASE_BACKUP_PATH");
            if (DATABASE_FILE_BACKUP_PATH == null)
            {
                DATABASE_FILE_BACKUP_PATH =Path.build_filename (DATA_PATH, "activity.sqlite.bck");
            }
            stdout.printf("DATABASE_FILE_BACKUP_PATH = %s\n", DATABASE_FILE_BACKUP_PATH);
            
            LOCAL_EXTENSIONS_PATH = Path.build_filename (DATA_PATH, "extensions");
            if (!FileUtils.test (LOCAL_EXTENSIONS_PATH , FileTest.IS_DIR)){
                     DirUtils.create (LOCAL_EXTENSIONS_PATH , 0755);
            }
            stdout.printf("LOCAL_EXTENSIONS_PATH = %s\n", LOCAL_EXTENSIONS_PATH);
        }
    }
}

// vim:expandtab:ts=4:sw=4
