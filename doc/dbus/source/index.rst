========
DBus API
========

.. module:: zeitgeist.engine.remote

Engine
======

org.gnome.zeitgeist Interface
+++++++++++++++++++++++++++++

.. autoclass:: RemoteInterface
    :members: 
    :undoc-members:

        
        
        
        
        
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
 
