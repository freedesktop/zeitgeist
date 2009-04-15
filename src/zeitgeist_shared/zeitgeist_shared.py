sig_plain_data = "(issssssusbs)"
def plainify_data(obj):
	''' Takes a Data object or a dictionary and converts it into a
		tuple suitable for transmission through D-Bus. '''
	
	item = (
		int(obj.get_timestamp()),
		obj.get_uri(),
		obj.get_name(),
		obj.get_type(),
		obj.get_mimetype(), 
		','.join(obj.get_tags()),
		obj.get_comment(),
		obj.get_count(),
		obj.get_use(),
		obj.get_bookmark(),
		obj.get_icon_string() or "",
		)
	return item

def dictify_data(item_list):
	return {
		"timestamp": item_list[0],
		"uri": item_list[1],
		"name": item_list[2],
		"type": item_list[3],
		"mimetype": item_list[4],
		"tags": item_list[5],
		"comment": item_list[6],
		"count": item_list[7],
		"use": item_list[8],
		"bookmark": item_list[9],
		"icon": item_list[10]
		}


sig_plain_dataprovider = "(ssb)"

def plainify_dataprovider(obj):
	''' Takes a DataSource object and converts it into an object
		suitable for transmission through D-Bus. '''
	return (obj.get_name(), obj.get_icon_string(), obj.get_active())
