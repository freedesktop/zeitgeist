.. module:: _zeitgeist.engine.remote

========
DBus API
========

This is the raw DBus API for the Zeitgeist engine. Applications written in
Python are encouraged to use the
:class:`ZeitgeistClient <zeitgeist.client.ZeitgeistClient>` API instead.

.. _event_serialization_format:
.. index:: Event Serialization Format

Event Serialization Format
++++++++++++++++++++++++++

The wire representation of events is central to the DBus API of the
Zeitgeist engine. An event has DBus signature :const:`asaasay`. The
Python client library includes an :class:`Event <zeitgeist.datamodel.Event>`
class that conforms, without manual mashalling, to the DBus wire format
described here.

The first array of strings, :const:`as`, contains the `event metadata` at the
following offsets:

 0. Event id, which is guaranteed to be an unsigned integer. Applications
    must never set this field, it is an error to do so. The field will be
    filled out when you ask for events from the Zeitgeist engine.
 1. Timestamp in milliseconds since the Unix Epoch
 2. Interpretation - the abstract notion of "what happened" defined by a formal
    URI. There is a predefined set of event interpretations in the
    :class:`zeitgeist.datamodel.Interpretation` class
 3. Manifestation - the abstract notion of "how did this happen" defined by a
    formal URI. There is a predefined set of event manifestations in the
    :class:`zeitgeist.datamodel.Manifestation` class
 4. Actor - a URI defining the entity spawning the event. In most cases this
    will be an application. The URI of an application is defined as
    the :const:`app://` URI-scheme with the base filename of the application's
    .desktop file (with the extension). Fx
    Firefox with .desktop file :const:`/usr/share/applications/firefox.desktop`
    will have an actor URI of :const:`app://firefox.desktop`.
     
The second component in the event datastructure is the `list of subjects`,
:const:`aas`, each subject being an :const:`as`. Note that an event can have
more than one subject - fx. when deleting a collection of files with one
click in the file manager. The subject metadata is defined
with the following offsets:

 0. URI - eg. :const:`http://example.com/myfile.pdf` or :const:`file:///tmp/my.txt`
 1. Interpretation - the abstract notion of what the subject is,
    eg. "this is a document" or "this is an image". The interpretation is formally
    represented by a URI. The :class:`zeitgeist.datamodel.Interpretation` class
    contains a collection of predefined subject interpretations. It is
    otherwise recommended to use 
    `Nepomuk Information Elements <http://www.semanticdesktop.org/ontologies/nie/#InformationElement>`_
    to describe subject interpretations.
 2. Manifestation - the abstract notion of how the subject is stored or available,
    eg. "this is file" or "this is a webpage". The manifestation is formally
    represented by a URI. The :class:`zeitgeist.datamodel.Manifestation` class
    contains a collection of predefined subject manifestations. It is
    otherwise recommended to use 
    `Nepomuk Data Objects <http://www.semanticdesktop.org/ontologies/nie/#DataObject>`_
    to describe subject manifestations.
 3. Origin - the URI where the user accessed the subject from
 4. Mimetype - The mimetype of the subject, eg. :const:`text/plain`
 5. Text - A short textual representation of the subject suitable for display
 6. Storage - the id storage device the subject is. For files this would be
    the UUID of the volume, for subjects requiring a network interface use the
    string "net". If the subject has been deleted use the string "deleted".
    The storage id of the subject is used internally in the
    Zeitgeist engine to keep track of subject availability. This way clients
    can request hits only on subjects that are currently available.
 
The third an last component of the event data structure is an array of bytes,
:const:`ay`, called the `payload`. The payload can be used to hold any kind of
free form data and its intent and purpose is entirely up to the entity inserting
the event into the log.

.. index:: org.gnome.zeitgeist.Log

org.gnome.zeitgeist.Log
+++++++++++++++++++++++

.. autoclass:: RemoteInterface
    :members: InsertEvents, GetEvents, FindEventIds, FindRelatedUris, DeleteEvents, DeleteLog, Quit, InstallMonitor, RemoveMonitor

.. _org_gnome_zeitgeist_Monitor:
.. index:: org.gnome.zeitgeist.Monitor

org.gnome.zeitgeist.Monitor
+++++++++++++++++++++++++++

.. autoclass:: zeitgeist.client.Monitor
    :members: NotifyInsert, NotifyDelete
    
.. _org_gnome_zeitgeist_Blacklist:
.. index:: org.gnome.zeitgeist.Blacklist

org.gnome.zeitgeist.Blacklist
+++++++++++++++++++++++++++++

.. autoclass:: _zeitgeist.engine.extensions.blacklist.Blacklist
    :members: SetBlacklist, GetBlacklist

org.gnome.zeitgeist.DataSourceRegistry
++++++++++++++++++++++++++++++++++++++

.. autoclass:: _zeitgeist.engine.extensions.datasource_registry.DataSourceRegistry
    :members: RegisterDataSource, GetDataSources, SetDataSourceEnabled, DataSourceEnabled, DataSourceRegistered
