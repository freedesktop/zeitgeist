How do extensions to the engine work?
=====================================

Extensions are objects which are maintained in external python modules
which can have methods which a directly accessible as engine methods.
There is only one extension right nowcalled RelevancyProvider, which
is not enable by default (for now).

Per default there is no extension enabled

    >>> from _zeitgeist.engine.resonance_engine import ZeitgeistEngine
    >>> engine = ZeitgeistEngine()
    >>> len(engine.extensions)
    0
    
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
    
This example adds to new methods to the engine 'add_value' and 'get_engine'.
On the other hand the method called 'internal_method' is not available as
a method of the engine object. The constructor of an Extension object takes
one parameter, the engine object. Per default this engine object is accessible
as the 'engine' attribute of the extension object, like 'self.engine'.
Now we have to load this extension to the engine

    >>> engine.extensions.load(SampleExtension)
    >>> len(engine.extensions)
    1
    >>> print engine.extensions
    ExtensionsCollection(['add_value', 'get_engine'])
    >>> sorted(engine.extensions.methods)
    ['add_value', 'get_engine']
    
In the last line you can see all method which are added to the engine by
an extension.
This methods are now accessible like

    >>> engine.add_value(5)
    5
    >>> engine.add_value(1)
    6
    >>> engine.get_engine() # doctest:+ELLIPSIS
    <_zeitgeist.engine.resonance_engine.ZeitgeistEngine instance at 0x...>

However, there is also a private method which is not accessible as a member
of the engine

    >>> engine.internal_method()
    Traceback (most recent call last):
      ...
    AttributeError

It is not allowed to register an extension which provides a method which
is already a member of the engine object

    >>> class FailExtension(Extension):
    ...     PUBLIC_METHODS = ["get_highest_timestamp_for_actor",]
    ...
    ...     def get_highest_timestamp_for_actor(self, actor):
    ...         pass
    ...
    >>> engine.extensions.load(FailExtension)
    Traceback (most recent call last):
      ...
    ValueError: cannot register method 'get_highest_timestamp_for_actor', this is already an engine method

It is also possible to unload an extension

    >>> engine.extensions.unload(SampleExtension)
    >>> sorted(engine.extensions.methods)
    []

Now its methods are not accessible anymore

    >>> engine.add_value(5)
    Traceback (most recent call last):
      ...
    AttributeError
