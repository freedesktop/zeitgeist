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
 
public class SymbolsCollection
{

}

public class Symbol
{
    private HashTable<string, Symbol> children;
    public HashTable<string, Symbol> allChildren;
    public string   name { get; private set; }
    public string   uri { get; private set; }
    public string   displayName { get; private set; }
    public string   doc { get; private set; }
    
    public Symbol(string uri, string name, string displayName, string doc){
        this.name = name;
        this.uri = uri;
        this.displayName = displayName;
        this.doc = doc;
    }
    
    public GenericArray<Symbol> get_parents()
    {
        return new GenericArray<Symbol>();
    }
    
    public GenericArray<Symbol> get_children()
    {
        return new GenericArray<Symbol>();
    }
    
    public GenericArray<Symbol> get_all_children()
    {
        return new GenericArray<Symbol>();
    }
    
    public bool is_a(Symbol symbol)
    {
        return true;
    }
    
    public string to_string()
    {
        return this.uri;
    }
}
