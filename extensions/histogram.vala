/* histogram.vala
 *
 * Copyright © 2011 Michal Hruby <michal.mhr@gmail.com>
 * Copyright © 2011 Stefano Candori <stefano.candori@gmail.com>
 *
 * Based upon a Python implementation (2010-2011) by:
 *  Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
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
    [DBus (name = "org.gnome.zeitgeist.Histogram")]
    public interface RemoteHistogram: Object
    {
        [DBus (signature = "a(xu)")]
        public abstract Variant get_histogram_data () throws Error;
    }

    public class Histogram: Extension, RemoteHistogram
    {

        private uint registration_id = 0;

        construct
        {
            // This will be called after bus is acquired, so it shouldn't block
            try
            {
                var connection = Bus.get_sync (BusType.SESSION, null);
                registration_id = connection.register_object<RemoteHistogram> (
                    "/org/gnome/zeitgeist/journal/activity", this);
            }
            catch (Error err)
            {
                warning ("%s", err.message);
            }
        }

        public override void unload ()
        {
            try
            {
                var connection = Bus.get_sync (BusType.SESSION, null);
                if (registration_id != 0)
                {
                    connection.unregister_object (registration_id);
                    registration_id = 0;
                }
            }
            catch (Error err)
            {
                warning ("%s", err.message);
            }

            debug ("%s, this.ref_count = %u", GLib.Log.METHOD, this.ref_count);
        }

        public Variant get_histogram_data () throws Error
        {
            var builder = new VariantBuilder (new VariantType ("a(xu)"));

            string sql = """
                SELECT strftime('%s', datetime(timestamp/1000, 'unixepoch',
                'localtime'), 'start of day') AS daystamp,
                COUNT(*)
                FROM event
                GROUP BY daystamp
                ORDER BY daystamp DESC
                """;

            Sqlite.Statement stmt;
            var database = engine.database;
            unowned Sqlite.Database db = database.database;

            int rc = db.prepare_v2 (sql, -1, out stmt);
            database.assert_query_success (rc, "SQL error");

            while ((rc = stmt.step ()) == Sqlite.ROW)
            {
                int64 t = stmt.column_int64 (0);
                uint32 count = stmt.column_int (1);

                builder.add ("(xu)", t, count);
            }
            database.assert_query_success (rc, "Error in get_histogram_data",
                Sqlite.DONE);

            return builder.end ();
        }

    }

    [ModuleInit]
#if BUILTIN_EXTENSIONS
    public static Type histogram_init (TypeModule module)
    {
#else
    public static Type extension_register (TypeModule module)
    {
#endif
        return typeof (Histogram);
    }
}

// vim:expandtab:ts=4:sw=4
