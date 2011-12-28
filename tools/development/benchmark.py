import dbus

BUS_NAME = "org.gnome.zeitgeist.Engine"
INTERFACE_NAME = "org.gnome.zeitgeist.Benchmark"
OBJECT_PATH = "/org/gnome/zeitgeist/benchmark"
 
bus = dbus.SessionBus()
benchmark_obj = bus.get_object(BUS_NAME, OBJECT_PATH)
benchmark_interface = dbus.Interface(benchmark_obj,
    dbus_interface = INTERFACE_NAME)

def find_events(time_frame, templates, storage_type, num_events, result_type):
    return benchmark_interface.FindEvents(time_frame, templates, storage_type, 
        num_events, result_type)
