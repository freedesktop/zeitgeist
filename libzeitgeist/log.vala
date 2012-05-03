/*
 * Copyright © 2012 Canonical Ltd.
 *             By Siegfried-A. Gevatter <siegfried.gevatter@collabora.co.uk>
 *
 * Based upon a C implementation (© 2010-2012 Canonical Ltd) by:
 *  Mikkel Kamstrup Erlandsen <mikkel.kamstrup@canonical.com>
 *  Michal Hruby <michal.hruby@canonical.com>
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

public class Log : Object
{
    private static Log default_instance;

    private RemoteLog proxy;
    private Variant engine_version;

    public Log ()
    {
        Bus.get_proxy<RemoteLog> (BusType.SESSION, Utils.ENGINE_DBUS_NAME,
            Utils.ENGINE_DBUS_PATH, 0, null, (obj, res) =>
            {
                try
                {
                    proxy = Bus.get_proxy.end (res);
                    // process queued..

                    //proxy.notify["g-name-owner"].connect (name_owner_changed);
                }
                catch (IOError err)
                {
                    warning ("%s", err.message);
                }
            });
    }

    public static Log get_default ()
    {
        if (default_instance == null)
            default_instance = new Log ();
        return default_instance;
    }

    public void get_events (uint32[] event_ids, Cancellable? cancellable,
        AsyncReadyCallback callback) throws Error // user_data?
    {
        proxy.get_events (event_ids); // cancellable and stuff
    }

}

}
