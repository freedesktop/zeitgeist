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
    public class ExtensionCollection : Object
    {
        private GenericArray<Extension> extensions;

        public ExtensionCollection ()
        {
            Object ();
        }

        ~ExtensionCollection ()
        {
            extensions.foreach ((ext) => { ext.unload (); });
        }

        construct
        {
            Extension? extension;
            extensions = new GenericArray<Extension> ();

            // load the builtin extensions first
#if BUILTIN_EXTENSIONS
            RegisterExtensionFunc[] builtins =
            {
                data_source_registry_init,
                blacklist_init
            };

            foreach (var func in builtins)
            {
                ExtensionLoader builtin = new BuiltinExtension (func);
                extension = builtin.create_instance ();
                if (extension != null) extensions.add (extension);
            }
#endif

            // TODO: load extensions from system & user directories, and make
            // sure the order is correct
            unowned string ext_dir1 = Utils.get_local_extensions_path ();
            Dir? user_ext_dir;
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
                        // FIXME: check if enabled
                        extension = loader.create_instance ();
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
    }

#if BUILTIN_EXTENSIONS
    private extern static Type data_source_registry_init (TypeModule mod);
    private extern static Type blacklist_init (TypeModule mod);
#endif

}
// vim:expandtab:ts=4:sw=4
