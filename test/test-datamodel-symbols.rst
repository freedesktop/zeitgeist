====================================
How are symbols handled in zeitgeist
====================================

What are symbols and how are they used
**************************************

The datamodel provides two top-level symbols, 'Manifestation' and
'Interpretation'. These symbols are part of the python representation
of the zeitgeist ontologie and several other ontologies.

    >>> from zeitgeist.datamodel import Manifestation, Interpretation
    >>> print repr(Manifestation)
    <Manifestation 'Manifestation'>
    >>> print repr(Interpretation)
    <Interpretation 'Interpretation'>
    
How do Symbols work?
********************

To answer this question we will build up our own set of Symbols from
scratch.

    >>> from zeitgeist.datamodel import Symbol
    >>> TestSymbol = Symbol(name="Test", uri="http://some/uri#TestSymbol")
    >>> print repr(TestSymbol)
    <Test 'http://some/uri#TestSymbol'>
    
    >>> TestSymbol.get_children()
    frozenset([])
    >>> TestSymbol.get_parent()
    frozenset([])
    
Now it is possible to register another symbol which is a sub-symbol of
`TestSymbol`
    
    >>> Symbol("SubSymbol", parent=set([TestSymbol,]), uri="http://some_other/uri#SubSymbol")
    <Test, SubSymbol 'http://some_other/uri#SubSymbol'>
    >>> TestSymbol.SubSymbol
    <Test, SubSymbol 'http://some_other/uri#SubSymbol'>
    
Another way to create a symbol is to just call an Attribute, this will
magically generate this symbol and cache it

    >>> TestSymbol.SubSymbol.Boo
    <Test, SubSymbol, Boo 'Boo'>
    >>> print TestSymbol.SubSymbol.Boo.uri
    Boo
    
Now let's see how getting children of a symbol works

    >>> sorted(TestSymbol.get_children())
    [<Test, SubSymbol 'http://some_other/uri#SubSymbol'>]
    >>> sorted(TestSymbol.get_all_children())
    [<Test, SubSymbol, Boo 'Boo'>, <Test 'http://some/uri#TestSymbol'>, <Test, SubSymbol 'http://some_other/uri#SubSymbol'>]
    
Getting sub symbols by uri:

    >>> TestSymbol["http://some_other/uri#SubSymbol"]
    <Test, SubSymbol 'http://some_other/uri#SubSymbol'>
    >>> TestSymbol["Boo"]
    <Test, SubSymbol, Boo 'Boo'>
    
Symbol names must be CamelCase

    >>> TestSymbol.somesymbol
    Traceback (most recent call last):
        ...
    AttributeError: Test has no attribute 'somesymbol'

    >>> Symbol("somesymbol", parent=set([TestSymbol,]))
    Traceback (most recent call last):
        ...
    ValueError: Naming convention requires symbol name to be CamelCase, got 'somesymbol'

If you want to create a sub symbol, but you are not sure if the parent symbol
exists at this time you can give either the uri or the name of the parent
symbol as name to avoid NameErrors:

    >>> Symbol("AnotherTest", parent=set(["Interpretation",]))
    <Interpretation, AnotherTest 'AnotherTest'>
    >>> print Interpretation.AnotherTest
    AnotherTest
    >>> Symbol("JustAnotherTest",
    ...     parent=set(["http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#MindMap",]))
    <Document, MindMap, JustAnotherTest, Interpretation 'JustAnotherTest'>
    >>> print Interpretation.MindMap.JustAnotherTest
    JustAnotherTest
    
Symbols are also lazy wrt. attribute lookup, you can get each symbol by
using it as an attribute of the top-level symbol

    >>> Interpretation.Document.MindMap.JustAnotherTest == \
    ...     Interpretation.MindMap.JustAnotherTest == Interpretation.JustAnotherTest
    True
