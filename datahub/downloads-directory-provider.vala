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

public class DownloadsDirectoryMonitor : DataProvider
{
  public DownloadsDirectoryMonitor (DataHub datahub) throws GLib.Error
  {
    GLib.Object (unique_id: "com.zeitgeist-project,datahub,downloads-monitor",
                 name: "Downloads Directory Monitor",
                 description: "Logs files in the XDG downloads directory",
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

  private string? downloads_path;
  private GLib.File downloads_directory;
  private GLib.FileMonitor monitor;
  private string[] ignored_actors;

  construct
  {
    downloads_path = GLib.Environment.get_user_special_dir (
      GLib.UserDirectory.DOWNLOAD);
    if (downloads_path != null)
    {
      downloads_directory = File.new_for_path (downloads_path);
      try
      {
        monitor = downloads_directory.monitor_directory (
          GLib.FileMonitorFlags.NONE/*SEND_MOVED*/);
      }
      catch (GLib.Error err)
      {
        warning ("Couldn't set up monitor on Downloads directory: %s", err.message);
      }
    }
  }

  public override void start ()
  {
    if (downloads_path != null)
    {
      ignored_actors = datahub.get_data_source_actors ();
      monitor.changed.connect (this.process_event);
    }
  }

  public override void stop ()
  {
    if (downloads_path != null)
    {
      monitor.changed.disconnect (this.process_event);
    }
  }

  private const string ATTRIBUTES =
    FileAttribute.STANDARD_FAST_CONTENT_TYPE + "," +
    FileAttribute.STANDARD_IS_HIDDEN + "," +
    FileAttribute.STANDARD_IS_BACKUP + ",";

  private async void process_event (GLib.File file, GLib.File? other_file,
    GLib.FileMonitorEvent event_type)
  {
    // FIXME: add MOVED once libzg supports current_uri (not that they are
    // very useful, inotify won't tell us about moves to outside ~/Downloads)
    if (event_type != GLib.FileMonitorEvent.CREATED)
    {
      // We're ignoring DELETE since we can't get the mime-type for it, and who
      // cares anyway if we only have them for ~/Downloads?
      return;
    }

    // Skip temporary files (eg. in-progress Downloads)
    string uri = file.get_uri ();
    if (uri.has_suffix (".part") || uri.has_suffix (".crdownload"))
      return;

    GLib.FileInfo subject_info;
    try
    {
      subject_info = yield file.query_info_async (ATTRIBUTES,
                                                  GLib.FileQueryInfoFlags.NONE);
      if (subject_info.get_is_hidden () || subject_info.get_is_backup ())
        return;
    }
    catch (GLib.Error err)
    {
      warning ("Couldn't process %s: %s", file.get_path (), err.message);
      return;
    }

    string mimetype = subject_info.get_attribute_string (
      FileAttribute.STANDARD_FAST_CONTENT_TYPE);
    string origin = Path.get_dirname (uri);
    string basename = Path.get_basename (file.get_path ());

    var subject = new Subject.full (uri,
                                    interpretation_for_mimetype (mimetype),
                                    manifestation_for_uri (uri),
                                    mimetype,
                                    origin,
                                    basename,
                                    ""); // storage will be figured out by Zeitgeist

    string actor = ""; // unknown
    Event event = new Event.full (ZG.CREATE_EVENT, ZG.WORLD_ACTIVITY,
                                  actor, null, null);
    event.add_subject (subject);

    if (event != null)
    {
      GenericArray<Event> events = new GenericArray<Event> ();
      events.add ((owned) event);
      items_available (events);
    }
  }

}
