How do extensions to the engine work?
=====================================

Extensions are Python modules that run inside the Zeitgeist process. They
have full access to the database and any other internals of the daemon.
There is only one extension right now called Blacklist, which
is in fact a part of the core Zeitgeist API, but is implemented as an extension
anyway.

Per default two extensions are loaded, the Blacklist and the DataSourceRegistry
extension

    >>> from _zeitgeist.engine.main import ZeitgeistEngine
    >>> engine = ZeitgeistEngine()
    >>> len(engine.extensions)
    2
    
To create a new extension you have to subclass the Extension class and
provide a list of accessible methods in PUBLIC_METHODS

    >>> from _zeitgeist.engine.extension import Extension
    >>> class SampleExtension(Extension):
    ...     PUBLIC_METHODS = ["add_value", "get_engine"]
    ...
    ...     def __init__(self, engine):
    ...         super(SampleExtension, self).__init__(engine)
    ...         self.counter = 0
    ...
    ...     def add_value(self, value):
    ...         self.counter += value
    ...         return self.counter
    ...
    ...     def get_engine(self):
    ...         return self.engine
    ...
    ...     def internal_method(self):
    ...         return 0
    ...
    
This example adds two new methods to the engine 'add_value' and 'get_engine'.
On the other hand the method called 'internal_method' is not available as
a method of the engine object. The constructor of an Extension object takes
one parameter, the engine object. Per default this engine object is accessible
as the 'engine' attribute of the extension object, like 'self.engine'.
Now we have to load this extension to the engine

    >>> engine.extensions.load(SampleExtension)
    >>> len(engine.extensions)
    3
    >>> print engine.extensions
    ExtensionsCollection(['add_value', 'get_blacklist', 'get_data_sources', 'get_engine', 'register_data_source', 'set_blacklist', 'set_data_source_enabled'])
    >>> sorted(engine.extensions.methods)
    ['add_value', 'get_blacklist', 'get_data_sources', 'get_engine', 'register_data_source', 'set_blacklist', 'set_data_source_enabled']

    
In the last line you can see all methods which are added to the engine by
an extension.
These methods are now accessible like

    >>> engine.extensions.add_value(5)
    5
    >>> engine.extensions.add_value(1)
    6
    >>> engine.extensions.get_engine() # doctest:+ELLIPSIS
    <_zeitgeist.engine.main.ZeitgeistEngine instance at 0x...>

However, there is also a private method which is not accessible as a member
of the engine

    >>> engine.extensions.internal_method()
    Traceback (most recent call last):
      ...
    AttributeError: ExtensionsCollection instance has no attribute 'internal_method'

It is also possible to unload an extension

    >>> engine.extensions.unload(SampleExtension)
    >>> sorted(engine.extensions.methods)
    ['get_blacklist', 'get_data_sources', 'register_data_source', 'set_blacklist', 'set_data_source_enabled']

Now its methods are not accessible anymore

    >>> engine.extensions.add_value(5)
    Traceback (most recent call last):
      ...
    AttributeError: ExtensionsCollection instance has no attribute 'add_value'

If you try to load an extension which is not a subclass if `Extension` a
TypeError is raised

    >>> engine.extensions.load(set) # doctest:+ELLIPSIS
    Traceback (most recent call last):
      ...
    TypeError: Unable to load <type 'set'>, all extensions must be subclasses of <class '...Extension'>

Also, if an extension does not define any public method a ValueErro is raised

    >>> class FailExtension(Extension):
    ...
    ...     def get_boo(self):
    ...         return "boo"
    ...
    >>> engine.extensions.load(FailExtension) # doctest:+ELLIPSIS
    Traceback (most recent call last):
      ...
    ValueError: Unable to load <...FailExtension'>, this extension has not defined any methods

At a last step, let's unload all extensions

    >>> engine.extensions.unload()
    >>> len(engine.extensions)
    0

Clean-up and close the engine object

    >>> engine.close()
