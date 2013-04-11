/*
 * Copyright © 2012 Collabora Ltd.
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

    [DBus (name = "org.gnome.zeitgeist.DataSourceRegistry")]
    protected interface RemoteRegistry: Object
    {
        [DBus (signature = "a(sssa(asaasay)bxb)")]
        public abstract async Variant get_data_sources (
            Cancellable? cancellable=null) throws Error;
        public abstract async bool register_data_source (string unique_id,
            string name, string description,
            [DBus (signature = "a(asaasay)")] Variant event_templates,
            Cancellable? cancellable=null, BusName? sender=null) throws Error;
        public abstract async void set_data_source_enabled (string unique_id,
            bool enabled, Cancellable? cancellable=null) throws Error;
        [DBus (signature = "(sssa(asaasay)bxb)")]
        public abstract async Variant get_data_source_from_id (
            string unique_id, Cancellable? cancellable=null) throws Error;

        public signal void data_source_disconnected (
            [DBus (signature = "(sssa(asaasay)bxb)")] Variant data_source);
        public signal void data_source_enabled (string unique_id,
            bool enabled);
        public signal void data_source_registered (
            [DBus (signature = "(sssa(asaasay)bxb)")] Variant data_source);
    }

    /**
     * Query the Zeitgeist Data-Source Registry extension
     *
     * The Zeitgeist engine maintains a publicly available list of recognized
     * data-sources (components inserting information into Zeitgeist).
     * ZeitgeistDataSourceRegistry is used to register new data sources,
     * get information about them and gives the ability to enable or disable
     * the data sources.
     */

    public class DataSourceRegistry : QueuedProxyWrapper
    {

        private RemoteRegistry proxy;

        public signal void source_disconnected (DataSource data_source);
        public signal void source_enabled (string unique_id, bool enabled);
        public signal void source_registered (DataSource data_source);

        public DataSourceRegistry ()
        {
            Bus.get_proxy.begin<RemoteRegistry> (BusType.SESSION,
                Utils.ENGINE_DBUS_NAME,
                "/org/gnome/zeitgeist/data_source_registry", 0, null,
                (obj, res) =>
                {
                    try
                    {
                        proxy = Bus.get_proxy.end (res);
                        proxy_acquired (proxy);
                    }
                    catch (IOError err)
                    {
                        critical (
                            "Unable to connect to Zeitgeist's " +
                            "DataSourceRegistry: %s", err.message);
                        proxy_unavailable (err);
                    }
                });
        }

        protected override void on_connection_established ()
        {
            proxy.data_source_disconnected.connect ((data_source) => {
                try
                {
                    var source = new DataSource.from_variant (data_source);
                    source_disconnected (source);
                }
                catch (DataModelError err)
                {
                    warning ("Error parsing data-source: %s", err.message);
                }
            });
            proxy.data_source_enabled.connect ((unique_id, enabled) => {
                // FIXME: why don't we return DataSource here too? :(
                source_enabled (unique_id, enabled);
            });
            proxy.data_source_registered.connect ((data_source) => {
                try
                {
                    var source = new DataSource.from_variant (data_source);
                    source_registered (source);
                }
                catch (DataModelError err)
                {
                    warning ("Error parsing data-source: %s", err.message);
                }
            });
        }

        protected override void on_connection_lost ()
        {
        }

        public async GenericArray<DataSource> get_data_sources (
            Cancellable? cancellable=null) throws Error
        {
            yield wait_for_proxy ();
            var result = yield proxy.get_data_sources (cancellable);
            return DataSources.from_variant (result);
        }

        public async DataSource get_data_source_from_id (
            string unique_id, Cancellable? cancellable=null) throws Error
        {
            yield wait_for_proxy ();
            var result = yield proxy.get_data_source_from_id (unique_id,
                cancellable);

            return new DataSource.from_variant (result);
        }

        public async bool register_data_source (
            DataSource data_source, Cancellable? cancellable=null) throws Error
        {
            yield wait_for_proxy ();
            return yield proxy.register_data_source (
                data_source.unique_id, data_source.name,
                data_source.description,
                Events.to_variant(data_source.event_templates),
                cancellable);
        }

        // FIXME: return bool with false if error? (+ rethrow error)
        public async void set_data_source_enabled (
            string unique_id, bool enabled, Cancellable? cancellable=null)
            throws Error
        {
            yield wait_for_proxy ();
            yield proxy.set_data_source_enabled (unique_id, enabled,
                cancellable);
        }

    }

}

// vim:expandtab:ts=4:sw=4
