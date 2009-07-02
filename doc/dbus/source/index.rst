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
        
        :param min_timestamp:
        :type min_timestamp: integer
        :param max_timestamp:
        :type max_timestamp: integer
        :param limit:
        :type limit: integer
        :param sorting_asc:
        :type sorting_asc: boolean
        :param mode:
        :type mode: string, either ``event``, ``item`` or ``mostused``
        :param filters: list of filter, multiple filters are connected by an ``OR`` condition
        :type filters: list of tuples presenting a :ref:`filter-label`
        :returns: list of items
        :rtype: list of tuples presenting an :ref:`item-label`
        
        
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
 * **bookamrked** (boolean) -
 
