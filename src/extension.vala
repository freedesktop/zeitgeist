/* extension.vala
 *
 * Copyright © 2011 Manish Sinha <manishsinha@ubuntu.com>
 * Copyright © 2011 Michal Hruby <michal.mhr@gmail.com>
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
     * FIXME: figure out what to do with this. I don't really see
     *        what the point for it is, since D-Bus accessible stuff is
     *        usually exported on a new interface. --RainCT
     * Every extension has to define a list of accessible methods as
     * 'PUBLIC_METHODS'. The constructor of an Extension object takes the
     * engine object it extends as the only argument.
     * ---
     *
     * In addition each extension has a set of hooks to control how events are
     * inserted and retrieved from the log. These hooks can either block the
     * event completely, modify it, or add additional metadata to it.
     */
    public abstract class Extension : Object
    {
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
         * To block an event completely simply return null.
         * The event may also be modified or completely substituted for
         * another event.
         *
         * The default implementation of this method simply returns the
         * event as is.
         *
         * @param event: A Event instance
         * @param sender: The D-Bus bus name of the client
         * @returns: The filtered event instance to insert into the log
         */
        public virtual GenericArray<Event?> pre_insert_events (
            GenericArray<Event?> events, BusName sender)
        {
            return events;
        }
    
        /**
         * Hook applied to all events after they are inserted into the log.
         * 
         * @param event: A Event instance
         * @param sender: The D-Bus bus name of the client
         * @returns: Nothing
         */
        public virtual void post_insert_events (GenericArray<Event?> events,
            BusName sender)
        {
        }
    
        /**
         * Hook applied after events have been deleted from the log.
         *
         * @param ids: A list of event ids for the events that has been deleted
         * @param sender: The unique DBus name for the client triggering the delete
         * @returns: Nothing
         */
        public virtual void post_delete_events (uint32[] ids, BusName sender)
        {
        }
    
        /**
         * Hook applied before events are deleted from the log.
         *
         * @param ids: A list of event ids for the events requested to be deleted
         * @param sender: The unique DBus name for the client triggering the delete
         * @returns: The filtered list of event ids which should be deleted or
         *           null to specify no change.
         */
        public virtual uint32[]? pre_delete_events (uint32[] ids,
            BusName sender)
        {
            return null;
        }
    }

    [CCode (has_target = false)]
    public delegate Type RegisterExtensionFunc (TypeModule module);

    public abstract class ExtensionLoader: TypeModule
    {
        public Type extension_type { get; protected set; }

        public virtual Extension? create_instance ()
        {
            if (this.use ())
            {
                if (extension_type == Type.INVALID) return null;
                Extension? instance = Object.@new (extension_type) as Extension;
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

        protected override bool load ()
        {
            if (extension_type == Type.INVALID)
            {
                extension_type = reg_func (this);

                if (extension_type.is_a (typeof (Extension)) == false)
                {
                    extension_type = Type.INVALID;
                    warning ("Type implemented by \"%p\" does not subclass " +
                        "Zeitgeist.Extension!", this.reg_func);
                    return false;
                }
                
                // according to docs initialized TypeModule is not supposed
                // to be unreferenced, so we do this
                this.ref ();
            }

            return true;
        }

        protected override void unload ()
        {
        }

    }

}
// vim:expandtab:ts=4:sw=4
