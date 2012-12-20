const Gtk = imports.gi.Gtk;
const Lang = imports.lang;
const Zeitgeist = imports.gi.Zeitgeist;

let zglog = Zeitgeist.Log.get_default();

let ids = [];
for (let i=200; i<222; i++){
    ids.push(i);
}

zglog.get_events(ids, null, Lang.bind(this,
            function(zg, result, data) {
                print ("===")
                let events = zg.get_events_finish(result);
                for (let i=0; i<events.size(); i++) {
                        print (i)
                        print(events[i]);
                 }
            }),
            null);

Gtk.main();
