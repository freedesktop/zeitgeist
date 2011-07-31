/* datamodel.vala
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
 

public class Symbol
{
    private static HashTable<string, Symbol> all_symbols = null;
    private unowned List<string> parents;
    private unowned List<string> children;
    private unowned List<string> all_children;
    public string   name { get; private set; }
    public string   uri { get; private set; }
    public string   display_name { get; private set; }
    public string   doc { get; private set; }
    
    private Symbol(string uri, string name, string display_name, string doc, 
                List<string> parents, List<string> children, 
                List<string> all_children){
        this.name = name;
        this.uri = uri;
        this.display_name = display_name;
        this.doc = doc;
        this.parents = parents;
        this.children = children;
        this. all_children = all_children;
    }
    
    public List<string> get_parents()
    {
        var results = new List<string>();
        foreach (string uri in parents)
        {
            results.append(uri);
            var parent = all_symbols.lookup(uri);
            // Recursivly get the other parents
            foreach (string s in parent.get_parents())
                if (results.index(s) > -1)
                    results.append(s);
        }
        return results;
    }
    
    public List<string> get_children()
    {
        var results = new List<string>();
        foreach (string uri in children)
            results.append(uri);
        return results;
    }
    
    public List<string> get_all_children()
    {
        var results = new List<string>();
        foreach (string uri in children)
        {
            results.append(uri);
            var child = all_symbols.lookup(uri);
            // Recursivly get the other children
            foreach (string s in child.get_all_children())
                if (results.index(s) > -1)
                    results.append(s);
        }
        return results;
    }
    
    public bool is_a(Symbol symbol)
    {
        foreach (string uri in get_parents())
            if (symbol.uri == uri)
                return true;
        return false;
    }
    
    public string to_string()
    {
        return this.uri;
    }
    
    public void register()
    {
        if (all_symbols == null)
            all_symbols = new HashTable<string, Symbol>(str_hash, str_equal);
        all_symbols.insert(uri, this);
    }
    
    public static Symbol from_uri(string uri)
    {
        return all_symbols.lookup(uri);
    }
}
