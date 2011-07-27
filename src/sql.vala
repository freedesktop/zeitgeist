/* zeitgeist-daemon.vala
 *
 * Copyright © 2011 Collabora Ltd.
 *             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
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

using Sqlite;

namespace Zeitgeist.SQLite
{

public class ZeitgeistDatabase : Object
{

	Database database;

	public ZeitgeistDatabase () throws EngineError
	{
		int rc = Database.open(
			"/home/rainct/.local/share/zeitgeist/activity.sqlite",
			out database);
		assert_query_success(rc, "Can't open database");
		
		// FIXME: check DB integrity, create it if needed, etc.
	}

	public uint32 get_last_id () throws EngineError
	{
		int last_id = -1;
		int rc = database.exec ("SELECT MAX(id) FROM event",
			(n_columns, values, column_names) =>
			{
				last_id = int.parse(values[0]);
				return 0;
			}, null);
		assert_query_success(rc, "Can't query database");
		assert (last_id != -1);
		return last_id;
	}

	private void assert_query_success (int rc, string msg) throws EngineError
	{
		if (rc != Sqlite.OK)
		{
			stderr.printf ("%s: %d, %s\n", msg, rc, database.errmsg ());
			throw new EngineError.DATABASE_ERROR("Fail.");
		}
	}

/*
	if ((rc = db.prepare_v2 (args[2], -1, out stmt, null)) == 1) {
		printerr ("SQL error: %d, %s\n", rc, db.errmsg ());
		return;
	}

	cols = stmt.column_count();
	do {
		rc = stmt.step();
		switch (rc) {
			case Sqlite.DONE:
				break;
			case Sqlite.ROW:
				for (col = 0; col < cols; col++) {
					string txt = stmt.column_text(col);
					print ("%s = %s\n", stmt.column_name (col), txt);
				}
				break;
			default:
				printerr ("Error: %d, %s\n", rc, db.errmsg ());
				break;
		}
	} while (rc == Sqlite.ROW);
*/

}

}
