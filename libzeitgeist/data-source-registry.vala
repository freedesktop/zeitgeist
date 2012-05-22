/* data-source-registry.vala
 *
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

    // FIXME: sucks, why can't we make this internal and DataSourceRegistry be public?
    [DBus (name = "org.gnome.zeitgeist.DataSourceRegistry")]
    public interface RemoteRegistry: Object
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

    public class DataSourceRegistry : Object
    {

        private RemoteRegistry proxy;
        //FIXME: refactor code out from log.vala
        //private SList<QueuedMethod> method_dispatch_queue;

        // FIXME: signals

        public DataSourceRegistry ()
        {
            Bus.get_proxy<RemoteRegistry> (BusType.SESSION,
                Utils.ENGINE_DBUS_NAME,
                "/org/gnome/zeitgeist/data_source_registry", 0, null,
                (obj, res) =>
                {
                    try
                    {
                        proxy = Bus.get_proxy.end (res);
                        // FIXME
                    }
                    catch (IOError err)
                    {
                        critical (
                            "Unable to connect to Zeitgeist's " +
                            "DataSourceRegistry: %s");
                    }
                });
        }

        public async GenericArray<DataSource> get_data_sources (
            Cancellable? cancellable) throws Error
        {
            // yield wait_for_proxy (get_data_sources.callback);
            var result = yield proxy.get_data_sources (cancellable);
            return DataSources.from_variant (result);
        }

        public async DataSource get_data_source_from_id (
            string unique_id, Cancellable? cancellable) throws Error
        {
            // yield wait_for_proxy (get_data_source_from_id.callback);
            var result = yield proxy.get_data_source_from_id (unique_id,
                cancellable);

            return new DataSource.from_variant (result);
        }

        public async bool register_data_source (
            DataSource data_source, Cancellable? cancellable) throws Error
        {
            // yield wait_for_proxy (register_data_source.callback);
            return yield proxy.register_data_source (
                data_source.unique_id, data_source.name,
                data_source.description,
                Events.to_variant(data_source.event_templates),
                cancellable);
        }

        // FIXME: return bool with false if error? (+ rethrow error)
        public async void set_data_source_enabled (
            string unique_id, bool enabled, Cancellable? cancellable)
            throws Error
        {
            // yield wait_for_proxy (set_data_source_enabled.callback);
            yield proxy.set_data_source_enabled (unique_id, enabled,
                cancellable);
        }

    }

}

// vim:expandtab:ts=4:sw=4
