/*
 * Zeitgeist
 *
 * Copyright (C) 2010 Michal Hruby <michal.mhr@gmail.com>
 * Copyright (C) 2012 Canonical Ltd.
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
 * Authored by Siegfried-A. Gevatter <siegfried.gevatter@collabora.co.uk>
 *
 */

using Zeitgeist;

public class RecentManagerGtk : DataProvider
{
  public RecentManagerGtk (DataHub datahub)
  {
    GLib.Object (unique_id: "com.zeitgeist-project,datahub,recent",
                 name: "Recently Used Documents",
                 description: "Logs events from GtkRecentlyUsed",
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

  private unowned Gtk.RecentManager recent_manager;
  private uint idle_id = 0;

  construct
  {
    recent_manager = Gtk.RecentManager.get_default ();
  }

  public override void start ()
  {
    recent_manager.changed.connect (this.items_changed);

    items_available (get_items ());
  }

  public override void stop ()
  {
    recent_manager.changed.disconnect (this.items_changed);
  }

  private void items_changed ()
  {
    if (idle_id == 0)
    {
      idle_id = Idle.add (() =>
      {
        items_available (get_items ());
        idle_id = 0;
        return false;
      });
    }
  }

  protected GenericArray<Event> get_items ()
  {
    GenericArray<Event> events = new GenericArray<Event> ();

    int64 signal_time = Timestamp.from_now ();
    string[] ignored_actors = datahub.get_data_source_actors ();

    foreach (Gtk.RecentInfo ri in recent_manager.get_items ())
    {
      // GFile and GtkRecentInfo use different encoding of the uris, so we'll
      // do this
      File file_obj = File.new_for_uri (ri.get_uri ());
      string uri = file_obj.get_uri ();
      if (ri.get_private_hint () || uri.has_prefix ("file:///tmp/"))
        continue;
      if (ri.is_local () && !ri.exists ())
        continue;

      var last_app = ri.last_application ().strip ();
      unowned string exec_str;
      uint count;
      ulong time_;
      bool registered = ri.get_application_info (last_app, out exec_str,
                                                 out count, out time_);
      if (!registered)
      {
        warning ("%s was not registered in RecentInfo item %p", last_app, ri);
        continue;
      }

      string[] exec = exec_str.split_set (" \t\n", 2);

      string? desktop_file;
      if (exec[0] == "soffice" || exec[0] == "ooffice")
      {
        // special case OpenOffice... since it must do everything differently
        desktop_file = Utils.get_ooo_desktop_file_for_mimetype (ri.get_mime_type ());
      }
      else
      {
        desktop_file = Utils.find_desktop_file_for_app (exec[0]);

        // Thunderbird also likes doing funny stuff...
        if (desktop_file == null && exec[0].has_suffix ("-bin"))
        {
          desktop_file = Utils.find_desktop_file_for_app (
            exec[0].substring(0, exec[0].length - 4));
        }
      }

      if (desktop_file == null)
      {
        debug ("Desktop file for \"%s\" was not found, exec: %s, mime_type: %s",
                 uri, exec[0], ri.get_mime_type ());
        continue; // this makes us sad panda
      }

      var actor = "application://%s".printf (Path.get_basename (desktop_file));
      if (actor in ignored_actors)
      {
        continue;
      }

      var parent_file = file_obj.get_parent ();
      string origin = parent_file != null ?
        parent_file.get_uri () : Path.get_dirname (uri);
      var subject =
        new Subject.full (uri,
                          interpretation_for_mimetype (ri.get_mime_type ()),
                          manifestation_for_uri (uri),
                          ri.get_mime_type (),
                          origin,
                          ri.get_display_name (),
                          ""); // FIXME: storage?!

      Event event;
      int64 timestamp;

      // Zeitgeist checks for duplicated events, so we can just inserted
      // all events every time.
      bool log_create = true;
      bool log_modify = true;
      bool log_access = true;

      // However, we don't really want duplicate events with the same
      // timestamp but different interpretations...
      if (ri.get_added () == ri.get_modified ())
      {
        // Creation also changes modified (and visited). If they are the
        // same, we only log the former.
        log_modify = false;
      }
      if (ri.get_modified () == ri.get_visited ())
      {
        // Modification also updated visited. If they are the same, we
        // only log the former.
        log_access = false;
      }

      if (log_create)
      {
        event = new Event.full (ZG.ACCESS_EVENT,
                                ZG.USER_ACTIVITY,
                                actor,
                                null, null);
        event.add_subject (subject);
        timestamp = ri.get_added ();
        timestamp *= 1000;
        event.timestamp = timestamp;
        if (timestamp > last_timestamp && timestamp >= 0)
        {
          events.add ((owned) event);
        }
      }

      if (log_modify)
      {
        event = new Event.full (ZG.MODIFY_EVENT,
                                ZG.USER_ACTIVITY,
                                actor,
                                null , null);
        event.add_subject (subject);
        timestamp = ri.get_modified ();
        timestamp *= 1000;
        event.timestamp = timestamp;
        if (timestamp > last_timestamp && timestamp >= 0)
        {
          events.add ((owned) event);
        }
      }

      if (log_access)
      {
        event = new Event.full (ZG.ACCESS_EVENT,
                                ZG.USER_ACTIVITY,
                                actor,
                                null, null);
        event.add_subject (subject);
        timestamp = ri.get_visited ();
        timestamp *= 1000;
        event.timestamp = timestamp;
        if (timestamp > last_timestamp && timestamp >= 0)
        {
          events.add ((owned) event);
        }
      }

    }

    last_timestamp = signal_time;

    return events;
  }
}
