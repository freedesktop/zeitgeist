/* extension-collection.vala
 *
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
    public class ExtensionCollection : Object
    {
        private GenericArray<Extension> extensions;
        private string[] disabled_extensions = {};

        public unowned Engine engine { get; construct; }

        public ExtensionCollection (Engine engine,
                                    RegisterExtensionFunc[] builtins)
        {
            Object (engine: engine);
            setup(builtins);
        }

        ~ExtensionCollection ()
        {
            extensions.foreach ((ext) => { ext.unload (); });
        }

        private void setup (RegisterExtensionFunc[] builtins)
        {
            Extension? extension;
            extensions = new GenericArray<Extension> ();

            unowned string? disabled =
                Environment.get_variable ("ZEITGEIST_DISABLED_EXTENSIONS");
            if (disabled != null)
            {
                disabled_extensions = disabled.split_set (",:;");
            }

            foreach (var func in builtins)
            {
                ExtensionLoader builtin = new BuiltinExtension (func);
                extension = instantiate_extension (builtin);
                if (extension != null) extensions.add (extension);
            }

            // TODO: load extensions from system & user directories, and make
            // sure the order is correct
            unowned string ext_dir1 = Utils.get_local_extensions_path ();
            if (!FileUtils.test (ext_dir1, FileTest.IS_DIR | FileTest.EXISTS))
                return;
            Dir? user_ext_dir = null;
            try
            {
                user_ext_dir = Dir.open (ext_dir1);
            }
            catch (Error e)
            {
                warning (
                    "Couldn't open local extensions directory: %s", e.message);
            }
            if (user_ext_dir != null)
            {
                unowned string? file_name = user_ext_dir.read_name ();
                while (file_name != null)
                {
                    if (file_name.has_suffix (".so"))
                    {
                        string path = Path.build_filename (ext_dir1, file_name);
                        debug ("Loading extension: \"%s\"", path);
                        var loader = new ModuleLoader (path);
                        extension = instantiate_extension (loader);
                        if (extension != null) extensions.add (extension);
                    }
                    else
                    {
                        debug ("Ignored file \"%s/%s\"", ext_dir1, file_name);
                    }
                    file_name = user_ext_dir.read_name ();
                }
            }
        }

        private Extension? instantiate_extension (ExtensionLoader loader)
        {
            if (loader.use ())
            {
                unowned string type_name = loader.extension_type.name ();
                if (type_name == null) return null;

                if (type_name.has_prefix ("Zeitgeist"))
                {
                    type_name = (string) ((char*) type_name + 9);
                }
                if (type_name.has_suffix ("Extension"))
                {
                    string type_no_suffix = (string) type_name.slice(0, type_name.length - 9);
                    type_name = type_no_suffix;
                }

                bool enabled = !(type_name in disabled_extensions);
                if (!enabled) message ("Skipping %s (disabled)", type_name);

                Extension? e = enabled ? loader.create_instance (engine) : null;
                loader.unuse ();

                return e;
            }
            return null;
        }

        public string[] get_extension_names ()
        {
            string[] result = {};
            for (int i = 0; i < extensions.length; i++)
            {
                unowned string ext_name = extensions[i].get_type ().name ();
                if (ext_name.has_prefix ("Zeitgeist"))
                    result += ext_name.substring (9);
                else
                    result += ext_name;
            }

            return result;
        }

        public void call_pre_insert_events (GenericArray<Event?> events,
            BusName? sender)
        {
            int num_events = events.length;
            for (int i = 0; i < extensions.length; ++i)
            {
                extensions[i].pre_insert_events (events, sender);
            }
            assert (num_events == events.length);
        }

        public void call_post_insert_events (GenericArray<Event?> events,
            BusName? sender)
        {
            int num_events = events.length;
            for (int i = 0; i < extensions.length; ++i)
            {
                extensions[i].post_insert_events (events, sender);
            }
            assert (num_events == events.length);
        }

        public unowned uint32[] call_pre_delete_events (uint32[] event_ids,
            BusName? sender)
        {
            for (int i = 0; i < extensions.length; ++i)
            {
                uint32[]? filtered_ids = extensions[i].pre_delete_events (
                    event_ids, sender);
                if (filtered_ids != null)
                    event_ids = filtered_ids;
            }
            return event_ids;
        }

        public void call_post_delete_events (uint32[] event_ids,
            BusName? sender)
        {
            for (int i = 0; i < extensions.length; ++i)
            {
                extensions[i].post_delete_events (event_ids, sender);
            }
        }
    }

}

// vim:expandtab:ts=4:sw=4
