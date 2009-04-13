# Don't add zeitgeist_{gui/engine} here! This line is clever enough
# to read from _gui when called by the GUI and from _engine when
# called by the D-Bus service.
from zeitgeist_base import Data

sig_plaindata = "a(usssssssusb)"
def plainify(obj):
	''' Takes a Data object and converts it into an object
		suitable for transmission through D-Bus. '''
	return (int(obj.get_timestamp()), obj.get_uri(),
		obj.get_name(), obj.get_type(), obj.get_mimetype(), 
		obj.get_icon_string() or '', ','.join(obj.get_tags()),
		obj.get_comment(), obj.get_count(), obj.get_use(),
		obj.get_bookmark())

def objectify(item_list):
	return Data(
		timestamp	= item_list[0],
		uri			= item_list[1],
		name		= item_list[2],
		type		= item_list[3],
		mimetype	= item_list[4],
		icon		= item_list[5],
		tags		= item_list[6],
		comment		= item_list[7],
		count		= item_list[8],
		use			= item_list[9],
		bookmark	= item_list[10]
		)
