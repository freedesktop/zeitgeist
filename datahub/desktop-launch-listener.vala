/*
 * Zeitgeist
 *
 * Copyright (C) 2010, 2012 Michal Hruby <michal.mhr@gmail.com>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 * Authored by Michal Hruby <michal.mhr@gmail.com>
 *
 */

using Zeitgeist;

public class DesktopLaunchListener : DataProvider
{
  public DesktopLaunchListener (DataHub datahub)
  {
    GLib.Object (unique_id: "com.zeitgeist-project,datahub,gio-launch-listener",
                 name: "Launched desktop files",
                 description: "Logs events about launched desktop files using GIO",
                 datahub: datahub);
  }

  // if vala didn't have bug in construct-only properties, the properties
  // would be construct-only
  public override string unique_id { get; construct set; }
  public override string name { get; construct set; }
  public override string description { get; construct set; }

  public override DataHub datahub { get; construct set; }
  public override bool enabled { get; set; default = true; }
  public override bool register { get; construct set; default = true; }

  private GLib.DBusConnection bus;
  private uint launched_signal_id = 0;

  construct
  {
    try
    {
      bus = GLib.Bus.get_sync (GLib.BusType.SESSION);
    }
    catch (IOError err)
    {
      warning ("%s", err.message);
    }

    unowned string desktop_env = Environment.get_variable ("XDG_CURRENT_DESKTOP");
    if (desktop_env != null)
    {
      DesktopAppInfo.set_desktop_env (desktop_env);
      return;
    }
  }

  public override void start ()
  {
    if (launched_signal_id != 0) return;

    launched_signal_id = bus.signal_subscribe (null,
                                               "org.gtk.gio.DesktopAppInfo",
                                               "Launched",
                                               "/org/gtk/gio/DesktopAppInfo",
                                               null,
                                               0,
                                               this.signal_received);
  }

  private void signal_received (GLib.DBusConnection connection,
                                string? sender,
                                string object_path,
                                string interface_name,
                                string signal_name,
                                Variant parameters)
  {
    // unpack the variant
    Variant desktop_variant;
    VariantIter uris;
    Variant dict;
    int64 pid;

    parameters.get ("(@aysxas@a{sv})", out desktop_variant, null,
                    out pid, out uris, out dict);

    string desktop_file = desktop_variant.get_bytestring ();
    if (desktop_file == "") return;

    // are we going to do anything with these?
    string uri;
    while (uris.next ("s", out uri))
    {
      debug ("ran with uri: %s", uri);
    }

    // here we should be able to get info about the origin of the launch
    HashTable<string, Variant> extra_params = (HashTable<string, Variant>) dict;

    DesktopAppInfo? dai;
    string launched_uri = Utils.get_actor_for_desktop_file (desktop_file,
                                                            out dai);
    if (launched_uri == null)
    {
      warning ("Unable to open desktop file '%s'", desktop_file);
      return;
    }

    string? launcher_uri = null;
    unowned Variant origin_df = extra_params.lookup ("origin-desktop-file");
    if (origin_df != null)
    {
      launcher_uri = Utils.get_actor_for_desktop_file (origin_df.get_bytestring ());
    }
    else
    {
      unowned Variant origin_prgname = extra_params.lookup ("origin-prgname");
      if (origin_prgname != null)
      {
        unowned string? prgname = origin_prgname.get_bytestring ();
        string origin_desktop_id = prgname + ".desktop";
        DesktopAppInfo id_check = new DesktopAppInfo (origin_desktop_id);
        if (id_check != null) launcher_uri = "application://%s".printf (origin_desktop_id);
      }
    }

    if (!dai.should_show ())
    {
      // FIXME: do something else? Log with WORLD_EVENT?
      return;
    }

    var event = new Zeitgeist.Event ();
    var subject = new Zeitgeist.Subject ();

    event.actor = launcher_uri;
    event.interpretation = ZG.ACCESS_EVENT;
    event.manifestation = ZG.USER_ACTIVITY;
    event.add_subject (subject);

    subject.uri = launched_uri;
    subject.interpretation = NFO.SOFTWARE;
    subject.manifestation = NFO.SOFTWARE_ITEM;
    subject.mimetype = "application/x-desktop";
    subject.text = dai.get_display_name ();

    var arr = new GenericArray<Event> ();
    arr.add (event);

    items_available (arr);
  }

  public override void stop ()
  {
    if (launched_signal_id != 0)
    {
      bus.signal_unsubscribe (launched_signal_id);
      launched_signal_id = 0;
    }
  }
}

