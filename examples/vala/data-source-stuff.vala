using Zeitgeist;

MainLoop loop;

async void do_stuff () throws Error
{
    var registry = new Zeitgeist.DataSourceRegistry ();

    registry.source_registered.connect (on_source_registered);
    registry.source_enabled.connect (on_source_enabled);

    DataSource my_data_source = new DataSource.full (
        "com.example.test/my-ds", "Example Data-Source",
        "An example data-source for testing libzeitgeist2",
        new GenericArray<Event>());

    stdout.printf ("Registering with data-source registry...\n");
    bool enabled = yield registry.register_data_source (my_data_source);
    stdout.printf ("Done. The data-source is %s.\n\n",
        (enabled) ? "enabled" : "disabled");

    stdout.printf ("Disabling the data-source...\n");
    yield registry.set_data_source_enabled (my_data_source.unique_id, false);

    yield print_data_sources (registry);

    stdout.printf ("\nEnabling it again...\n");
    yield registry.set_data_source_enabled (my_data_source.unique_id, true);

    yield print_data_sources (registry);

    loop.quit ();
}

void on_source_registered (DataSource source)
{
    stdout.printf("%s registered!\n", source.name);
}

async void on_source_enabled (string unique_id, bool enabled)
{
    var registry = new Zeitgeist.DataSourceRegistry ();
    DataSource source;
    try
    {
        source = yield registry.get_data_source_from_id (unique_id);
        stdout.printf("%s has been %s!\n", source.name,
            (enabled) ? "enabled" : "disabled");
    }
    catch (Error e)
    {
        critical ("Error retrieving data-source information: %s", e.message);
    }
}

async void print_data_sources (DataSourceRegistry registry) throws Error
{
    GenericArray<DataSource> datasources = null;
    datasources = yield registry.get_data_sources ();

    stdout.printf ("\nThe following data-sources are registered:\n");
    for (int i = 0; i < datasources.length; ++i)
    {
        DataSource datasource = datasources[i];
        stdout.printf (" - %s [%s]\n", datasource.name,
            (datasource.enabled) ? "enabled" : "disabled");
    }
}

int main ()
{
    loop = new MainLoop();

    do_stuff.begin ();

    loop.run ();

    return 0;
}
