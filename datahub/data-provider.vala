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

public abstract class DataProvider : Object
{
  public abstract string unique_id { get; construct set; }
  public abstract string name { get; construct set; }
  public abstract string description { get; construct set; }

  public abstract DataHub datahub { get; construct set; }
  public abstract bool enabled { get; set; default = true; }
  public abstract bool register { get; construct set; default = true; }
  public int64 last_timestamp { get; set; }

  public virtual void start ()
  {
  }

  public virtual void stop ()
  {
  }

  public signal void items_available (GenericArray<Event> events);
}

