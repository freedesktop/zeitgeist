========
DBus API
========

.. module:: _zeitgeist.engine.remote

Engine
======

org.gnome.zeitgeist Interface
+++++++++++++++++++++++++++++

.. autoclass:: RemoteInterface
    :members:
    :undoc-members:

Data Types
==========

.. _event-label:

A dict representing an event, with the following elements:

 #. **timestamp** (integer) - the timestamp of the event
 #. **uri** (string) - an unique URI representing the event
 #. **subject** - the URI of the affected item
 #. **source** (string) - URI representing the cause of the event
 #. **content** (string) - URI representing the event type
 #. **application** (string) - .desktop file of the application related to the event
 #. **tags** (string) - dict containing lists with different tag strings
 #. **bookmark** (boolean) - whether the user marked the event as important

.. _item-label:

Item
++++

A dict representing an item, with the following elements:

 #. **source** (string) - URI representing where the item originates (file/online/etc.)
 #. **content** (string) - URI representing the item type (image/video/etc.)
 #. **mimetype** (string) - mimetype of the item
 #. **origin** (string) - URI pointing to where the item came from (optional)
 #. **text** (string) - name of the item (optional)
 #. **icon** (string) - icon override hint
 #. **tags** (string) - dict containing lists with different tag strings
 #. **bookmark** (boolean) - whether the user marked the item as important

.. _filter-label:

Filter
++++++

A dict which can have the following items:

 * **name** (list of strings) - filter by name (``OR`` Condition)
 * **uri** (list of strings) - filter by uris (``OR`` Condition)
 * **tags** (list of strings) - filter by tags (``AND`` Condition)
 * **mimetypes** (list of strings) - filter by mimetypes (``OR`` Condition)
 * **source** (list of strings) - filter by source (``OR`` Condition)
 * **content** (list of strings) - filter by content (``OR`` Condition)
 * **application** (list of strings) - filter by application (ie., path to its .desktop file) (``OR`` Condition)
 * **bookmarked** (boolean) -
