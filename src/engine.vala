/* zeitgeist-daemon.vala
 *
 * Copyright © 2011 Collabora Ltd.
 *             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
 *
 * Based upon a Python implementation (2009-2011) by:
 *  Markus Korn <thekorn@gmx.net>
 *  Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
 *  Seif Lotfy <seif@lotfy.com>
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

using Sqlite;

public errordomain EngineError
{
	DATABASE_ERROR
}

public class Engine : Object
{

	Database database;
	uint32 last_id;

	public Engine () throws EngineError
	{
		int rc;
	
		rc = Database.open(
			"/home/rainct/.local/share/zeitgeist/activity.sqlite",
			out database);
		if (rc != Sqlite.OK) {
			stderr.printf ("Can't open database: %d, %s\n", rc,
				database.errmsg ());
			throw new EngineError.DATABASE_ERROR("Fail.");
		}
		
		rc = database.exec ("SELECT MAX(id) FROM event",
			(n_columns, values, column_names) =>
			{
				last_id = int.parse(values[0]);
				return 0;
			}, null);
		
		stdout.printf("last_id: %u\n", last_id);
	}

	public void close ()
	{
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
