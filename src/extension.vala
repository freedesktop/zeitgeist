/* extension.vala
 *
 * Copyright © 2011 Manish Sinha <manishsinha@ubuntu.com>
 * Copyright © 2011 Michal Hruby <michal.mhr@gmail.com>
 * Copyright © 2011 Collabora Ltd.
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
    /**
     * Base class for all extensions
     *
     * The constructor of an Extension object takes the Engine object
     * it extends as the only argument.
     *
     * Extensions have a set of hooks with which they can control how
     * events are inserted and retrieved from the log.
     *
     * Additionally, extensions may create their own D-Bus interface
     * over which they can expose their own methods.
     */
    public abstract class Extension : Object
    {
        public unowned Engine engine { get; construct set; }

        /**
         * This method gets called before Zeitgeist stops.
         *
         * Execution of this method isn't guaranteed, and you shouldn't do
         * anything slow in there.
         */
        public virtual void unload ()
        {
        }

        /**
         * Hook applied to all events before they are inserted into the
         * log. The returned event is progressively passed through all
         * extensions before the final result is inserted.
         *
         * To block an event completely simply replace it with NULL.
         * The event may also be modified or completely substituted for
         * another event.
         *
         * @param events: A GenericArray of Event instances
         * @param sender: The D-Bus bus name of the client or NULL
         */
        public virtual void pre_insert_events (GenericArray<Event?> events,
            BusName? sender)
        {
        }

        /**
         * Hook applied to all events after they are inserted into the log.
         *
         * The inserted events will have been updated to include their new
         * ID.
         *
         * @param events: A GenericArray of Event instances
         * @param sender: The D-Bus bus name of the client or NULL
         */
        public virtual void post_insert_events (GenericArray<Event?> events,
            BusName? sender)
        {
        }

        /**
         * Hook applied before events are deleted from the log.
         *
         * @param ids: A list with the IDs of the events whose deletion
         *     is being requested
         * @param sender: The unique DBus name for the client triggering
         *     the delete, or NULL
         * @return: The filtered list of event IDs which should be deleted,
         *     or NULL to specify no change
         */
        public virtual uint32[]? pre_delete_events (uint32[] ids,
            BusName? sender)
        {
            return null;
        }

        /**
         * Hook applied after events have been deleted from the log.
         *
         * @param ids: A list with the IDs of the events that have been deleted
         * @param sender: The unique DBus name for the client triggering the delete
         */
        public virtual void post_delete_events (uint32[] ids, BusName? sender)
        {
        }

        /**
         * Store `data' under the given (extension unique) key, overwriting any
         * previous value.
         */
        protected void store_config (string key, Variant data)
        {
            engine.extension_store.store (get_type ().name (), key, data);
        }

        /**
         * Retrieve data this extension previously stored under the given key,
         * or null if there is no such data.
         *
         * @param key: key under which the data is stored
         * @param format: type string for the resulting Variant
         */
        protected Variant? retrieve_config (string key, string format)
        {
            VariantType type = new VariantType(format);
            return engine.extension_store.retrieve (
                get_type ().name (), key, type);
        }
    }

    [CCode (has_target = false)]
    public delegate Type RegisterExtensionFunc (TypeModule module);

    public abstract class ExtensionLoader: TypeModule
    {
        public Type extension_type { get; protected set; }

        public virtual Extension? create_instance (Engine engine)
        {
            if (this.use ())
            {
                if (extension_type == Type.INVALID) return null;
                Extension? instance = Object.@new (extension_type,
                    "engine", engine) as Extension;
                debug ("Loaded extension: %s", extension_type.name ());
                this.unuse ();
                return instance;
            }

            return null;
        }
    }

    public class ModuleLoader: ExtensionLoader
    {
        public string module_path { get; construct; }

        private Module? module = null;

        public ModuleLoader (string module_path)
        {
            Object (module_path: module_path);
        }

        construct
        {
            set_name (module_path);
        }

        protected override bool load ()
        {
            module = Module.open (module_path, ModuleFlags.BIND_LOCAL);
            if (module == null)
            {
                warning ("%s", Module.error ());
                return false;
            }

            void* func_ptr;
            if (module.symbol ("zeitgeist_extension_register", out func_ptr))
            {
                RegisterExtensionFunc func = (RegisterExtensionFunc) func_ptr;
                extension_type = func (this);

                if (extension_type.is_a (typeof (Extension)) == false)
                {
                    extension_type = Type.INVALID;
                    warning ("Type implemented in \"%s\" does not subclass " +
                        "Zeitgeist.Extension!", module_path);
                    return false;
                }

                // according to docs initialized TypeModule is not supposed
                // to be unreferenced, so we do this
                this.ref ();
            }
            else
            {
                warning ("%s", Module.error ());
                return false;
            }

            return true;
        }

        protected override void unload ()
        {
            module = null;
        }
    }

    public class BuiltinExtension: ExtensionLoader
    {
        private RegisterExtensionFunc reg_func;

        public BuiltinExtension (RegisterExtensionFunc func)
        {
            Object ();
            reg_func = func;
        }

        construct
        {
            set_name ("builtin");
        }

        protected override bool load ()
        {
            if (extension_type == Type.INVALID)
            {
                extension_type = reg_func (this);

                if (extension_type.is_a (typeof (Extension)) == false)
                {
                    warning ("Type \"%s\" implemented by [%p] does not " +
                        "subclass Zeitgeist.Extension!",
                        extension_type.name (), this.reg_func);
                    extension_type = Type.INVALID;
                    return false;
                }

                // according to docs initialized TypeModule is not supposed
                // to be unreferenced, so we do this
                this.ref ();
            }
            else
            {
                // this is still needed
                extension_type = reg_func (this);
            }

            return true;
        }

        protected override void unload ()
        {
        }

    }

}

// vim:expandtab:ts=4:sw=4
