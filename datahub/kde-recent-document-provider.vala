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

public class RecentDocumentsKDE : DataProvider
{
  public RecentDocumentsKDE (DataHub datahub) throws GLib.Error
  {
    GLib.Object (unique_id: "com.zeitgeist-project,datahub,kde-recent",
                 name: "Recently Used Documents (KDE)",
                 description: "Logs events from KRecentDocument",
                 datahub: datahub);
  }

  private const string RECENT_DOCUMENTS_PATH =
    "/.kde/share/apps/RecentDocuments";
  private const string RECENT_FILE_GROUP = "Desktop Entry";

  private const string ATTRIBUTE_SEPARATOR = ",";
  private const string FILE_ATTRIBUTE_QUERY_RECENT =
    GLib.FileAttribute.STANDARD_TYPE + ATTRIBUTE_SEPARATOR +
    GLib.FileAttribute.TIME_MODIFIED + ATTRIBUTE_SEPARATOR +
    GLib.FileAttribute.TIME_MODIFIED_USEC;
  private const string FILE_ATTRIBUTE_QUERY_SUBJECT =
    GLib.FileAttribute.STANDARD_CONTENT_TYPE + ATTRIBUTE_SEPARATOR +
    GLib.FileAttribute.TIME_MODIFIED + ATTRIBUTE_SEPARATOR +
    GLib.FileAttribute.TIME_MODIFIED_USEC + ATTRIBUTE_SEPARATOR +
    GLib.FileAttribute.TIME_CHANGED + ATTRIBUTE_SEPARATOR +
    GLib.FileAttribute.TIME_CHANGED_USEC;

  private const int TIME_EPSILON = 100; // msec

  // if vala didn't have bug in construct-only properties, the properties
  // would be construct-only
  public override string unique_id { get; construct set; }
  public override string name { get; construct set; }
  public override string description { get; construct set; }

  public override DataHub datahub { get; construct set; }
  public override bool enabled { get; set; default = true; }
  public override bool register { get; construct set; default = true; }

  private string recent_document_path;
  private GLib.File recent_documents_directory;
  private GLib.FileMonitor monitor;
  private string[] ignored_actors;

  private GLib.Regex recent_regex;
  private GLib.Regex url_regex;
  private const string RECENT_REGEX_REPLACEMENT = "URL=";

  construct
  {
    //FIXME: is done properly ?
    try
    {
      recent_regex = new Regex ("URL\\[[^]]+\\]=");
      url_regex = new Regex ("\\$HOME");
    }
    catch (RegexError err)
    {
      warning ("Couldn't process regex: %s", err.message);
    }
    recent_document_path = Environment.get_home_dir () + RECENT_DOCUMENTS_PATH;
    recent_documents_directory = File.new_for_path (recent_document_path);
    try
    {
      monitor = recent_documents_directory.monitor_directory (
          GLib.FileMonitorFlags.NONE);
    }
    catch (GLib.IOError err)
    {
      warning ("Couldn't set up monitor: %s", err.message);
    }
  }

  public override void start ()
  {
    ignored_actors = datahub.get_data_source_actors ();
    monitor.changed.connect (this.process_event);

    crawl_all_items.begin ();
  }

  public override void stop ()
  {
    monitor.changed.disconnect (this.process_event);
  }

  private async void process_event (GLib.File file, GLib.File? other_file,
    GLib.FileMonitorEvent event_type)
  {
    if (event_type == GLib.FileMonitorEvent.CREATED ||
        event_type == GLib.FileMonitorEvent.CHANGED ||
        event_type == GLib.FileMonitorEvent.ATTRIBUTE_CHANGED)
    {
      try
      {
        Event? event = yield parse_file (file);
        if (event != null)
        {
          GenericArray<Event> events = new GenericArray<Event> ();
          events.add ((owned) event);
          items_available (events);
        }
      }
      catch (GLib.Error err)
      {
        warning ("Couldn't process %s: %s", file.get_path (), err.message);
      }
    }
  }

  private async Event? parse_file (GLib.File file) throws GLib.Error
  {
    TimeVal timeval;

    if (!file.get_basename ().has_suffix (".desktop"))
      return null;

    var recent_info = yield file.query_info_async (
      FILE_ATTRIBUTE_QUERY_RECENT, GLib.FileQueryInfoFlags.NONE);

    GLib.FileType file_type = (GLib.FileType) recent_info.get_attribute_uint32 (
      GLib.FileAttribute.STANDARD_TYPE);
    if (file_type != GLib.FileType.REGULAR)
      return null;

    timeval = recent_info.get_modification_time ();
    int64 event_time = Timestamp.from_timeval (timeval);

    string? content = Utils.get_file_contents (file);
    if (content == null)
      return null;
    content = recent_regex.replace (content, content.length, 0,
      RECENT_REGEX_REPLACEMENT);

    KeyFile recent_file = new KeyFile ();
    recent_file.load_from_data (content, content.length, KeyFileFlags.NONE);
    string basename = recent_file.get_string (RECENT_FILE_GROUP, "Name");
    string uri = recent_file.get_string (RECENT_FILE_GROUP, "URL");
    string desktop_entry_name = recent_file.get_string (RECENT_FILE_GROUP,
      "X-KDE-LastOpenedWith");

    // URL may contain environment variables. In practice, KConfigGroup
    // only uses $HOME.
    uri = url_regex.replace (uri, uri.length, 0, Environment.get_home_dir ());

    string? actor = get_actor_for_desktop_entry_name (desktop_entry_name);
    if (actor == null)
    {
        warning ("Couldn't find actor for '%s'.", desktop_entry_name);
        return null;
    }
    if (actor in ignored_actors)
      return null;

    GLib.File subject_file = File.new_for_uri (uri);
    var subject_info = subject_file.query_info (
      FILE_ATTRIBUTE_QUERY_SUBJECT, GLib.FileQueryInfoFlags.NONE);

    timeval = subject_info.get_modification_time ();
    int64 modification_time = Timestamp.from_timeval (timeval);

    timeval.tv_sec = (long) subject_info.get_attribute_uint64 (
      GLib.FileAttribute.TIME_CHANGED);
    timeval.tv_usec = subject_info.get_attribute_uint32 (
      GLib.FileAttribute.TIME_CHANGED_USEC);
    int64 creation_time = Timestamp.from_timeval (timeval);

    string mimetype = subject_info.get_attribute_string (
      FileAttribute.STANDARD_CONTENT_TYPE);

    string event_interpretation;
    int64 creation_diff = event_time - creation_time;
    int64 modification_diff = event_time - modification_time;
    if (creation_diff.abs () < TIME_EPSILON)
      event_interpretation = ZG.CREATE_EVENT;
    else if (modification_diff.abs () < TIME_EPSILON)
      event_interpretation = ZG.MODIFY_EVENT;
    else
      event_interpretation = ZG.ACCESS_EVENT;

    string origin = Path.get_dirname (uri);
    var subject =
      new Subject.full (uri,
                        interpretation_for_mimetype (mimetype),
                        manifestation_for_uri (uri),
                        mimetype,
                        origin,
                        basename,
                        ""); // storage will be figured out by Zeitgeist

    Event event = new Event.full (event_interpretation, ZG.USER_ACTIVITY,
                                  actor, null, null);
    event.add_subject (subject);
    event.timestamp = event_time;

    return event;
  }

  private string? get_actor_for_desktop_entry_name (string desktop_entry_name)
  {
      const string desktop_prefixes[] = { "", "kde-", "kde4-" };

      DesktopAppInfo dae = null;
      string desktop_id = null;
      foreach (unowned string prefix in desktop_prefixes)
      {
          desktop_id = "%s%s.desktop".printf (prefix, desktop_entry_name);
          dae = new DesktopAppInfo (desktop_id);
          if (dae != null)
            break;
      }

      if (dae != null)
      {
          return "application://%s".printf (desktop_id);
      }

      return null;
  }

  private async void crawl_all_items () throws GLib.Error
  {
    GenericArray<Event> events = new GenericArray<Event> ();

    GLib.File directory = GLib.File.new_for_path (recent_document_path);
    GLib.FileEnumerator enumerator = directory.enumerate_children (
      FileAttribute.STANDARD_NAME, GLib.FileQueryInfoFlags.NONE);
    GLib.FileInfo fi;
    while ((fi = enumerator.next_file ()) != null)
    {
      var file = directory.get_child (fi.get_name ());
      try
      {
        Event? event = yield parse_file (file);
        if (event != null)
          events.add ((owned) event);
      }
      catch (GLib.Error err)
      {
        // Silently ignore. The files may be gone by now - who cares?
      }
    }
    enumerator.close ();

    // Zeitgeist will take care of ignoring the duplicates
    items_available (events);
  }
}
