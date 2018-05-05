/*
 * Zeitgeist
 *
 * Copyright (C) 2010 Michal Hruby <michal.mhr@gmail.com>
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

[DBus (name = "org.gnome.zeitgeist.datahub")]
public interface DataHubService : Object
{
  public abstract string[] get_data_providers () throws GLib.Error;
}

public class DataHub : Object, DataHubService
{
  private Zeitgeist.Log zg_log;
  private Zeitgeist.DataSourceRegistry registry;
  private MainLoop main_loop;
  private List<DataProvider> providers;
  private List<DataSource> sources_info; // list got from ZG's Registry
  private GenericArray<Event> queued_events;
  private uint idle_id = 0;

  public int return_code { get; private set; default = 0; }

  public DataHub ()
  {
    GLib.Object ();
  }

  construct
  {
    providers = new List<DataProvider> ();
    sources_info = new List<DataSource> ();
    queued_events = new GenericArray<Event> ();
    main_loop = new MainLoop ();

    zg_log = new Zeitgeist.Log ();
    zg_log.notify["connected"].connect (() => 
    {
      if (!zg_log.is_connected)
      {
        debug ("Zeitgeist-daemon disappeared from the bus, exitting...");
        quit ();
      }
    });

    registry = new DataSourceRegistry ();
  }

  private void data_source_registered (DataSource ds)
  {
    unowned List<DataSource> iter = sources_info;
    while (iter != null)
    {
      if (iter.data.unique_id == ds.unique_id)
      {
        break;
      }
      iter = iter.next;
    }

    if (iter != null)
    {
      iter.data = ds;
    }
    else
    {
      sources_info.prepend (ds);
    }
  }

  private async void start_data_providers () throws Error
  {
    try
    {
      registry.source_registered.connect (data_source_registered);
      var sources = yield registry.get_data_sources (null);
      for (uint i=0; i<sources.length; i++)
      {
        sources_info.prepend (sources.get (i) as DataSource);
      }
    }
    catch (GLib.Error err)
    {
      warning ("%s", err.message);
    }
    // TODO: load all datasources once we do them as modules
    /*
    foreach (var datasource in datasources)
    {
      providers.prepend (datasource.run ());
    }
    */
    providers.prepend (new RecentManagerGtk (this));
    providers.prepend (new RecentDocumentsKDE (this));

#if ENABLE_TELEPATHY
    providers.prepend (new TelepathyObserver (this));
#endif

#if ENABLE_DOWNLOADS_MONITOR
    providers.prepend (new DownloadsDirectoryMonitor (this));
#endif

    providers.prepend (new DesktopLaunchListener (this));

    foreach (unowned DataProvider prov in providers)
    {
      bool enabled = true;
      // we need to get the timestamp before we register the data provider
      int64 timestamp = 0;
      foreach (var src in sources_info)
      {
        if (src.unique_id == prov.unique_id)
        {
          timestamp = src.timestamp;
          break;
        }
      }

      if (prov.register)
      {
        var ds = new DataSource.full (prov.unique_id,
                                      prov.name,
                                      prov.description,
                                      new GenericArray<Event> ()); // FIXME: templates!
        try
        {
          enabled = yield registry.register_data_source (ds, null);
        }
        catch (GLib.Error reg_err)
        {
          warning ("%s", reg_err.message);
        }
      }
      prov.items_available.connect (this.items_available);
      if (enabled)
      {
        prov.last_timestamp = timestamp;
        prov.start ();
      }
    }
  }

  private void items_available (DataProvider prov, GenericArray<Event> events)
  {
    if (!prov.enabled) return;

    events.foreach ((e) => { queued_events.add (e); });

    if (queued_events.length > 0 && idle_id == 0)
    {
      idle_id = Idle.add (() => 
      {
        insert_events ();
        idle_id = 0;
        return false;
      });
    }
  }

  private void insert_events ()
  {
    debug ("Inserting %u events", queued_events.length);

    batch_insert_events.begin ();

    queued_events = new GenericArray<Event> ();
  }

  protected async void batch_insert_events ()
  {
    // copy the events to GenericArray (with a ref on them)
    GenericArray<Event> all_events = new GenericArray<Event> ();
    queued_events.foreach ((e) => { all_events.add (e); });

    while (all_events.length > 0)
    {
      uint elements_pushed = uint.min ((uint) all_events.length, 100);
      GenericArray<Event> ptr_arr = new GenericArray<Event> ();
      for (uint i=0; i<elements_pushed; i++) ptr_arr.add (all_events[i]);

      try
      {
        yield zg_log.insert_events(ptr_arr, null);
      }
      catch (GLib.Error err)
      {
        warning ("Error during inserting events: %s", err.message);
      }

      all_events.remove_range (0, elements_pushed);
    }
  }

  const string UNIQUE_NAME = "org.gnome.zeitgeist.datahub";
  const string OBJECT_PATH = "/org/gnome/zeitgeist/datahub";

  protected void run () throws Error
  {
    Bus.own_name (BusType.SESSION, UNIQUE_NAME, BusNameOwnerFlags.NONE,
      (conn) => { conn.register_object (OBJECT_PATH, (DataHubService) this); },
      () => { start_data_providers.begin (); },
      () =>
      {
        warning ("Unable to get name \"org.gnome.zeitgeist.datahub\"" +
                 " on the bus!");
        this.return_code = 1;
        this.quit ();
      }
    );
        
    main_loop.run ();
  }

  protected void quit ()
  {
    // dispose all providers
    providers = new List<DataProvider> ();
    main_loop.quit ();
  }

  public string[] get_data_source_actors (bool only_enabled = true)
  {
    string[] actors = {};
    foreach (unowned DataSource src in sources_info)
    {
      if (only_enabled && !src.enabled) continue;
      var template_arr = src.event_templates;
      if (template_arr != null)
      {
        for (uint i=0; i<template_arr.length; i++)
        {
          Zeitgeist.Event event_template =
              template_arr.get (i) as Zeitgeist.Event;
          string? actor = event_template.actor;

          if (actor != null && actor != "")
          {
            actors += actor;
          }
        }
      }
    }

    return actors;
  }

  public string[] get_data_providers () throws IOError
  {
    string[] arr = {};
    foreach (var provider in providers)
    {
      arr += provider.unique_id;
    }
    return arr;
  }

  public static int main (string[] args)
  {
    Environment.set_prgname ("zeitgeist-datahub");
    var hub = new DataHub ();
    try {
        hub.run ();
    } catch (Error err) {
        stdout.printf("Error running Zeitgeist Datahub %s".printf(err.message));
    }

    return hub.return_code;
  }
}
