========
DBus API
========

Engine
======

org.gnome.zeitgeist Interface
+++++++++++++++++++++++++++++

.. class:: RemoteInterface

    **Output Methods**
    
    .. method:: GetItems(uris)
    
        Get items by uri
        
        :param uris: list of uris
        :type uris: list of strings
        :returns: list of items
        :rtype: list of tuples presenting an :ref:`item-label`
        
    .. method:: FindEvents(min_timestamp, max_timestamp, limit, sorting_asc, mode, filters)
    
        Search for Items which matches different criterias
        
        :param min_timestamp: search for events beginning after this timestamp
        :type min_timestamp: integer
        :param max_timestamp: search for events beginning before this timestamp;
            ``max_timestamp`` equals ``0`` means indefinite time
        :type max_timestamp: integer
        :param limit: limit the number of returned items;
            ``limit`` equals ``0`` returns all matching items
        :type limit: integer
        :param sorting_asc: sort result in ascending order of timestamp, otherwise descending
        :type sorting_asc: boolean
        :param mode: The first mode returns all events, the second one only returns
            the last event when items are repeated and the ``mostused`` mode
            is like ``item`` but returns the results sorted by the number of
            events.
        :type mode: string, either ``event``, ``item`` or ``mostused``
        :param filters: list of filter, multiple filters are connected by an ``OR`` condition
        :type filters: list of tuples presenting a :ref:`filter-label`
        :returns: list of items
        :rtype: list of tuples presenting an :ref:`item-label`
        
    .. method:: CountEvents(min_timestamp, max_timestamp, mode, filters)
    
        This method is similar to ``FindEvents()``, but returns all results
        in ascending order
        
        :param min_timestamp: search for events beginning after this timestamp
        :type min_timestamp: integer
        :param max_timestamp: search for events beginning before this timestamp;
            ``max_timestamp`` equals ``0`` means indefinite time
        :type max_timestamp: integer
        :param mode: The first mode returns all events, the second one only returns
            the last event when items are repeated and the ``mostused`` mode
            is like ``item`` but returns the results sorted by the number of
            events.
        :type mode: string, either ``event``, ``item`` or ``mostused``
        :param filters: list of filter, multiple filters are connected by an ``OR`` condition
        :type filters: list of tuples presenting a :ref:`filter-label`
        :returns: list of items
        :rtype: list of tuples presenting an :ref:`item-label`
        
    .. method:: GetCountForUri(uri, start, end)
        
        *(This method has not been implemented yet)*
        
    .. method:: GetLastTimestamp(uri)
    
        Gets the timestamp of the most recent item in the database. If
        ``uri`` is not empty, it will give the last timestamp for the
        indicated URI. Returns 0 if there are no items in the database.
        
        :param uri: URI of item
        :type uri: string
        :returns: timestamp of most recent item
        :rtype: Integer
        
    .. method:: GetTags(name_filter, amount, min_timestamp, max_timestamp)
    
        Returns a list containing tuples with the name and the number of
        occurencies of the tags matching ``name_filter``, or all existing
        tags in case it's empty, sorted from most used to least used. ``amount``
        can base used to limit the amount of results.
        
        Use ``min_timestamp`` and ``max_timestamp`` to limit the time frames you
        want to consider.
        
        :param name_filter: 
        :type name_filter: string
        :param amount: max amount of returned elements, ``amount`` equals ``0``
            means the result not beeing limited
        :type amount: integer
        :param min_timestamp:
        :type min_timestamp: Integer
        :param max_timestamp:
        :type max_timestamp: Integer
        :returns: list of tuple containing the name and number of occurencies
        :rtype: list of tuples
        
    .. method:: GetRelatedItems(item_uri)
        
        *(This method has not been implemented yet)*
        
    .. method:: GetLastInsertionDate(application)
    
        Returns the timestamp of the last item which was inserted
        related to the given ``application``. If there is no such record,
        0 is returned.
        
        :param application: application to query for
        :type application: string
        :returns: timestamp of last insertion date
        :rtype: integer
        
    .. method:: GetTypes()
        
        Returns a list of all different types in the database.
        
        :returns: list of types
        :rtype: list of strings
       
    **Input Methods**
        
    .. method:: InsertItems(item_list)
    
        Inserts an item into the database. Returns ``1`` if any item
        has been added successfully or ``0`` otherwise
        
        :param item_list: list of items to be inserted in the database
        :type item_list: list of tuples presenting an :ref:`item-label`
        :returns: ``1`` on success, ``0`` otherwise
        :rtype: Integer
        
    .. method:: UpdateItems(item_list)
        
        Update items in the database
        
        :param item_list: list of items to be inserted in the database
        :type item_list: list of tuples presenting an :ref:`item-label`
        
    .. method:: DeleteItems(uris)
    
        Delete items from the database
        
        :param uris: list of uris representing an item
        :type uris: list of strings
        
    **Signals**
    
    .. method:: EventsChanged()
        
        This Signal is emmitted whenever one or more items have been changed
        
    .. method:: EngineStart()
    
        This signal is emmitted once the engine successfully started and
        is ready to process requests
        
    .. method:: EngineExit()
    
    **Commands**
    
    .. method:: Quit()
        
        Terminate the running RemoteInterface process
        
        
        
        
        
Data Types
==========

.. _item-label:

Item
++++

A tuple representing an item, with the following elements:

 #. **timestamp** (integer) -
 #. **uri** (string) -
 #. **text** (string) -
 #. **source** (string) -
 #. **content** (string) -
 #. **mimetype** (string) -
 #. **tags** (string) -
 #. **comment** (string) -
 #. **bookmark** (boolean) -
 #. **use** (string) -
 #. **icon** (string) -
 #. **app** (string) -
 #. **origin** (string) -

.. _filter-label:

Filter
++++++

A dict which can have the following items:

 * **text_name** (string) - some text
    some multi line test
 * **text_uri** (string) - some text
 * **tags** (list of strings) - filter by tags (``AND`` Condition)
 * **mimetypes** (list of strings) - filter by mimetypes (``AND`` Condition)
 * **source** (string) -
 * **content** (string) -
 * **bookmarked** (boolean) -
 
