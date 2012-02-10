/* indexer.vapi is hand-written - not a big deal for these ~10 lines */

namespace Zeitgeist {
  [Compact]
  [CCode (free_function = "zeitgeist_indexer_free", cheader_filename = "fts.h")]
  public class Indexer {
    public Indexer (DbReader reader) throws EngineError;

    public GLib.GenericArray<Event> search (string search_string,
                                            TimeRange time_range,
                                            GLib.GenericArray<Event> templates,
                                            uint offset,
                                            uint count,
                                            ResultType result_type,
                                            out uint matches) throws GLib.Error;

    public GLib.GenericArray<Event> search_with_relevancies (
                                            string search_string,
                                            TimeRange time_range,
                                            GLib.GenericArray<Event> templates,
                                            StorageState storage_state,
                                            uint offset,
                                            uint count,
                                            ResultType result_type,
                                            out double[] relevancies,
                                            out uint matches) throws GLib.Error;

    public void index_events (GLib.GenericArray<Event> events);

    public void delete_events (uint[] event_ids);

    public bool has_pending_tasks ();

    public void process_task ();
  }
}
