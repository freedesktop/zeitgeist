# reproducer for (lp: #387316)

from zeitgeist.datamodel import Content as _Content, Source as _Source
from zeitgeist.engine.base import *
from zeitgeist.engine.engine import ZeitgeistEngine

items = (
    {
        "uri" : "test://mytest",
        "content" : _Content.IMAGE.uri,
        "source" : _Source.USER_ACTIVITY.uri,
        "app" : "/usr/share/applications/gnome-about.desktop",
        "timestamp" : 0,
        "text" : "Text",
        "mimetype" : "mime/type",
        "icon" : "stock_left",
        "use" : _Content.CREATE_EVENT.uri,
        "origin" : "http://example.org",
        "tags" : u"boo"
    },
    {
        "uri" : "test://mytest2",
        "content" : _Content.IMAGE.uri,
        "source" : _Source.USER_ACTIVITY.uri,
        "app" : "/usr/share/applications/gnome-about.desktop",
        "timestamp" : 0,
        "text" : "Text",
        "mimetype" : "mime/type",
        "icon" : "stock_left",
        "use" : _Content.CREATE_EVENT.uri,
        "origin" : "http://example.org",
        "tags" : u"eins"
    },
    {
        "uri" : "test://mytest3",
        "content" : _Content.IMAGE.uri,
        "source" : _Source.USER_ACTIVITY.uri,
        "app" : "/usr/share/applications/gnome-about.desktop",
        "timestamp" : 0,
        "text" : "Text",
        "mimetype" : "mime/type",
        "icon" : "stock_left",
        "use" : _Content.CREATE_EVENT.uri,
        "origin" : "http://example.org",
        "tags" : u"eins"
    },
)
store = create_store("sqlite:boo.sql")

set_store(store)

engine = ZeitgeistEngine(store)
#~ print dir(engine)

for item in items:
    print engine.insert_item(item)

store.commit()
store.flush()

r = store.find(Annotation)
print [(i.item.uri.value, i.subject_id) for i in r]

store.close()

