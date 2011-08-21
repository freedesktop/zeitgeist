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
        private GenericArray<ExtensionLoader> loaders;
        private GenericArray<Extension> extensions;

        public ExtensionCollection ()
        {
            Object ();
        }

        construct
        {
            loaders = new GenericArray<ExtensionLoader> ();
            extensions = new GenericArray<Extension> ();
            
            // TODO: load extensions from system & user directories
            unowned string ext_dir1 = Utils.get_local_extensions_path ();
            Dir? user_ext_dir = Dir.open (ext_dir1);
            if (user_ext_dir != null)
            {
                unowned string? file_name = user_ext_dir.read_name ();
                while (file_name != null)
                {
                    if (file_name.has_suffix (".so"))
                    {
                        string path = Path.build_filename (ext_dir1, file_name);
                        debug ("Loading extension: \"%s\"", path);
                        loaders.add (new ExtensionLoader (path));
                    }
                    else
                    {
                        debug ("Ignored file \"%s/%s\"", ext_dir1, file_name);
                    }
                    file_name = user_ext_dir.read_name ();
                }
            }

            // try to load the modules
            loaders.foreach ((mod) =>
            {
                if (mod.use ())
                {
                    // FIXME: check if enabled
                    extensions.add (mod.create_instance ());
                    mod.unuse ();
                }
            });
        }
    }

}
// vim:expandtab:ts=4:sw=4
