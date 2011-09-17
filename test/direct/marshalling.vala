using Zeitgeist;

Subject create_subject ()
{
  var s = new Subject ();
  s.uri = "scheme:///uri";
  s.interpretation = "subject_interpretation_uri";
  s.manifestation = "subject_manifestation_uri";
  s.mimetype = "text/plain";
  s.origin = "scheme:///";
  s.text = "Human readable text";
  s.storage = "";
  s.current_uri = "scheme:///uri";

  return s;
}

Event create_event ()
{
  var e = new Event ();
  e.id = 1234;
  e.timestamp = 1234567890L;
  e.interpretation = "interpretation_uri";
  e.manifestation = "manifestation_uri";
  e.actor = "test.desktop";
  e.origin = "source";

  return e;
}

void subject_test ()
{
  for (int i=0; i<1000; i++)
  {
    Variant vsubject = create_subject ().to_variant ();
    var subject = new Subject.from_variant (vsubject);
    warn_if_fail (subject != null);
  }
}

void event_test ()
{
  for (int i=0; i<1000; i++)
  {
    Variant vevent = create_event ().to_variant ();
    var event = new Event.from_variant (vevent);
    warn_if_fail (event != null);
  }
}

void events_test ()
{
  GenericArray<Event> events = new GenericArray<Event> ();
  for (int i=0; i<1000; i++)
  {
    var e = create_event ();
    e.add_subject (create_subject ());
    events.add (e);
  }

  Variant vevents = Events.to_variant (events);

  var demarshalled = Events.from_variant (vevents);
  assert (demarshalled.length == 1000);
}

int main (string[] argv)
{
  Test.init (ref argv);

  Test.add_func ("/marshalling/subjects", subject_test);
  Test.add_func ("/marshalling/event", event_test);
  Test.add_func ("/marshalling/events", events_test);

  return Test.run ();
}
