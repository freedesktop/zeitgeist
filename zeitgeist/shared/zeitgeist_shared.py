# -.- encoding: utf-8 -.-

sig_plain_data = "(isssssisbss)"
def plainify_data(obj):
	""" Takes a Data object or a dictionary and converts it into a
		tuple suitable for transmission through D-Bus. """
	
	return (
		int(obj.get_timestamp()),
		obj.get_uri(),
		obj.get_name(),
		obj.get_type(),
		obj.get_mimetype(), 
		",".join(obj.get_tags()),
		obj.get_comment(),
		obj.get_count(),
		obj.get_use(),
		obj.get_bookmark(),
		obj.get_icon_string() or "",
		obj.get_app(),
		)

def plainify_dict(item_list):
	return (
		item_list["timestamp"],
		item_list["uri"],
		item_list["name"],
		item_list["type"],
		item_list["mimetype"], 
		item_list["tags"],
		item_list["comment"],
		item_list["count"],
		item_list["use"],
		item_list["bookmark"] if "bookmark" in item_list else False,
		item_list["icon"],
		item_list["app"],
		)

def dictify_data(item_list):
	return {
		"timestamp": item_list[0],
		"uri": item_list[1],
		"name": item_list[2],
		"type": item_list[3],
		"mimetype": item_list[4],
		"tags": item_list[5],
		"comment": item_list[6],
		"use": item_list[7],
		"bookmark": item_list[8],
		"icon": item_list[9],
		"app": item_list[10],
		}
