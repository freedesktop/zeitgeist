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

public class Utils : Object
{
  private static HashTable<string, string> app_to_desktop_file = null;
  private static string[] desktop_file_prefixes = null;

  // FIXME: Do we want to make this async?
  // FIXME: this can throw GLib.Error, but if we use try/catch or throws
  //        it makes segfaults :(
  public static string? get_file_contents (GLib.File file)
  {
    uint8[]? contents_array = null;

    try
    {
      if (!file.load_contents (null, out contents_array, null))
        return null;
    }
    catch (Error err)
    {
      debug ("Couldn't get file contents %s: %s", file.get_path (), err.message);
    }

    return (string?) (owned) contents_array;
  }

  /*
   * Configures DesktopAppInfo and initializes the list of places where we
   *  may find .desktop files.
   */
  private static void init_desktop_id ()
  {
    if (desktop_file_prefixes != null)
      return;

    unowned string session_var;

    session_var = Environment.get_variable ("XDG_CURRENT_DESKTOP");
    if (session_var != null)
    {
        DesktopAppInfo.set_desktop_env (session_var);
    }
    else
    {
      session_var = Environment.get_variable ("DESKTOP_SESSION");
      if (session_var == null)
      {
        // let's assume it's GNOME
        DesktopAppInfo.set_desktop_env ("GNOME");
      }
      else
      {
        string desktop_session = session_var.up ();
        if (desktop_session.has_prefix ("GNOME"))
        {
          DesktopAppInfo.set_desktop_env ("GNOME");
        }
        else if (desktop_session.has_prefix ("KDE"))
        {
          DesktopAppInfo.set_desktop_env ("KDE");
        }
        else if (desktop_session.has_prefix ("XFCE"))
        {
          DesktopAppInfo.set_desktop_env ("XFCE");
        }
        else
        {
          // assume GNOME
          DesktopAppInfo.set_desktop_env ("GNOME");
        }
      }
    }

    foreach (unowned string data_dir in Environment.get_system_data_dirs ())
    {
      desktop_file_prefixes += Path.build_path (Path.DIR_SEPARATOR_S,
                                                data_dir,
                                                "applications",
                                                Path.DIR_SEPARATOR_S, null);
    }
  }

  /*
   * Takes a path to a .desktop file and returns the Desktop ID for it.
   * This isn't simply the basename, but may contain part of the path;
   * eg. kde4-kate.desktop for /usr/share/applications/kde4/kate.desktop.
   * */
  private static string extract_desktop_id (string path)
  {
    if (!path.has_prefix ("/"))
      return path;

    string normalized_path = path.replace ("//", "/");

    foreach (unowned string prefix in desktop_file_prefixes)
    {
      if (normalized_path.has_prefix (prefix))
      {
        string without_prefix = normalized_path.substring (prefix.length);

        if (Path.DIR_SEPARATOR_S in without_prefix)
          return without_prefix.replace (Path.DIR_SEPARATOR_S, "-");

        return without_prefix;
      }
    }

    return Path.get_basename (path);
  }

  /*
   * Takes the basename of a .desktop and returns the Zeitgeist actor for it.
   */
  public static string? get_actor_for_desktop_file (string desktop_file,
                                            out DesktopAppInfo dai = null)
  {
    init_desktop_id ();

    if (Path.is_absolute (desktop_file))
    {
      dai = new DesktopAppInfo.from_filename (desktop_file);
    }
    else
    {
      dai = new DesktopAppInfo (desktop_file);
    }

    if (dai == null)
    {
      return null;
    }

    string desktop_id = dai.get_id () ?? extract_desktop_id (dai.get_filename ());
    return "application://%s".printf (desktop_id);
  }

  /*
   * Initialize the cache mapping application names (from GtkRecentManager)
   * to Desktop IDs.
   * */
  private static void init_application_cache ()
  {
    if (unlikely (app_to_desktop_file == null))
      app_to_desktop_file = new HashTable<string, string> (str_hash, str_equal);
  }

  /*
   * Workaround for OpenOffice.org/LibreOffice.
   * */
  public static string? get_ooo_desktop_file_for_mimetype (string mimetype)
  {
    return find_desktop_file_for_app ("libreoffice", mimetype) ??
      find_desktop_file_for_app ("ooffice", mimetype);
  }

  /*
   * Takes an application name (from GtkRecentManager) and finds
   * a .desktop file that launches the given application.
   *
   * It returns the complete path to the .desktop file.
   */
  public static string? find_desktop_file_for_app (string app_name,
                                                   string? mimetype = null)
  {
    init_application_cache ();

    string hash_name = mimetype != null ?
      "%s::%s".printf (app_name, mimetype) : app_name;
    unowned string? in_cache = app_to_desktop_file.lookup (hash_name);
    if (in_cache != null)
    {
      return in_cache;
    }

    string[] data_dirs = Environment.get_system_data_dirs ();
    data_dirs += Environment.get_user_data_dir ();

    foreach (unowned string dir in data_dirs)
    {
      var p = Path.build_filename (dir, "applications",
                                   "%s.desktop".printf (app_name),
                                   null);
      var f = File.new_for_path (p);
      if (f.query_exists (null))
      {
        app_to_desktop_file.insert (hash_name, p);
        // FIXME: we're not checking mimetype here!
        return p;
      }
    }

    foreach (unowned string dir in data_dirs)
    {
      var p = Path.build_filename (dir, "applications", null);
      var app_dir = File.new_for_path (p);
      if (!app_dir.query_exists (null)) continue;

      try
      {
        var enumerator =
          app_dir.enumerate_children (FileAttribute.STANDARD_NAME, 0, null);
        FileInfo fi = enumerator.next_file (null);
        while (fi != null)
        {
          if (fi.get_name ().has_suffix (".desktop"))
          {
            var desktop_file = Path.build_filename (p, fi.get_name (), null);
            var f = File.new_for_path (desktop_file);

            string? contents = Utils.get_file_contents (f);
            if (contents != null)
            {
              if ("Exec=%s".printf (app_name) in contents)
              {
                if (mimetype == null || mimetype in contents)
                {
                  app_to_desktop_file.insert (hash_name, desktop_file);
                  return desktop_file;
                }
              }
            }
          }
          fi = enumerator.next_file (null);
        }

        enumerator.close (null);
      }
      catch (GLib.Error err)
      {
        warning ("%s", err.message);
      }
    }

    return null;
  }
}
