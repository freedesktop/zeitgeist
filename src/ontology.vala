/* ontology.vala
 *
 * Copyright © 2011 Collabora Ltd.
 *             By Seif Lotfy <seif@lotfy.com>
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

    private class Symbol
    {
        private static HashTable<string, Symbol> all_symbols = null;
        private List<string> parents;
        private List<string> children;
        private List<string> all_children;
        private string uri;
        private string display_name;

        private Symbol (string uri, string display_name, string[] parents,
            string[] children)
        {
            this.uri = uri;
            this.display_name = display_name;
            this.parents = new List<string> ();
            for (int i = 0; i < parents.length; i++)
                this.parents.append (parents[i]);
            this.children = new List<string> ();
            for (int i = 0; i < children.length; i++)
                this.children.append (children[i]);
        }

        public static string get_display_name (string symbol_uri)
        {
            var symbol = all_symbols.lookup (symbol_uri);
            return symbol.display_name;
        }

        public static List<string> get_all_parents(string symbol_uri)
        {
            var symbol = all_symbols.lookup (symbol_uri);
            var results = new List<string> ();
            foreach (string uri in symbol.parents)
            {
                results.append (uri);
                // Recursively get the other parents
                foreach (string parent_uri in get_all_parents (uri))
                    if (results.index (parent_uri) > -1)
                        results.append (parent_uri);
            }
            return results;
        }

        public static List<string> get_all_children (string symbol_uri)
        {
            var results = new List<string> ();
            var symbol = all_symbols.lookup (symbol_uri);
            foreach (string uri in symbol.all_children)
                results.append (uri);
            return results;
        }

        public static List<string> get_children (string symbol_uri)
        {
            var results = new List<string> ();
            var symbol = all_symbols.lookup (symbol_uri);
            foreach (string uri in symbol.children)
                results.append(uri);
            return results;
        }

        public static List<string> get_parents (string symbol_uri)
        {
            var results = new List<string>();
            var symbol = all_symbols.lookup (symbol_uri);
            foreach (string uri in symbol.parents)
                results.append (uri);
            return results;
        }

        public static bool is_a (string symbol_uri, string parent_uri)
        {
            foreach (string uri in get_all_parents (symbol_uri))
                if (parent_uri == uri)
                    return true;
            return false;
        }

        public static void register (string uri, string display_name,
            string[] parents, string[] children)
        {
            if (all_symbols == null)
                all_symbols = new HashTable<string, Symbol> (str_hash, str_equal);
            Symbol symbol = new Symbol (uri, display_name, parents, children);
            all_symbols.insert (uri, symbol);
        }

    }

}
