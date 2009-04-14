# Don't add zeitgeist_{gui/engine} here! This line is clever enough
# to read from _gui when called by the GUI and from _engine when
# called by the D-Bus service.
from zeitgeist_base import Data


sig_plain_data = "a(issssssisbs)"
def plainify_data(obj):
	''' Takes a Data object and converts it into an object
		suitable for transmission through D-Bus. '''
	icon = obj.get_icon_string()
	if icon == None:
		icon = ""
		
	return (int(obj.get_timestamp()), obj.get_uri(),
		obj.get_name(), obj.get_type(), obj.get_mimetype(), 
		','.join(obj.get_tags()), obj.get_comment(), obj.get_count(),
		obj.get_use(), obj.get_bookmark(), icon)

def objectify_data(item_list):
	return Data(
		timestamp	= item_list[0],
		uri			= item_list[1],
		name		= item_list[2],
		type		= item_list[3],
		mimetype	= item_list[4],
		tags		= item_list[5],
		comment		= item_list[6],
		count		= item_list[7],
		use			= item_list[8],
		bookmark	= item_list[9],
		icon = item_list[10]
		)


sig_plain_dataprovider = "a(ssb)"
def plainify_dataprovider(obj):
	''' Takes a DataSource object and converts it into an object
		suitable for transmission through D-Bus. '''
	return (obj.get_name(), obj.get_icon_string(), obj.get_active())
