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

namespace Zeitgeist
{
    [DBus (name = "org.gnome.zeitgeist.EngineError")]
    public errordomain EngineError
    {
        BACKUP_FAILED,
        DATABASE_BUSY,
        DATABASE_CANTOPEN,
        DATABASE_CORRUPT,
        DATABASE_ERROR,
        DATABASE_RETIRE_FAILED,
        EXISTING_INSTANCE,
        INVALID_ARGUMENT,
        INVALID_EVENT,
        INVALID_KEY,
    }

    // vala doesn't include proper headers, this fixes it
    private static void vala_bug_workaround ()
    {
        try
        {
            Bus.get_sync (BusType.SESSION, null);
        }
        catch (Error err)
        {
            // kill "unused method" warning
            vala_bug_workaround ();
        }
    }
}

// vim:expandtab:ts=4:sw=4
